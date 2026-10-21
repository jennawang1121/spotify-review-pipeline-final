# Golden 50 評估結果

50 條由學生作最終判斷的參考答案與 50 條模型預測均完整。此表呈現與學生判讀的一致率，並不表示人工判讀已由第三方驗證為正確。

主題、意圖、情緒、需覆核欄保留學生答案；C24 使用學生明確指定的 usability。嚴重程度有依指示修正，實體名稱有 AI 格式／原文校正，引用由 AI 摘錄。學生原 Excel 已填寫 49/50 個主題、50/50 個意圖、嚴重程度、情緒與需覆核，以及 32/50 個實體；唯一未填的主題 C24 由學生在聊天中指定。最終 50 筆分類判斷由學生逐條確認為自己的分析。AI 的引用摘錄與格式／規則執行仍按欄位公開；學生逐條確認並採用最終引用，不能宣稱每個儲存格的文字皆由學生親手輸入。

| 欄位 | 一致率 |
|---|---:|
| topic | 62% (31/50) |
| intent | 78% (39/50) |
| severity | 66% (33/50) |
| needs_review | 40% (20/50) |
| entities | 54% (27/50) |

情緒差距在 ±0.25 內：72%。

比較前沒有把參考答案送入模型，也沒有用這 50 條答案調整分類提示。6 條沿用完全相同文字的歷史預測，44 條用既有設定新分類。

## 不一致項目

以下是差異清單，不自動判定哪一方正確，也不會以模型答案覆蓋人工答案。

| Excel 列 | 主題（人工 → 模型） | 意圖（人工 → 模型） | 嚴重程度（人工 → 模型） |
|---:|---|---|---|
| 6 | other → other | cancellation → complaint | 5 → 2 |
| 11 | usability → other | complaint → complaint | 2 → 2 |
| 14 | usability → other | praise → praise | 1 → 1 |
| 16 | usability → playback | request → complaint | 1 → 3 |
| 17 | support → playback | praise → complaint | 1 → 4 |
| 18 | access → other | complaint → complaint | 4 → 2 |
| 21 | usability → usability | request → complaint | 1 → 2 |
| 22 | other → catalog | praise → request | 1 → 1 |
| 24 | usability → catalog | unclear → complaint | 1 → 2 |
| 25 | access → other | complaint → complaint | 2 → 2 |
| 26 | other → other | cancellation → unclear | 5 → 1 |
| 29 | usability → usability | request → request | 1 → 2 |
| 34 | usability → usability | cancellation → cancellation | 5 → 3 |
| 36 | other → other | praise → complaint | 1 → 2 |
| 37 | access → playback | praise → complaint | 1 → 4 |
| 38 | other → usability | complaint → complaint | 5 → 2 |
| 39 | billing → billing | request → unclear | 1 → 1 |
| 42 | other → usability | praise → praise | 1 → 1 |
| 43 | usability → catalog | complaint → complaint | 5 → 3 |
| 47 | usability → other | complaint → complaint | 2 → 2 |
| 48 | usability → playback | complaint → complaint | 5 → 3 |
| 49 | usability → catalog | praise → praise | 1 → 1 |
| 50 | usability → downloads | complaint → complaint | 4 → 3 |
| 51 | other → usability | complaint → complaint | 5 → 2 |
| 52 | billing → billing | complaint → cancellation | 5 → 3 |
| 53 | usability → other | complaint → complaint | 2 → 2 |
| 54 | usability → other | praise → praise | 1 → 1 |

## 學生最終複核確認

2026-10-20（Pacific），學生明確確認：「已逐條複核，標注符合我的判讀」。因此此版為學生逐條複核的 AI 協助參考標注。此確認不改寫原始產生過程，也不代表原先所有欄位均為盲測獨立人工標注；各欄位協助紀錄仍保留。

學生於後續聊天再次確認，原始分類分析是她本人完成；AI 協助應描述為依照她的指示整理、校正和摘錄引用，不應取代學生作為最終判斷者的身分。
