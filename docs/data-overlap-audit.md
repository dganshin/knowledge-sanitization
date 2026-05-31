# 数据重叠与样本结构审计

审计日期：`2026-05-31`

审计范围：

- `data/triviaqa_1` 到 `data/triviaqa_10`
- 训练文件：`train_5-forget-answers_85-percent-retain.jsonl`
- 测试集：`test-forget_gold-answer_K-F`、`test-forget_sanitization-phrase_K-S`、`test-retrain_K-R`

本审计只读取本地数据文件和 HuggingFace Arrow dataset，不运行模型。

## 1. 方法

统计方法：

- 训练集使用 `json.loads` 读取。虽然扩展名为 `.jsonl`，文件内容实际是一个 JSON array，可被 HuggingFace JSON loader 读取。
- 测试集使用 `datasets.load_from_disk()` 读取。
- question overlap 使用规范化字符串比较：`strip`、压缩空白、转小写。
- `K_S` 训练样本用 `output != output_gold` 判断。
- `K_R` 训练样本用 `output == output_gold` 判断。

## 2. 每个 split 的训练和测试规模

| Split | Train total | Train K_S | Train K_R | K_F test | K_S test | K_R test | Train/K_F overlap | Train/K_S overlap |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 533 | 80 | 453 | 23 | 23 | 17921 | 0 | 0 |
| 2 | 533 | 80 | 453 | 53 | 53 | 17891 | 0 | 0 |
| 3 | 533 | 80 | 453 | 23 | 23 | 17921 | 0 | 0 |
| 4 | 533 | 80 | 453 | 38 | 38 | 17906 | 0 | 0 |
| 5 | 533 | 80 | 453 | 32 | 32 | 17912 | 0 | 0 |
| 6 | 533 | 80 | 453 | 32 | 32 | 17912 | 0 | 0 |
| 7 | 533 | 80 | 453 | 58 | 58 | 17886 | 0 | 0 |
| 8 | 533 | 80 | 453 | 31 | 31 | 17913 | 0 | 0 |
| 9 | 533 | 80 | 453 | 28 | 28 | 17916 | 0 | 0 |
| 10 | 533 | 80 | 453 | 26 | 26 | 17918 | 0 | 0 |

结论：

- 每个 split 训练集固定为 `533` 条，其中 `K_S=80`、`K_R=453`。
- 每个 split 的 `K_F` 和 `K_S` 测试集大小相同，因为它们是同一批 forget questions 的不同 gold answer 版本。
- 训练 question 与 `K_F/K_S` 测试 question 没有完全字符串重叠。

## 3. Forgetting targets

| Split | Forgetting targets |
|---:|---|
| 1 | Cheese:16; Birds:16; Paris:16; Julius Caesar:16; Finland:16 |
| 2 | New York:16; Sweden:16; Ireland:16; Sheffield:16; Boxing:16 |
| 3 | Afghanistan:16; Quebec:16; Heart:16; Abraham Lincoln:16; Gin:16 |
| 4 | John:16; Liverpool:16; Chicago:16; Pink:16; Rudyard Kipling:16 |
| 5 | Head:16; Ronald Reagan:16; JAPAN:16; Romania:16; Three:16 |
| 6 | Hydrogen:16; 8:16; Diamond:16; 1967:16; Egypt:16 |
| 7 | June:16; 1984:16; Tokyo:16; China:16; London:16 |
| 8 | England:16; Massachusetts:16; 24:16; Cyprus:16; Cat:16 |
| 9 | Iron:16; True:16; 1:16; Eight:16; One:16 |
| 10 | Cardiff:16; USA:16; Skin:16; Ghana:16; Mozambique:16 |

每个 split 都是 5 个 forgetting target，每个 target 16 条 `K_S` 训练样本，总计 80 条。

## 4. K_F / K_S 重复情况

