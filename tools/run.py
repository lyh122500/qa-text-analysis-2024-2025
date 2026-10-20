"""Run supplied algorithms; original files are retained under each requirement/code."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import ast
import argparse
import bz2
import hashlib
import json
import math
import multiprocessing as mp
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import jieba
import cntext as ct
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
R_COLS = ['Question_R1','Question_R2','Question_R3','Answer_R1','Answer_R2','Answer_R3']
S_COLS = ['Question_Pos','Question_Neg','Answer_Pos','Answer_Neg']
KEYS = ['year','source_row','Scode','Qtm','Recvtm']
MODEL = None
DICTION = None

def original_function(folder, filename, name, namespace, replacements=()):
    source = (ROOT/folder/'code'/filename).read_text()
    for old, new in replacements:
        source = source.replace(old, new)
    tree = ast.parse(source)
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(module, filename, 'exec'), namespace)
    return namespace[name]

sentiment = original_function('02_sentiment','sentiment.py','calculate_sentiment',{'jieba':jieba})
quality = original_function('03_reply_quality','reply_quality.py','cal_softcos',{'jieba':jieba,'np':np,'math':math})

def analyze(pair):
    q,a=pair
    r=[]
    for text in (q,a):
        if isinstance(text,str) and text.strip():
            v=ct.readability(text,lang='chinese')
            r.extend(v[k] for k in ['readability1','readability2','readability3'])
        else:r.extend([0.0]*3)
    return r+list(sentiment(q,DICTION))+list(sentiment(a,DICTION))

def quality_pair(pair):
    return quality(pair[0],pair[1],MODEL)

repetition = original_function(
    '05_repetition', 'RepetitionScore.py', 'calculate_repetition_score',
    {'pd': pd, 'timedelta': timedelta, 'TfidfVectorizer': TfidfVectorizer,
     'cosine_similarity': cosine_similarity},
    replacements=[
        ('df = pd.read_csv(file_path)', 'df = file_path.copy()'),
        ('tfidf_matrix[past_subset.index.isin(valid_indices)]',
         'tfidf_matrix[valid_df.index.isin(past_subset.index)]'),
    ],
)

def repetition_group(item):
    indices, replies, dates = item
    frame = pd.DataFrame({'Reply': replies, 'answerdate': pd.to_datetime(pd.Series(dates), format='mixed')})
    result = repetition(frame)
    return indices, result['RepetitionScore'].to_numpy()

def save(df,path):
    df.to_csv(path,index=False,encoding='utf-8-sig',compression='gzip',lineterminator='\r\n')

def load_input(path,year,cache):
    p=cache/f'input_{year}.pkl'
    if p.exists():return pd.read_pickle(p)
    if not path.exists():
        path=path.parent/f'qa-{year}-input.xlsx'
    df=pd.read_excel(path,skiprows=[1],dtype={'Scode':str})
    df.insert(0,'source_row',np.arange(3,len(df)+3))
    df.insert(0,'year',year)
    df.to_pickle(p)
    print(f'INPUT {year}: {len(df)} rows; {df.Scode.nunique()} companies',flush=True)
    return df

def run(args):
    global DICTION,MODEL
    cache=Path(args.cache).resolve();cache.mkdir(parents=True,exist_ok=True)
    resources=ROOT/'resources'
    diction=pd.read_excel(resources/'diction.xlsx',sheet_name=['positive','negative'])
    DICTION={'pos':set(w.strip() for w in diction['positive'].iloc[:,0].dropna().tolist()),
             'neg':set(w.strip() for w in diction['negative'].iloc[:,0].dropna().tolist())}
    jieba.initialize()
    frames={year:load_input(Path(args.inputs)/f'用户与公司问答-{year}.xlsx',year,cache) for year in [2024,2025]}
    context=mp.get_context('fork')
    if args.stage in ['all','text']:
        for year,df in frames.items():
            checkpoints=[]
            with context.Pool(args.workers) as pool:
                for start in range(0,len(df),10000):
                    p=cache/f'text_{year}_{start}.npy';checkpoints.append(p)
                    if not p.exists():
                        pairs=df.iloc[start:start+10000][['Qsubj','Reply']].itertuples(index=False,name=None)
                        values=list(pool.imap(analyze,pairs,chunksize=64))
                        np.save(p,np.asarray(values))
                    print(f'TEXT {year}: {min(start+10000,len(df))}/{len(df)}',flush=True)
            values=np.concatenate([np.load(p) for p in checkpoints])
            for folder,columns,offset in [('01_readability',R_COLS,0),('02_sentiment',S_COLS,6)]:
                result=df[KEYS].copy()
                result[columns]=values[:,offset:offset+len(columns)]
                save(result,ROOT/folder/'results'/f'{year}.csv.gz')
    if args.stage in ['all','repetition']:
        combined=pd.concat(frames.values(),ignore_index=True)
        dates=combined.Recvtm.copy()
        overrides=resources/'date_overrides.csv'
        if overrides.exists():
            for record in pd.read_csv(overrides,keep_default_na=False).itertuples(index=False):
                mask=(combined.year==record.year)&(combined.source_row==record.source_row)
                assert mask.sum()==1
                dates.loc[mask]=record.answerdate or None
        parsed=pd.to_datetime(dates,format='mixed',errors='coerce')
        invalid=dates.notna()&parsed.isna()
        rep_cache=cache/'repetition_joint';rep_cache.mkdir(exist_ok=True)
        scores=np.full(len(combined),np.nan)
        tasks=[]
        pending=[]
        for company,group in combined.groupby('Scode',sort=False,dropna=False):
            indices=group.index.to_numpy()
            if invalid.loc[indices].any():
                pending.extend(indices[invalid.loc[indices]])
                continue
            checkpoint=rep_cache/f'{company}.npy'
            if checkpoint.exists():
                values=np.load(checkpoint)
                assert len(values)==len(indices)
                scores[indices]=values
            else:
                tasks.append((indices,group.Reply.tolist(),parsed.loc[indices].tolist()))
        with context.Pool(args.workers) as pool:
            for k,(indices,values) in enumerate(pool.imap_unordered(repetition_group,tasks,chunksize=1)):
                scores[indices]=values
                company=combined.at[indices[0],'Scode']
                np.save(rep_cache/f'{company}.npy',values)
                if k%100==0:print(f'REPETITION: {k+1}/{len(tasks)} companies',flush=True)
        if pending:
            problem=combined.loc[pending,KEYS]
            problem.to_csv(cache/'pending_invalid_dates.csv',index=False,encoding='utf-8-sig')
            raise ValueError('Unparseable dates require explicit date_overrides.csv; other companies are checkpointed')
        assert np.isfinite(scores).all()
        for year in frames:
            mask=combined.year==year
            result=combined.loc[mask,KEYS].copy()
            result['RepetitionScore']=scores[mask]
            save(result,ROOT/'05_repetition'/'results'/f'{year}.csv.gz')
        print('REPETITION COMPLETE',flush=True)
    if args.stage in ['all','quality']:
        from gensim.models import KeyedVectors
        print('LOADING WORD VECTORS',flush=True)
        vectors=KeyedVectors.load_word2vec_format(str(Path(args.inputs)/'sgns.financial.char.bz2'),binary=False)
        MODEL=SimpleNamespace(wv=vectors)
        os.chdir(resources)
        for year,df in frames.items():
            checkpoints=[]
            with context.Pool(args.workers) as pool:
                for start in range(0,len(df),10000):
                    p=cache/f'quality_{year}_{start}.npy';checkpoints.append(p)
                    if not p.exists():
                        pairs=df.iloc[start:start+10000][['Qsubj','Reply']].itertuples(index=False,name=None)
                        values=list(pool.imap(quality_pair,pairs,chunksize=32))
                        np.save(p,np.asarray(values))
                    print(f'QUALITY {year}: {min(start+10000,len(df))}/{len(df)}',flush=True)
            result=df[KEYS].copy();result['quality_score']=np.concatenate([np.load(p) for p in checkpoints])
            save(result,ROOT/'03_reply_quality'/'results'/f'{year}.csv.gz')
    if args.stage in ['all','merge']:
        report={}
        for year,df in frames.items():
            for folder,cols in [('01_readability',R_COLS),('02_sentiment',S_COLS),('03_reply_quality',['quality_score']),('05_repetition',['RepetitionScore'])]:
                scores=pd.read_csv(ROOT/folder/'results'/f'{year}.csv.gz',dtype={'Scode':str})
                assert len(scores)==len(df)
                assert scores.source_row.tolist()==df.source_row.tolist()
                assert scores.Scode.tolist()==df.Scode.tolist()
                values=scores[cols].to_numpy()
                assert np.isfinite(values).all(),(year,folder,'nonfinite')
                df[cols]=scores[cols]
                report[f'{year}/{folder}']={'rows':len(scores),'min':scores[cols].min().to_dict(),'max':scores[cols].max().to_dict(),'mean':scores[cols].mean().to_dict()}
            save(df,ROOT/'results'/f'用户与公司问答-{year}_全部指标.csv.gz')
        (ROOT/'results'/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print('MERGE AND VALIDATION COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--inputs',required=True)
    parser.add_argument('--cache',default='work/cache')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--stage',choices=['all','text','quality','repetition','merge'],default='all')
    run(parser.parse_args())
