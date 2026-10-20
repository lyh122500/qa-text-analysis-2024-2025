# 需求原文

文本可读性的分析

问题的可读性、回答的可读性

对每一对问答，分别计算问题的Readability和回答的Readability，并生成多列新的变量，命名为：Question_R1, Question_R2, Question_R3, Answer_R1, Answer_R2, Answer_R3, 可参考：https://textdata.cn/blog/cntext_tutorial/ ，提及的三种计算方法请都做一遍。

# 运行与结果

原始代码保存在 `code/readbility.py`。统一运行入口为 `tools/run.py`，命令见仓库首页。

`results/2024.csv.gz`、`results/2025.csv.gz` 为该项指标结果，UTF-8 BOM 编码。`year`、`source_row` 对应输入年份及 Excel 原始行号；`Scode`、`Qtm`、`Recvtm` 用于定位原始记录。