| Dataset | Raw rows | Unique questions | Duplicate rows | Duplicate rate | Cross-split duplicate questions |
|---|---:|---:|---:|---:|---:|
| K_F | 344 | 182 | 162 | 47.09% | 0 |
| K_S | 344 | 182 | 162 | 47.09% | 0 |

说明：

- `K_F` 与 `K_S` 的重复统计相同，因为它们是同一批问题的两套答案标签。
- 重复主要发生在同一 split 内部，同一个 question 最多出现 2 次。
- 没有发现同一 question 跨不同 split 重复。

示例：

| Dataset | Example question | Rows | Distinct splits |
|---|---|---:|---:|
| K_F/K_S | `"in 1858 rowland macy established a new store named ""r. h. macy & company"", where it stayed on the same site for nearly forty years, in which city?"` | 2 | 1 |
| K_F/K_S | `"in david hockney's painting ""mr and mrs clark and percy"", what is percy?"` | 2 | 1 |
| K_F/K_S | `"in what city were travelers first asked to ""mind the gap""?"` | 2 | 1 |

结论：

- `K_F/K_S` 的有效 unique question 数明显小于 raw rows。
- 论文/实验如果直接按 raw rows 算 accuracy，会把同一 split 内重复 question 计入权重。
- 由于没有跨 split 重复，继续跑 split6-10 仍然能提供新的 forget target 证据。

## 5. K_R 重复情况

| Dataset | Raw rows | Unique questions | Duplicate rows | Duplicate rate | Cross-split duplicate questions |
|---|---:|---:|---:|---:|---:|
| K_R | 179096 | 9961 | 169135 | 94.44% | 9961 |

更多观察：

- `K_R` 的每个 unique question 都跨 10 个 split 重复出现。
- 同一 question 最多出现 20 行，覆盖 10 个 split；这说明部分 question 在单个 split 内也出现 2 次。
- 因为每个 split 的 forgetting targets 不同，`K_R` 实际上是“排除当前 split forget targets 后的大 retain pool”。不同 split 之间 retain pool 高度重叠是预期现象。

示例：

| Example question | Rows | Distinct splits |
|---|---:|---:|
| `"""84 charing cross road"" is a book based on 20 years of correspondence between which new york writer and frank doel, an antiquarian bookseller in london?"` | 20 | 10 |
| `"""a shropshire lad"" is a work of poetry by whom?"` | 20 | 10 |
| `"""a whiter shade of pale"" was the 1967 debut single for which successful british band?"` | 20 | 10 |

结论：

- 从资源角度，完整跑 10 个 split 的 full K_R 会大量重复评测相同 retain questions。
- 对调参阶段而言，`K_R sample` 是合理节省成本的做法。
- 对最终论文复现报告而言，必须明确写明 `K_R` 是 sample 还是 full；如果要和论文表格严格比较，仍需要至少说明 sample 策略和置信风险。

## 6. 对当前实验的影响

1. `K_F/K_S` 测试集很小，10 split raw total 只有 344，unique question 只有 182，因此 split 方差会很大。
2. 当前 split1-5 的 `K_S` 波动从 `0.1304` 到 `0.6981`，与数据小样本、高方差一致。
3. `K_R` raw total 看似巨大，但 unique question 只有 9961，且跨 split 高度重复；full K_R 的成本远高于其新增信息量。
4. 当前 `K_R sample` 可以判断 retain 是否大致崩坏，但不应与论文 full K_R 结果做无条件等价比较。

## 7. 建议

- 继续跑 split6-10 的 `K_F/K_S` full eval，因为它们能补充新的 forget target。
- `K_R` 在调参阶段保留 sample 即可；建议每个 split 使用相同 sample size 以便 macro/micro 都更易解释。
- 如果后续需要严格论文对照，选择一个固定策略：
  - 全部 split 跑 full K_R；或
  - 全部 split 使用同样 sample size 和 sample seed，并明确这是 approximate retain estimate。
- 汇报时优先用 macro average，避免 split1 的 2000 条 `K_R` sample 对 micro average 过度加权。

