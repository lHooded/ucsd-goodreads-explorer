# UCSD Goodreads warehouse

Build from the [UCSD Goodreads Book Graph](https://mengtingwan.github.io/data/goodreads)
(Wan & McAuley). **Academic use only — do not redistribute the raw files.**

## Layout (local)

| Path | Role |
|---|---|
| `data/ucsd_goodreads/raw/` | Original dumps (gzip / CSV) |
| `data/ucsd_goodreads/parquet/` | Columnar extracts |
| `data/ucsd_goodreads/ucsd.duckdb` | DuckDB views over parquet |
| `data/ucsd_goodreads/explorer.duckdb` | Explorer rating / curator tables |

Genre is a filter, not a silo: parquet holds the full catalog; SF (etc.) is a
SQL predicate.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # repo root
./ucsd_goodreads/download.sh
```

| File | ~size | Role |
|---|---|---|
| `goodreads_books.json.gz` | 1.9G | Full catalog |
| `goodreads_interactions.csv` | 4.0G | All ratings (`book_id_map.csv`) |
| `goodreads_book_authors.json.gz` | 18M | Author names |

## Warehouse

```bash
.venv/bin/python -m ucsd_goodreads.warehouse build-parquet --skip-interactions
.venv/bin/python -m ucsd_goodreads.warehouse build-parquet --only interactions
.venv/bin/python -m ucsd_goodreads.warehouse build-db
```

Or one shot: `build-all`.

Then materialize the explorer (see root README):

```bash
.venv/bin/python -m ucsd_explorer.materialize_ratings
```

### Browse with SQL

```bash
.venv/bin/python -m ucsd_goodreads.warehouse query "
  SELECT book_id, title, author_name, sf_core, fantasy, sf_ratio, ratings_count
  FROM books_with_genres
  WHERE sf_core >= 10 AND sf_ratio >= 0.55
  ORDER BY ratings_count DESC
  LIMIT 20
"
```

Useful relations: `books`, `book_shelves`, `authors`, `interactions`,
`books_with_genres`, optional `sf_book_ids` cache (`materialize-sf`).

## Cite

Mengting Wan, Julian McAuley, *Item Recommendation on Monotonic Behavior Chains*, RecSys 2018.

Mengting Wan et al., *Fine-Grained Spoiler Detection from Large-Scale Review Corpora*, ACL 2019.
