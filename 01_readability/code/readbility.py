import pandas as pd
import cntext as ct  # 确保已安装cntext库

# 加载CSV文件
input_file = 'output_all.csv'
output_file = 'output_with_readability.csv'
df = pd.read_csv(input_file)

# 初始化新列
df['Question_R1'] = 0.0
df['Question_R2'] = 0.0
df['Question_R3'] = 0.0
df['Answer_R1'] = 0.0
df['Answer_R2'] = 0.0
df['Answer_R3'] = 0.0

cnt = 0
# 计算每条记录的可读性指标
for index, row in df.iterrows():
    cnt += 1
    print(cnt)
    # 处理问题（Qsubj）
    if isinstance(row['Qsubj'], str) and row['Qsubj'].strip():  # 检查是否为非空字符串
        q_readability = ct.readability(row['Qsubj'], lang='chinese')
        df.at[index, 'Question_R1'] = q_readability['readability1']
        df.at[index, 'Question_R2'] = q_readability['readability2']
        df.at[index, 'Question_R3'] = q_readability['readability3']
    else:
        # 如果 Qsubj 是空值或非字符串，将可读性指标设置为 0
        df.at[index, 'Question_R1'] = 0.0
        df.at[index, 'Question_R2'] = 0.0
        df.at[index, 'Question_R3'] = 0.0

    # 处理回答（Reply）
    if isinstance(row['Reply'], str) and row['Reply'].strip():  # 检查是否为非空字符串
        a_readability = ct.readability(row['Reply'], lang='chinese')
        df.at[index, 'Answer_R1'] = a_readability['readability1']
        df.at[index, 'Answer_R2'] = a_readability['readability2']
        df.at[index, 'Answer_R3'] = a_readability['readability3']
    else:
        # 如果 Reply 是空值或非字符串，将可读性指标设置为 0
        df.at[index, 'Answer_R1'] = 0.0
        df.at[index, 'Answer_R2'] = 0.0
        df.at[index, 'Answer_R3'] = 0.0

# 保存处理后的数据到新的CSV文件
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"处理后的数据已保存到 {output_file}")