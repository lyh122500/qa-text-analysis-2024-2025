import os
import pandas as pd
from datetime import timedelta
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp


def calculate_repetition_score(file_path, time_window_days=90, similarity_threshold=0.5):
    df = pd.read_csv(file_path)
    df["answerdate"] = pd.to_datetime(df["answerdate"])

    # 清洗空文本（保留空文本行）
    df["Reply"] = df["Reply"].fillna("").astype(str)
    valid_mask = df["Reply"].str.strip() != ""

    # 仅对有效文本生成TF-IDF向量
    valid_df = df[valid_mask].copy()
    if len(valid_df) == 0:
        df["RepetitionScore"] = 0.0
        return df

    # 生成TF-IDF矩阵（仅有效文本）
    tfidf = TfidfVectorizer(stop_words=None, max_features=5000)
    tfidf_matrix = tfidf.fit_transform(valid_df["Reply"])

    # 将有效文本的索引映射回原始DataFrame
    valid_indices = valid_df.index.tolist()
    df["RepetitionScore"] = 0.0  # 默认值

    # 遍历有效文本计算相似度
    for i, valid_idx in enumerate(valid_indices):
        current_time = df.at[valid_idx, "answerdate"]
        current_vector = tfidf_matrix[i]

        # 时间窗口筛选：仅比较有效文本中之前的行
        past_mask = (
                (valid_df.index < valid_idx) &
                (current_time - valid_df["answerdate"] <= timedelta(days=time_window_days))
        )
        past_subset = valid_df[past_mask]

        if len(past_subset) == 0:
            continue

        # 提取对应的TF-IDF向量
        past_vectors = tfidf_matrix[past_subset.index.isin(valid_indices)]

        # 计算相似度
        similarities = cosine_similarity(current_vector, past_vectors).flatten()
        max_similarity = similarities.max()
        if max_similarity >= similarity_threshold:
            df.at[valid_idx, "RepetitionScore"] = round(max_similarity, 2)

    return df


def process_and_merge_csvs(input_dir, output_file):
    input_dir = os.path.normpath(input_dir)
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]

    merged_df = pd.DataFrame()

    with tqdm(total=len(all_files), desc="处理文件中", unit="file") as pbar:
        for file in all_files:
            file_path = os.path.join(input_dir, file)
            df = calculate_repetition_score(file_path)
            merged_df = pd.concat([merged_df, df], ignore_index=True)
            pbar.set_postfix({"当前文件": file})
            pbar.update(1)

    merged_df.to_csv(output_file, index=False)
    print(f"\n合并完成！结果保存至: {output_file}")


if __name__ == "__main__":
    input_dir = r"F:\research\query_any\split_scode_files"
    output_file = "output_with_repetition.csv"
    process_and_merge_csvs(input_dir, output_file)