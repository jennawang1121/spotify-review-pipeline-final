# Course dataset

Received from the user-provided [Google Drive archive](https://drive.google.com/file/d/1P0rUoAS_wVjp3BYKqXMEyD4u0uJP1Bvf/view). Local archive: `course-dataset.zip`; extracted files: `course/`. Download permission may be required for another user. Preserve original CSV bytes.

Archive SHA-256: `ec5a3ddceb68df52cd935b7fb3e1286aea8432d77183fbd54f397695566d5e68`.
All five CSV file sizes and hashes match `course/manifest.json`. The archive contains eleven files, including both specifications and the official checker. Small unmodified reference documents/checker were copied to the project's top-level `course/` for reproducibility; raw data is Git-ignored.

For a fresh checkout, download the supplied ZIP and extract its eleven files directly into `data/course/`, then verify each CSV against the tracked manifest. Do not substitute another Spotify dataset or resave CSVs through a spreadsheet application.

Full corpus: 660,622 rows; 660,609 nonempty; 13 empty; 484,189 unique nonempty texts; no duplicate IDs. Monthly/rating counts match the manifest. Source report and file checks are in `../evidence/`.

`cost_100.csv` is the first 100 rows of `checkpoint_500.csv`, itself the first 500 rows of `analysis_10000.csv`. Golden IDs are disjoint from development IDs. The original golden texts still belong to the full final run, but their human answer columns never enter model requests.
