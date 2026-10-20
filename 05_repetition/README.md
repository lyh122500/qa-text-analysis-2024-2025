# 需求原文

问答的重复程度

对于每一个问题和回答，计算其与之前的问答（前180天内）相似程度。注意：这里要使用同一个公司（即Scode相同）前180天内的问答记录进行查重。

# 运行与结果

原始代码保存在 `code/RepetitionScore.py`。统一运行入口为 `tools/run.py`，命令见仓库首页。

`results/2024.csv.gz`、`results/2025.csv.gz` 为该项指标结果，UTF-8 BOM 编码。`year`、`source_row` 对应输入年份及 Excel 原始行号；`Scode`、`Qtm`、`Recvtm` 用于定位原始记录。
