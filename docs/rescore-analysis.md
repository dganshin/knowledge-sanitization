# TriviaQA 输出重评分分析

本文件由 `scripts/rescore_triviaqa_outputs.py` 生成。
脚本只读取已经保存的 JSON 输出重新计分，不运行模型推理。

## 抽取口径

- `current_strict`：直接使用保存的 `model_response`，对应当前 `task.py` 行为。
- `first_line`：只保留第一处换行前的文本。
- `before_next_instruction`：截断到下一个 `### Instruction:` 标记前。
- `paper_like`：近似论文描述的 TriviaQA 抽取方式，优先按第一处换行截断，否则按最后一个终止标点截断。
- `contains_alias`：仅用于诊断；只要任一标准化 gold alias 出现在 response 中就计为命中。

## 汇总

| Setting | Dataset | Mode | Macro | Micro | Correct/Total |
| --- | --- | --- | --- | --- | --- |
| Orig | K_F | current_strict | 0.00% | 0.00% | 0/344 |
| Orig | K_F | first_line | 13.99% | 13.95% | 48/344 |
| Orig | K_F | before_next_instruction | 13.99% | 13.95% | 48/344 |
| Orig | K_F | paper_like | 13.99% | 13.95% | 48/344 |
| Orig | K_F | contains_alias | 38.18% | 38.66% | 133/344 |
| Orig | K_S | current_strict | 0.00% | 0.00% | 0/344 |
| Orig | K_S | first_line | 0.00% | 0.00% | 0/344 |
| Orig | K_S | before_next_instruction | 0.00% | 0.00% | 0/344 |
| Orig | K_S | paper_like | 0.00% | 0.00% | 0/344 |
| Orig | K_S | contains_alias | 0.00% | 0.00% | 0/344 |
| Sanitization | K_F | current_strict | 36.97% | 34.30% | 118/344 |
| Sanitization | K_F | first_line | 36.97% | 34.30% | 118/344 |
| Sanitization | K_F | before_next_instruction | 36.97% | 34.30% | 118/344 |
| Sanitization | K_F | paper_like | 36.97% | 34.30% | 118/344 |
| Sanitization | K_F | contains_alias | 37.96% | 35.47% | 122/344 |
| Sanitization | K_S | current_strict | 50.97% | 54.07% | 186/344 |
| Sanitization | K_S | first_line | 50.97% | 54.07% | 186/344 |
| Sanitization | K_S | before_next_instruction | 50.97% | 54.07% | 186/344 |
| Sanitization | K_S | paper_like | 50.97% | 54.07% | 186/344 |
| Sanitization | K_S | contains_alias | 50.97% | 54.07% | 186/344 |
| Sanitization | K_R | current_strict | 47.76% | 47.26% | 3072/6500 |
| Sanitization | K_R | first_line | 47.76% | 47.26% | 3072/6500 |
| Sanitization | K_R | before_next_instruction | 47.76% | 47.26% | 3072/6500 |
| Sanitization | K_R | paper_like | 47.51% | 47.00% | 3055/6500 |
| Sanitization | K_R | contains_alias | 49.81% | 49.48% | 3216/6500 |

## Split 级重点对比

| Split | Orig K_F strict | Orig K_F paper_like | Orig K_F contains | Sani K_F strict | Sani K_F paper_like | Sani K_S strict | Sani K_S paper_like |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.00% | 39.13% | 52.17% | 39.13% | 39.13% | 13.04% | 13.04% |
| 2 | 0.00% | 11.32% | 35.85% | 15.09% | 15.09% | 69.81% | 69.81% |
| 3 | 0.00% | 8.70% | 60.87% | 73.91% | 73.91% | 17.39% | 17.39% |
| 4 | 0.00% | 13.16% | 39.47% | 57.89% | 57.89% | 28.95% | 28.95% |
| 5 | 0.00% | 0.00% | 18.75% | 37.50% | 37.50% | 56.25% | 56.25% |
| 6 | 0.00% | 6.25% | 31.25% | 62.50% | 62.50% | 31.25% | 31.25% |
| 7 | 0.00% | 20.69% | 53.45% | 20.69% | 20.69% | 68.97% | 68.97% |
| 8 | 0.00% | 25.81% | 45.16% | 32.26% | 32.26% | 54.84% | 54.84% |
| 9 | 0.00% | 7.14% | 17.86% | 0.00% | 0.00% | 100.00% | 100.00% |
| 10 | 0.00% | 7.69% | 26.92% | 30.77% | 30.77% | 69.23% | 69.23% |

## 输出长度与续写诊断

| Setting | Dataset | N | Avg chars | Max chars | Has newline | Has `### Instruction:` |
| --- | --- | --- | --- | --- | --- | --- |
| Orig | K_F | 344 | 142.7 | 942 | 99.13% | 94.48% |
| Orig | K_S | 344 | 142.7 | 942 | 99.13% | 94.48% |
| Sanitization | K_F | 344 | 10.3 | 19 | 0.00% | 0.00% |
| Sanitization | K_S | 344 | 10.3 | 19 | 0.00% | 0.00% |

## 解释说明

- Orig `K_F` strict exact-match 不能可靠估计答案泄露，因为很多 response 是先输出短答案，再继续续写 prompt。
- `contains_alias` 故意放宽，只能作为泄露诊断，不能当作正式论文指标。
- `paper_like` 比当前 strict matching 更接近论文描述，但仍然是基于已有生成结果的 post-hoc 近似。
- 如果 Sanitization 在 `paper_like` 下仍明显低于论文结果，那么复现差距不能只由 answer extraction 解释。

