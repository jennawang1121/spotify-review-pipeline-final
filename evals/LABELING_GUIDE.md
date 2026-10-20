# Golden 50 人工标注指南

请学生本人填写 `golden_50_human.csv` 的七个空标签栏。保留全部 50 行、ID、原文和其他原始字段；不要排序、删重或改写原文。即使文本重复，也保留每个原始 ID。

本文件只解释 rubric，不提供这 50 条的答案。先依据原文独立判断，再用程序比较预测；不要参考模型结果后把人工答案改成一致，也不要把人工答案放入模型输入或用于调 prompt。

| 栏位 | 填写方式 |
|---|---|
| topic | `access`, `usability`, `playback`, `downloads`, `catalog`, `billing`, `support`, `other` 中一个 |
| intent | `cancellation`, `complaint`, `request`, `praise`, `unclear` 中一个；按此优先顺序判断 |
| sentiment | -1 到 1 的数字：负面为负，正面为正，中性/混合/不清楚接近 0 |
| severity | 1–5 整数；依据实际描述的影响，不依据星数或语气激烈程度 |
| entities | JSON 字符串数组，如 `[]`；填写原文中逐字出现的功能/产品/平台实体，不能添加猜测 |
| evidence_quote | 能支持标签的非空原文片段，逐字复制；短评论可使用全文 |
| needs_review | `true` 或 `false`；歧义、信息不足或判断不可靠时标记 true |

Severity：1 无报告问题/赞美/不清楚/纯请求；2 困扰或笼统批评；3 功能受限但仍能使用；4 核心任务明确受阻；5 明确严重财务、隐私或数据损害。

Topic 边界：账号进入是 access；界面、播放队列和歌单管理、广告打断是 usability；播放失败、崩溃、延迟、资源占用是 playback；离线或下载是 downloads；缺歌、发现推荐、歌词是 catalog；费用、订阅、付费墙、明确 premium-only 控制是 billing；联系客服及回复质量是 support。只是提到付费身份不自动构成 billing。

Cancellation 要有个人明确离开或取消意图；仅口号不足。Stars 仅为 metadata。遇到难判例，仍填最佳标签，并设 needs_review；另记简短理由供人工讨论。

标签完成且独立预测保存后，在项目目录执行：

```sh
python3 -m pipeline evaluate --golden evals/golden_50_human.csv --predictions path/to/records.jsonl --out runs/golden-evaluation.json
```

程序报告字段 agreement、severity/sentiment MAE、sentiment tolerance、needs_review precision/recall、混淆与逐例结果。缺失预测按错误计入 agreement；MAE 单列有效预测分母。引用确为原文不等于语义支持正确，仍需人工检查。50 个例子只适合诊断，不是精确总体准确率估计。


Excel 版包含「标注」「填写说明」「原始数据」三张表；标注页只填写黄色栏。下拉选 topic、intent、severity 和 needs_review；sentiment 输入 -1 到 1；entities 和 evidence_quote 逐字依据原文填写。保存后可使用 pipeline.golden_workbook 离线检查/导出。Excel 的填写进度只计算完整性，不代表标签正确。
