"""Check full result coverage, source preservation, and original-script equivalence."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import tempfile
from types import SimpleNamespace
from datetime import timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def main(args):
    CACHE=Path(args.cache).resolve()
    INPUTS=Path(args.inputs).resolve()
    report={}
    quality_samples=[]
    combined=pd.concat([pd.read_pickle(CACHE/f'input_{y}.pkl') for y in [2024,2025]],ignore_index=True)
    combined_dates=combined.Recvtm.copy()
    overrides=ROOT/'resources'/'date_overrides.csv'
    if overrides.exists():
        for r in pd.read_csv(overrides,keep_default_na=False).itertuples(index=False):
            combined_dates.loc[(combined.year==r.year)&(combined.source_row==r.source_row)]=r.answerdate or None
    manifest=json.loads((ROOT/'resources'/'input_manifest.json').read_text())
    for folder,name in [('01_readability','readbility.py'),('02_sentiment','sentiment.py'),('03_reply_quality','reply_quality.py'),('05_repetition','RepetitionScore.py')]:
        assert hashlib.sha256((ROOT/folder/'code'/name).read_bytes()).hexdigest()==manifest[name]['sha256']
    report['original_scripts_sha256']='all four match supplied files'
    for year in [2024,2025]:
        original=pd.read_pickle(CACHE/f'input_{year}.pkl')
        full=pd.read_csv(ROOT/'results'/f'用户与公司问答-{year}_全部指标.csv.gz',dtype={'Scode':str},low_memory=False)
        assert len(full)==len(original)
        for col in original.columns:
            expected=original[col].fillna('').astype(str)
            actual=full[col].fillna('').astype(str)
            assert expected.tolist()==actual.tolist(),(year,col)
        for folder in ['01_readability','02_sentiment','03_reply_quality','05_repetition']:
            result=pd.read_csv(ROOT/folder/'results'/f'{year}.csv.gz',dtype={'Scode':str},low_memory=False)
            for col in result.columns:
                if pd.api.types.is_numeric_dtype(result[col]):
                    np.testing.assert_allclose(result[col],full[col],rtol=0,atol=0)
                else:assert result[col].fillna('').tolist()==full[col].fillna('').tolist()
        report[str(year)]={'rows':len(full),'all_original_fields_preserved':True,'all_four_outputs_match_full_result':True}
        # Execute original file-level scripts on a real-data sample without editing them.
        sample=original.sample(100,random_state=2024).copy()
        with tempfile.TemporaryDirectory() as d:
            old=os.getcwd();os.chdir(d)
            try:
                sample.to_csv('output_all.csv',index=False)
                shutil.copy2(ROOT/'resources'/'diction.xlsx','diction.xlsx')
                with contextlib.redirect_stdout(io.StringIO()):
                    runpy.run_path(str(ROOT/'01_readability'/'code'/'readbility.py'))
                    runpy.run_path(str(ROOT/'02_sentiment'/'code'/'sentiment.py'))
                check=pd.read_csv('output_with_sentiment.csv')
                cols=['Question_R1','Question_R2','Question_R3','Answer_R1','Answer_R2','Answer_R3','Question_Pos','Question_Neg','Answer_Pos','Answer_Neg']
                np.testing.assert_allclose(check[cols],full.iloc[sample.index][cols],rtol=0,atol=1e-14)
            finally:os.chdir(old)
        report[str(year)]['original_readability_sentiment_script_sample_matches']=100
        quality_samples.append((year, sample[['Qsubj','Reply']].copy(), full.iloc[sample.index].quality_score.to_numpy()))
        script=(ROOT/'05_repetition'/'code'/'RepetitionScore.py').read_text()
        script=script.replace('tfidf_matrix[past_subset.index.isin(valid_indices)]',
                              'tfidf_matrix[valid_df.index.isin(past_subset.index)]')
        ns={'__name__':'reference','pd':pd,'timedelta':timedelta,
            'TfidfVectorizer':TfidfVectorizer,'cosine_similarity':cosine_similarity}
        exec(compile(script,'RepetitionScore.py','exec'),ns)
        companies=original.groupby('Scode').size().nlargest(4).index
        checked=0
        with tempfile.TemporaryDirectory() as d:
            for company in companies:
                group=combined[combined.Scode==company]
                reference=group[['Reply']].copy()
                reference['answerdate']=pd.to_datetime(combined_dates.loc[group.index],format='mixed').dt.strftime('%Y-%m-%d %H:%M:%S')
                path=Path(d)/'company.csv';reference.to_csv(path,index=False)
                expected=ns['calculate_repetition_score'](path).RepetitionScore.to_numpy()
                selected=group.year.to_numpy()==year
                np.testing.assert_allclose(expected[selected],full.loc[full.Scode==company,'RepetitionScore'],rtol=0,atol=0)
                checked+=int(selected.sum())
        report[str(year)]['original_repetition_script_rows_checked']=checked
    from gensim.models import KeyedVectors
    model=SimpleNamespace(wv=KeyedVectors.load_word2vec_format(str(INPUTS/'sgns.financial.char.bz2'),binary=False))
    namespace=runpy.run_path(str(ROOT/'03_reply_quality'/'code'/'reply_quality.py'),run_name='reference')
    old=os.getcwd();os.chdir(ROOT/'resources')
    try:
        for year,sample,scores in quality_samples:
            expected=[namespace['cal_softcos'](q,a,model) for q,a in sample.itertuples(index=False,name=None)]
            np.testing.assert_allclose(expected,scores,rtol=0,atol=1e-12)
            report[str(year)]['original_quality_function_sample_matches']=len(sample)
    finally:os.chdir(old)
    (ROOT/'results'/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--inputs',default='inputs')
    parser.add_argument('--cache',default='work/cache')
    main(parser.parse_args())
