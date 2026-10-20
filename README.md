# 投资者与公司问答文本分析（2024、2025）

复用提供的四个 Python 脚本，对两份年度 Excel 计算第 1、2、3、5 项。第 4、6 项不实现。

| 需求 | 文件夹 | 输出指标 |
|---|---|---|
| 1 文本可读性 | `01_readability` | Question_R1/R2/R3、Answer_R1/R2/R3 |
| 2 文本情绪 | `02_sentiment` | Question_Pos/Neg、Answer_Pos/Neg |
| 3 回复质量 | `03_reply_quality` | quality_score |
| 5 问答重复程度 | `05_repetition` | RepetitionScore |

共处理 688,033 条问答：2024 年 473,997 条，2025 年 214,036 条。

各文件夹包含原始代码、对应需求原文、分年度结果。`resources` 包含原需求文档、情绪词典、停用词表、输入文件校验值。大文件通过[仓库 Release](https://github.com/lyh122500/qa-text-analysis-2024-2025/releases/tag/v1.0.0)提供，包括原始 Excel、词向量模型和保留全部原始字段的完整结果。

## 运行

Python 3.9，macOS/Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 从 Release 下载 qa-2024-input.xlsx、qa-2025-input.xlsx
# 以及 sgns.financial.char.bz2，放进 inputs/
python tools/run.py --inputs inputs --cache work/cache --workers 4
```

可使用 `--stage text`、`--stage quality`、`--stage repetition` 分项运行，最后用 `--stage merge` 生成完整结果。计算按批次保存检查点，重复执行可继续运行。

Excel 第 1 行为字段名，第 2 行为中文字段说明，数据从第 3 行开始。保留原始记录顺序、股票代码前导零及空文本行。重复度合并两年记录后按公司拆分计算，再分年度输出，保留跨年历史记录。其他指标逐条计算。回复时间 `Recvtm` 映射为原脚本的 `answerdate`。2024 表第 469913 行的“3小时前”按用户确认视为缺失日期，记录于 `resources/date_overrides.csv`；结果保留原始时间文本。

评分函数复用原始代码；运行入口负责读取 Excel、加载配套资源、分批调度、汇总输出。

每个分项结果以 `year`、`source_row` 定位原始 Excel 行。CSV 使用 gzip 压缩，pandas 可以直接读取：

```python
import pandas as pd
result = pd.read_csv('01_readability/results/2024.csv.gz', dtype={'Scode': str})
```

完整结果在 Release 中，分别为 `qa-2024-results.csv.gz`、`qa-2025-results.csv.gz`，包含全部原始字段与 12 个指标。`results/validation.json` 记录结果行数、指标范围及均值，`results/verification.json` 记录原脚本抽样复算及原字段核验。

完成计算后，可执行 `python tools/verify.py --inputs inputs --cache work/cache` 复核。

## 词典引用

Fuwei Jiang, Joshua Lee, Xiumin Martin, and Guofu Zhou. “Manager Sentiment and Stock Returns.” Journal of Financial Economics 132(1), 2019, 126–149.

姜富伟、孟令超、唐国豪：《媒体文本情绪与股票回报预测》，《经济学（季刊）》。词典使用说明以 `resources/diction.xlsx` 为准。
