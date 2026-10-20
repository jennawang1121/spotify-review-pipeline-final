> Submission preparation in progress. Updated deadline: October20,2026,11:59pm America/Los_Angeles (user update).
> The100k paid run is active under an approved USD7 total API cap. The completed10k development checkpoint passed the unmodified instructor checker with no issues; this is not yet final100k coverage.
> See evidence/checkpoint-10000/official-check-complete-lineage.json and evidence/grading-checkpoint-10000-complete-lineage/. Golden50 reference labels include disclosed AI assistance. Dashboard currently shows500 development reviews and access remains private pending authorization.

# Spotify review pipeline

验收标准以你提供的作业 guidelines 为准。**效率和省钱是你另外提出的设计目标**：在完整满足验收标准的前提下，减少必要模型调用、总费用、等待时间和人工重复操作。作业要求记录成本与实测，但不要求追求最低价格或指定 Jev。当前为**真实 100 条 cold/warm pilot 已完成：cold 107 次调用、76.03 秒、US$0.007073404；warm 零次新调用、零新增 API 费用**。

## 新版作业范围（2026-10-06）

按老师新版和你的确认，最终目标改为 **至少 100,000 条非空评论的有效分类**。保留已经完成的全源 660,622 条导入与 hash；固定分析集包含 100,000 条非空评论及 13 条空文本，共 100,013 个原始 ID。另有 560,609 条非空源记录在本次分析范围之外，不能标成已分类。选择方法、旧文字冲突和估算见 [范围说明](docs/revised-scope.md)。

