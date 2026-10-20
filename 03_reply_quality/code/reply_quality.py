import gensim
import numpy as np
from gensim.models import KeyedVectors
import jieba
from sklearn.metrics.pairwise import cosine_similarity
import math
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor  # 使用多线程
import bz2


def cal_softcos(Q, A, model):
    if not isinstance(Q, str) or not isinstance(A, str):
        return 0.0
        # 分词
    Q_list = jieba.lcut(Q, cut_all=False)
    A_list = jieba.lcut(A, cut_all=False)

    # 停用词过滤和词向量存在判断
    stopwords = set(open('stopwords.txt', encoding='utf-8').read().splitlines())
    Qwords = []
    for word in Q_list:
        if word not in stopwords and not word.isdigit() and word in model.wv:
            Qwords.append(word)
    Awords = []
    for word in A_list:
        if word not in stopwords and not word.isdigit() and word in model.wv:
            Awords.append(word)

    QAwords = Qwords + Awords
    unique_words = list(set(QAwords))
    n = len(unique_words)

    if n == 0:
        return 0.0  # 防止除以零

    # 构建词频向量
    Q_freq = {word: Qwords.count(word) for word in unique_words}
    A_freq = {word: Awords.count(word) for word in unique_words}

    Q_array = np.array([Q_freq.get(word, 0) for word in unique_words])
    A_array = np.array([A_freq.get(word, 0) for word in unique_words])

    # 构建相似度矩阵
    vectors = np.array([model.wv[word] for word in unique_words])
    M = np.dot(vectors, vectors.T)  # 内积矩阵
    M = np.maximum(M, 0)  # 非负值
    M = np.square(M)  # 平方

    # 计算软余弦相似度
    numerator = np.dot(Q_array, np.dot(M, A_array))
    denominator1 = math.sqrt(np.dot(Q_array, np.dot(M, Q_array)))
    denominator2 = math.sqrt(np.dot(A_array, np.dot(M, A_array)))
    similarity = numerator / (denominator1 * denominator2) if (denominator1 * denominator2) != 0 else 0.0
    return similarity


if __name__ == '__main__':
    with bz2.open('sgns.financial.char.bz2', 'rb') as f:
        model = gensim.models.KeyedVectors.load_word2vec_format(f, binary=False)

    df = pd.read_csv('output_with_sentiment.csv')

    # 将问题和回答转为列表
    Q_list = df['Qsubj'].tolist()
    A_list = df['Reply'].tolist()

    # 使用多线程池并行计算
    results = []
    for Q, A in tqdm(zip(Q_list, A_list), total=len(Q_list)):
        softcos = cal_softcos(Q, A, model)
        results.append(softcos)

    df['quality_score'] = results
    df.to_csv('output_with_quality.csv', index=False)