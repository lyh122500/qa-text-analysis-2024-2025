import pandas as pd
import cntext as ct
import jieba

# 读取情感词典
diction_df = pd.read_excel('diction.xlsx', sheet_name=['positive', 'negative'])

# 处理情感词典，去掉换行符
positive_words = [word.strip() for word in diction_df['positive'].iloc[:, 0].dropna().tolist()]
negative_words = [word.strip() for word in diction_df['negative'].iloc[:, 0].dropna().tolist()]

# 构建情感词典
diction = {
    'pos': set(positive_words),
    'neg': set(negative_words)
}
# 读取问答数据
df = pd.read_csv('output_with_readability.csv')

# 初始化新列
df['Question_Pos'] = 0.0
df['Question_Neg'] = 0.0
df['Answer_Pos'] = 0.0
df['Answer_Neg'] = 0.0

# 定义情感分析函数
def calculate_sentiment(text, diction):
    """
    计算文本的情感值（正面和负面词汇的比例）
    """
    if not isinstance(text, str) or not text.strip():
        return 0.0, 0.0  # 如果文本为空，返回 0

    # 分词
    words = jieba.lcut(text)
    total_words = len(words)

    if total_words == 0:
        return 0.0, 0.0

    # 统计正面和负面词汇数量
    pos_count = sum(1 for word in words if word in diction['pos'])
    neg_count = sum(1 for word in words if word in diction['neg'])

    # 计算比例
    pos_ratio = pos_count / total_words
    neg_ratio = neg_count / total_words

    return pos_ratio, neg_ratio
cnt = 0
# 对每对问答进行情感分析
for index, row in df.iterrows():
    # 计算问题的情感值
    cnt += 1
    print(cnt)
    q_pos, q_neg = calculate_sentiment(row['Qsubj'], diction)
    df.at[index, 'Question_Pos'] = q_pos
    df.at[index, 'Question_Neg'] = q_neg

    # 计算回答的情感值
    a_pos, a_neg = calculate_sentiment(row['Reply'], diction)
    df.at[index, 'Answer_Pos'] = a_pos
    df.at[index, 'Answer_Neg'] = a_neg

# 保存结果到新的 CSV 文件
df.to_csv('output_with_sentiment.csv', index=False, encoding='utf-8-sig')

print("情感分析完成，结果已保存到 output_with_sentiment.csv")