**部署 dashboard、backend、database 是新版必交项**。Dashboard 必须从 backend/database 读取保存的真实结果，显示总体指标、排名和有证据的 AI 推荐；浏览和筛选不触发模型调用。已完成并部署 500 条真实结果版本：[Spotify Review Evidence](https://spotify-review-evidence.jenna851121.chatgpt.site)。当前私人阅览，需要使用拥有者的 ChatGPT 帐号；公开给老师的阅览权限待确认。线上的 Worker backend 从 D1 database 读取数据，八个问题排名已与离线结果核对一致，详见 [线上检查](evidence/dashboard-live-checks.json)。

## 已完成

- 校验老师 ZIP 中五个 CSV 的 checksum；完整导入 660,622 条，保留所有原始 ID 和字段。
- 确认 660,609 条非空、13 条空文本隔离、484,189 个不同的非空文本。完全重复文本可减少 176,420 次首次分类，约 26.71%；这不是实测 token 或费用降幅。
- 四个模型角色：Jev 分类、OpenAI 独立核查、OpenAI 问题命名、OpenAI memo。SQL/Python 负责保存、去重、分组成员和排名计算。
- 实现真实调用入口、逐次请求/响应和 usage 保存、有限重试、持久预算预留、恢复与下游缓存。
- 实现官方行哈希和导出格式、离线成本重算、golden 50 评估。工程测试包含模拟完整 pilot 和老师 checker 的格式检查。

包含早期调试、真实系统测试和 500 checkpoint 在内的已知 API 小计为 US$0.040729119；六次充值前失败请求的 usage 仍待核对，完整项目费用未知。尚无人工准确率和全量业务推荐，详见 [实测报告](cost/report.md)。状态见 [RUBRIC.md](RUBRIC.md)，架构见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 运行方式

Python 3.9+，仅标准库。命令均在本目录执行。数据取得方式见 [data/README.md](data/README.md)；包含课程数据的测试需先解压原始 ZIP。

```sh
python3 -m pipeline doctor
python3 -m pipeline pilot
python3 -m unittest discover -s tests -v
```

`pilot` 默认只检查输入并展示计划，不联网、不需要 key、不创建实验目录。
离线准备结果位于 `runs/pilot-prepared/`；它与真实 cold 实验目录分开。

真实执行需要在本机 `.env` 填入 `TYPESAFE_API_KEY` 和 `OPENAI_API_KEY`，或设置同名环境变量。不要把 key 放进聊天或提交到 Git。仅提交空白 `.env.example`。

以下命令**允许付费 API**；预算必须遵循 [总预算分配](evidence/pilot-budget-allocation.json)，不因新实验目录而自动增加。
预算对同一个实验目录累计计算；未知费用保留预算预留，不能当作免费。

```sh
python3 -m pipeline pilot --run-dir runs/pilot-benchmark --phase warm --execute-paid --budget-usd 0.35
python3 -m pipeline checkpoint --input data/course/checkpoint_500.csv --run-dir runs/checkpoint-500 --phase resume --execute-paid --budget-usd 0.50
```

实验分配：`runs/pilot-live` 是调试与恢复记录，后续累计上限 US$0.10；`runs/pilot-benchmark` 是正式 cold/warm，后续上限 US$0.35；`runs/system-checks` 上限 US$0.05；`runs/checkpoint-500` 上限 US$0.50。四项合计仍为 US$1.00。不要对已有目录重新 initial，也不要重复付费跑已完成实验。离线重算的准确命令见 cost/report.md。

Cold 使用新的空结果缓存和一个 worker，执行完整 100 条及 5 条独立核查、问题命名和 memo。Warm 使用同一目录和设置；核查是否确实新增零次 enrichment 调用，并报告全部新增调用。日志和成本文件位于实验目录的 `cost/`；每次执行有独立子目录和 measurement。

若首次执行失败，用 `--phase resume` 继续。存在未知 in-flight 请求时会停止，需先核对 provider 记录。不要用新的目录绕过未知支出。
恢复演示可在**另一个已预算的实验**首次执行时加 `--stop-after 10`，随后 resume，保留 before/after checkpoint 并录像。暂停的实验不能冒充未中断 cold wall-time；主 cold/warm 成本实验应独立完整运行。

## 评估和推进顺序

1. 学生自行完成 [golden 50](evals/golden_50_human.csv)，填写说明见 [标注指南](evals/LABELING_GUIDE.md)。人工答案只进入离线评估。
2. 跑真实 100 cold/warm：核对失败、usage、费用、字段质量、独立 verifier 分歧与 memo 引用。
3. 基于实测做 base / conservative / no-reuse 成本和时间报告；在预算内测量 500 → 10,000 → 最终 100,000 条非空分析范围。
4. 补真实 planted-error、prompt injection、预算停止及中断恢复证据；最终重算排名，导出并检查全部记录。
5. 实现并部署 dashboard + backend + database，核对线上数据、排名与推荐引用；公开 GitHub repo/release、检查链接可访问性，再由学生提交。Dashboard 已部署私人版本；公开 GitHub repo 和老师阅览权限尚待完成。

`pilot` 保持老师固定 `cost_100.csv` 的空缓存测试；新的 `checkpoint --input CSV --run-dir DIR` 支持其他输入并允许复用已有结果，默认同样零 API 调用。全量已导入并不等于已分类。100k 的已知基础 API 估算约 US$4.70（500 checkpoint 更新值），超过当前 US$1 实验总预算；规模执行与部署费用尚未授权。

## 离线工具

```sh
python3 -m pipeline evaluate --golden evals/golden_50_human.csv --predictions path/to/records.jsonl --out runs/golden-evaluation.json
python3 -m pipeline cost --calls path/to/calls.jsonl --measurement path/to/measurement.json --out-dir runs/cost-replay
python3 -m pipeline group --db path/to/source.sqlite --out runs/membership.csv
python3 -m pipeline rank --db path/to/source.sqlite --membership runs/membership.csv --out-dir runs/ranking-replay
```

人工标签未填完整时，evaluate 明确失败。排名只计 complaint/cancellation，每个原始 ID 仍独立计数，priority_score = severity_sum；按 score 降序、issue_id 升序排序，mean_severity 六位小数 HALF_UP。

[工程测试输出](evidence/engineering-checks.txt)是软件验证，不是实测模型质量。测试已通过 37 项，其中包含两位小数概率舍入、额度停止和 memo 引用数字的回归检查。真实数据 profile 见 [ingestion.json](evidence/ingestion.json)；源文件完整性见 [dataset-integrity.json](evidence/dataset-integrity.json)。最终需把选定真实运行证据发布到可访问的 repo/release，不能漏交被忽略的本地 `runs/`。

官方参考：[Jev](https://docs.typesafe.ai/models)、[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)。费率与来源日期保存在 [rates.csv](cost/rates.csv)；这两个模型均已完成真实 pilot 调用。


人工标注可以使用已生成的 Excel（outputs/ 中的 golden-50-human-labels.xlsx）。保持七个标签栏由学生独立填写。离线检查或导入命令：

```sh
python3 -m pipeline.golden_workbook outputs/01a10e0d-96d4-7680-90ab-56067eadcf1d/golden-50-human-labels.xlsx
python3 -m pipeline.golden_workbook outputs/01a10e0d-96d4-7680-90ab-56067eadcf1d/golden-50-human-labels.xlsx --out evals/golden_50_human.csv
```

未填齐或原文/ID被改动时不会导出。真实 injection/planted-error 测试见 [测试证据](evals/system-checks/README.md)。[500 条真实 checkpoint 已完成](evidence/checkpoint-500/README.md)：复用 112 条，新增 379 个不同文本分类，全部 500 条完成；新增 US$0.024163929、605.62 秒。Warm 零新增调用和费用，离线排名一致。25 条独立核查的 topic / intent / severity 一致数为 23 / 25 / 21；这些不是人工准确率。

## Dashboard / backend / database

[线上网址](https://spotify-review-evidence.jenna851121.chatgpt.site)当前展示完成的 500 条开发 checkpoint；最终 100k 数据仍待执行和更新。

[部署源代码与设置](dashboard/README.md)包含 Worker backend、D1 schema/migrations 和前端。保存的评论、原始 hash、分类 provenance、汇总、claims、核查结果及 AI memo 存在 database；API 提供 coverage、SQL 排名、筛选和原始评论查询。页面浏览不调用模型。查看 issue 或核查分歧可以追到原始 review ID 与 quote。

[本地验证](evidence/dashboard-local-checks.json)使用真实 SQLite；[线上验证](evidence/dashboard-live-checks.json)使用真实 D1。两者均核对完成数量、所有八个排名与源证据。人工 Golden 50 和 student memo review 尚未完成；页面明确标示这些限制。


### 10,000 checkpoint and recorded recovery

Two-worker checkpoint configuration preserves the existing label/cache identity. Both workers share one dispatch limiter and the same transactional budget ledger; every successful classification is committed before more work is admitted. The formal cold 100 benchmark still requires one worker. All 41 current offline tests pass, including concurrent reservations and failure recovery.

The actual recorded 10k stop/resume demonstration is in `evidence/recovery-10k/stop-resume.html` (offline player) and `stop-resume.cast` (original timestamps). Two real invocations saved 25 new unique texts each. Completed original IDs increased from 1,463 to 1,488 on resume, with zero already-saved IDs reclassified. This is a terminal recording, not a screen video.

The remaining 10k checkpoint is running with `python3 -m pipeline.advance_checkpoint`. It resumes only explicit runtime-cap pauses; other errors stop visibly. Its cumulative allocation is USD0.80 within the original USD1 project budget. Completion and warm replay must be confirmed in saved measurements; starting this run does not establish final coverage or human accuracy. The live dashboard currently displays the completed 500 checkpoint.


### Golden50 update — 2026-10-19

The user supplied C24=usability. All50 rows in `golden-50-labels_assisted.xlsx` pass completeness and source validation. The reference CSV is `evals/golden_50_assisted.csv`; it intentionally does not replace or mislabel the independent-human template. `evals/golden_50_assisted.provenance.json` records student labels, authorized severity corrections, entity normalization and AI-extracted quotes. Predictions used only original texts and the frozen configuration; six exact-text results were reused and44 new Jev classifications completed. No reference labels were sent to the model or used to tune its prompt.

Diagnostic agreement is62% topic,78% intent,66% severity,40% needs_review and54% entity sets; sentiment is within0.25 on72% of cases. These are reference-agreement measurements, not certified population accuracy. See `evals/golden_50_評估說明.md` for cases and limitations.

The10k run resumed after an extraction quote was found to omit source newlines. A deterministic whitespace-only repair restores the exact source span; it cannot repair fabricated words or case changes. The saved provider response was reused without new charges, and both original failed attempts remain logged.44 offline tests pass. Current completion must be read from saved run status; the paid100k run is not started.
