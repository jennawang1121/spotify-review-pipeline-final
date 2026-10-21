# Inspected final-sample failures and disagreements

These cases were inspected by the assistant from saved original texts and model outputs. They are qualitative error analysis, not new independent human labels. No production prediction was edited to improve agreement. IDs belong to the seeded final verifier sample; complete results are saved by the pipeline when that stage finishes.

| Original review ID | Observed difference | Interpretation and consequence |
|---|---|---|
| `16c035e4-c466-478b-b377-e2c29de86e7d` | Source: “Privacy issues”. Jev severity 5; verifier severity 2; both flag review. | The word privacy alone does not establish the assignment's explicit serious privacy harm. The first-pass 5 is unsupported by the available text. Inspect flagged high-severity cases before operational use; do not treat every privacy mention as a confirmed incident. |
| `0815612d-3495-4bc9-88e3-06139fa247a2` | Source: “No:1 app for ads”. Jev intent unclear/severity 1; verifier complaint/severity 2. | Sarcasm and abbreviated text can cause undercounted complaints. The complaint interpretation is plausible, but it remains an interpretive judgment rather than a new gold label. |
| `08e7ad6b-00b8-4796-9c17-b94f4db7bf46` | Source: “It's hanging”. Both choose playback; Jev unclear/severity 1, verifier complaint/severity 3. | A very short description can still report degraded function. First-pass uncertainty may omit plausible functional complaints from the ranking. |
| `0d188ada-c020-464b-9983-ecf0ed0e9fa0` | The review mentions inability to add songs to the queue and cracks in songs. Jev usability/severity 4; verifier playback/severity 3. | The single-primary-topic requirement forces a choice in a multi-issue review. Both queue controls and audio failures are present. Topic volume and priority are sensitive to this boundary; a future separately evaluated subtopic policy could help. |
| `6747d1a5-7ffd-4eef-8795-6a1c3aa41e5f` | Source: “No option to select song from library”. Jev complaint/severity 4; verifier request/severity 1. | Missing-feature requests and blocked-task reports overlap. The review does not explain prior availability or remaining workarounds. Avoid assuming that either model supplies ground truth. |
| `1118521e-67a6-4966-9148-cf73f5f555e4` | Both verifier attempts changed “dere” to “there” inside the evidence quote. | This is a concrete verbatim-evidence failure. The two attempts remain billed and visible; the independent check is marked failed, not agreement or disagreement. The original first-pass classification remains valid and unchanged. |

## Controls and feedback

1. Preserve the original source and failed raw responses; exact-quote checks catch normalization that would otherwise appear credible.
2. Keep bounded invalid-output retries. Persist failed verification outcomes so a warm replay does not repeatedly charge for the same failed check. Failed checks remain in the selected sample count and are reported separately from valid comparisons.
3. Report per-field results: topic, intent, severity and review flags have different failure modes. Sentiment MAE uses valid comparisons only; model agreement is not human accuracy.
4. Do not overwrite labels with verifier answers or tune prompts on Golden 50. Any later taxonomy/prompt change needs a new version and a separate evaluation.
5. Treat the product ranking as a prioritization signal from historical, self-selected reviews. It does not establish revenue loss, causal retention effects, verified cancellations or confirmed privacy incidents.

## Engineering failures observed during the real final run

- An odd final queue item was admitted twice before its first result committed. The second real prediction conflicted with the immutable cache. The first result and both billed attempts are preserved. An odd-tail regression test now verifies single admission.
- A Python 3.9 socket read timeout escaped the transport's generic timeout branch. The terminated request was reconciled as a client failure; its unknown-charge reservation was retained. Transport now catches socket/protocol exceptions with the configured bounded retry count. The progress supervisor now records unexpected exceptions as visible failures.
- Sites artifact uploads temporarily failed with HTTP 522. The same source archive was retried only after checking that no version had been created; the private deployment subsequently succeeded.
- The multi-thousand-row verification array exceeded a single database value's safe size. It is now stored in bounded 500-row parts and reassembled by the backend. Local round-trip and production classification integrity checks passed.
