# Final independent verification feedback

Selected sample: 5000 original IDs. Valid comparisons: 4990. Failed independent checks: 10. Failed checks remain in the sample denominator and never count as agreements. Sentiment MAE uses valid comparisons only.

This measures model disagreement, not human accuracy. No first-pass label was overwritten to improve agreement. Golden 50 reference answers were not supplied to either model.

## Observed disagreements

- topic: usability → other — review `000398f2-7667-4fa2-8c20-f5e1ec8fb8dd`
  Source: 'App has become unusable since the new update. So disappointing.'
- topic: usability → billing — review `006c0617-920d-42aa-a723-34700531fc2f`
  Source: 'Blood useless app It gives you 2-3 adds after every song and forces you to buy premium and the adds are irritating af Autoplay has stopped working Unless you can buy premium this app is useless for you'
- topic: usability → playback — review `00841cbf-c015-4595-83d9-324150c8fd67`
  Source: "It's okay untill I run out of skips and it plays any song that isn't on my playlist"
- topic: usability → other — review `014ce1a3-7bdb-4bca-827a-6213875cf2ca`
  Source: 'Spotify is so amazing and easy to use it'
- topic: usability → playback — review `01acf9f3-659b-40ef-b696-d969d69741df`
  Source: 'The permanent shuffle play is annoying and also the app frequently stops so do the right thing and fix it Please remove the permanent shuffle play -Thank you'
- intent: complaint → praise — review `00630874-b2b5-4856-9653-69fb6ab96102`
  Source: "To me it's really good it's not the best but it's still good"
- intent: complaint → unclear — review `01799004-8b95-4ac8-bc64-2ebab75bf58e`
  Source: 'Hate 😡'
- intent: unclear → request — review `025abad4-6c50-4ea6-bb38-ac8bf39cc9d0`
  Source: 'Please keep something free 🙃'
- intent: praise → unclear — review `034be453-570e-4bbc-903c-2396b8775659`
  Source: 'Da best fs'
- intent: praise → unclear — review `03c1b77e-5600-4143-a56a-1238db4091b6`
  Source: 'THATS VERY CRAZY AND SUPERFANTASTIC'
- severity: 2 → 3 — review `000c1149-e4a1-4bc0-8fb9-c17434dc67fc`
  Source: "it's great and all but everytime I listen to my liked songs Playlist a random song comes on and it's not even on my Playlist thats just stupid"
- severity: 2 → 1 — review `005d7110-a229-4ede-b1c4-384966e49804`
  Source: 'My favourite app is now completely ruined you ruined your app haha imma deleting this appp bye bye Spotify....... Wynk is better than you huh'
- severity: 2 → 1 — review `01799004-8b95-4ac8-bc64-2ebab75bf58e`
  Source: 'Hate 😡'
- severity: 2 → 3 — review `01acf9f3-659b-40ef-b696-d969d69741df`
  Source: 'The permanent shuffle play is annoying and also the app frequently stops so do the right thing and fix it Please remove the permanent shuffle play -Thank you'
- severity: 1 → 2 — review `01dda960-af83-4c0a-b414-3a0fdefff969`
  Source: "Why ain't the canvas option showing in the settings?"
- needs_review: True → False — review `000b795c-123f-4d76-8fb6-e49983397c81`
  Source: 'Very good'
- needs_review: True → False — review `0038eef5-f6c2-43f8-9cd6-e5bf379bf5fb`
  Source: 'Finally removed waze, so 5 stars as promised.'
- needs_review: True → False — review `005d7110-a229-4ede-b1c4-384966e49804`
  Source: 'My favourite app is now completely ruined you ruined your app haha imma deleting this appp bye bye Spotify....... Wynk is better than you huh'
- needs_review: True → False — review `006c6004-3f3e-456c-b090-54f34aac8985`
  Source: 'Great'
- needs_review: True → False — review `009b83e9-1c6c-46b0-9326-6a6265e2d158`
  Source: "It's too good"

## Bounded verifier failures

- Review `1118521e-67a6-4966-9148-cf73f5f555e4`: Both independent responses normalized source dere to there; evidence quote is not verbatim. Bounded retries exhausted. No manual prediction correction. Saved attempt `5a3ad6c4a1394980bf739c755f751ba5`.
- Review `3d2d5338-8186-44f8-b411-c7345180c334`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `52ae3f741b724dc89858d4cccb9ddbe6`.
- Review `8445fb00-52db-4fda-bcad-c1a5d5631db3`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `0ac88d6851f843d7bd20c57d833a501f`.
- Review `908e81f4-324d-45d4-8104-0d4abd6b8e52`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `1768e8e59da34af6a18bcf21437bc69e`.
- Review `91278b5d-8ac0-4479-aecb-3f18d17c3e3a`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `4d1ed609b7994ba6a081782610f457eb`.
- Review `985498af-9201-421a-a84d-241c819e4a36`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `0b8c0e02a4334cf0b293dca255946aa9`.
- Review `9fe6c96d-1d8c-46d5-a537-1fa0bb1db23a`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `d9909fee943c444496690d32a20b80c2`.
- Review `b7dc4f2a-2982-4f03-9e3e-d36856211676`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `eee46b665b424680b7d780f22556d3c0`.
- Review `ce8ee1b8-39a7-4a53-a336-f648f86ea29a`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `242766079e2d4e709d2a4d3a364ee386`.
- Review `f6a4f568-ca67-453d-accb-c386ebe772af`: Independent response invalid after bounded retries; excluded from valid comparisons, counted as failed verification. Saved attempt `94aa9e2cff9c460bb7cc62e83c5c74d1`.

## Interpretation

Inspect topic boundaries, severity evidence and review flags separately. A quote mismatch is an extraction/validation failure and cannot establish a semantic label error. Do not change predictions based only on the verifier, and do not tune prompts on the held-out reference. Prioritize manual inspection of severe functional harm and recurring confusion patterns before using the recommendation for a product decision.
