# BrightData Goodreads metadata audit

The downloaded BrightData CSV is joined to UCSD by exact Goodreads edition `book_id` extracted from `url`. No fuzzy title or author matching is used. The work-level year is the earlier of the modal valid BrightData `first_published` year across matched editions and the minimum UCSD edition year. A claimed first publication cannot logically postdate an observed edition.

Runtime: **3.6s**. The 7.72 GiB CSV becomes a 392.0 MiB useful-column edition table and a 82.9 MiB joined work table.

## Coverage

- BrightData editions: **6,354,752**; parsed first-published years: **6,121,957**; authors: **6,354,699**; genre lists: **1,729,540**.
- UCSD works: **1,521,963**; exact matched works: **1,255,255** from **1,256,941** matched editions.
- BrightData-year works: **1,234,270**; UCSD-year works: **1,181,918**; combined best-year works: **1,423,253**.
- Work-level author coverage: **1,255,248**; genre coverage: **836,461**.
- Of **478,278** works with both author names, **441,914** agree after simple normalization and **36,364** differ; BrightData fills **3** blank current names.

## Date comparison

Where both exist, BrightData is earlier for **186,119** works and later for **8,160**; median absolute gap is **0 years**. **72** matched works have more than one BrightData first-published year across editions.
**877** works have a chosen year below 1000 and are flagged `ancient_year_era_uncertain`: the scrape does not reliably preserve BCE/CE semantics for values such as Homer's 701. This does not affect the canon oldness score because all such years are already at its capped maximum.

| work | author | Bright mode | Bright min | UCSD edition min | chosen | matched editions | distinct Bright years |
|---|---|---:|---:|---:|---:|---:|---:|
| *Moby-Dick or, The Whale* | Herman Melville | 1851 | 1851 | 1923 | 1851 | 1 | 1 |
| *The Brothers Karamazov* | Fyodor Dostoevsky | 1880 | 1880 | 1912 | 1880 | 1 | 1 |
| *The Great Gatsby* | F. Scott Fitzgerald | 1925 | 1925 | 1925 | 1925 | 1 | 1 |
| *The Odyssey* | Homer | 701 | 701 | 1935 | 701 | 1 | 1 |
| *The Odyssey* | Homer | 2010 | 2010 | 2010 | 2010 | 1 | 1 |
| *Ulysses* | James Joyce | 1922 | 1922 | 1934 | 1922 | 1 | 1 |

## Stored fields

The compact edition table retains URL, title, parsed author list, primary author, parsed genre list, raw and parsed first-publication date, rating count, and average rating. The work table adds exact-match coverage, BrightData year diagnostics, UCSD fallback years, the chosen year with provenance, and representative URL/author/genres. The same rows are materialized as `brightdata_work_metadata` in `explorer.duckdb` for later frontend filtering without reparsing or attaching the source CSV.
