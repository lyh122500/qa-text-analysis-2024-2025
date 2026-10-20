# 需求原文

回复质量

对于每一对问答，使用Python的Word2Vec库计算两者的软余弦相似度，该值的范围为0到1，越高代表交互质量越高。

可参考网站：

https://blog.csdn.net/weixin_43956523/article/details/142032328 

https://textdata.cn/blog/2023-05-23-soft-cosine-similarity/ 

# 运行与结果

原始代码保存在 `code/reply_quality.py`。统一运行入口为 `tools/run.py`，命令见仓库首页。

`results/2024.csv.gz`、`results/2025.csv.gz` 为该项指标结果，UTF-8 BOM 编码。`year`、`source_row` 对应输入年份及 Excel 原始行号；`Scode`、`Qtm`、`Recvtm` 用于定位原始记录。
