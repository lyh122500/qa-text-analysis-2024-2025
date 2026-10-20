# 需求原文

文本情绪的分析

问题的情绪、回答的情绪

对每一对问答，分别计算问题的情绪值和回答的情绪值，先对问答文本进行分词，并使用中文情感词典对其进行情感判断，然后计算文本的整体情绪（正面、负面词汇占总词数的比例），并生成两列新的变量，命名为：Question_Pos, Question_Neg, Answer_Pos, Answer_Neg，情感词典见下：

https://github.com/MengLingchao/Chinese_financial_sentiment_dictionary 

如果有其他度量情绪的方式，可以和我商量一下，看看是否加入。

# 运行与结果

原始代码保存在 `code/sentiment.py`。统一运行入口为 `tools/run.py`，命令见仓库首页。

`results/2024.csv.gz`、`results/2025.csv.gz` 为该项指标结果，UTF-8 BOM 编码。`year`、`source_row` 对应输入年份及 Excel 原始行号；`Scode`、`Qtm`、`Recvtm` 用于定位原始记录。
