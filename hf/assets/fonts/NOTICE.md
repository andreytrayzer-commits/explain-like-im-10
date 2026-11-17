# Bundled fonts

Used at build time to measure word widths with real metrics (see
`pipeline/hf_letterpress.py`), and loaded in the browser from Google Fonts at
render time. They are committed so a clean checkout can build without a network
fetch.

| Font | Licence | Source |
|---|---|---|
| Anton | SIL Open Font License 1.1 | github.com/google/fonts `ofl/anton` |
| Abril Fatface | SIL Open Font License 1.1 | github.com/google/fonts `ofl/abrilfatface` |
| Bebas Neue | SIL Open Font License 1.1 | github.com/google/fonts `ofl/bebasneue` |
| Rubik Mono One | SIL Open Font License 1.1 | github.com/google/fonts `ofl/rubikmonoone` |

The OFL permits redistribution. Re-fetch them with `python3 pipeline/fetch_fonts.py`.
