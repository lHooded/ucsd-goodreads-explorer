# Goodreads observation ladder

All compact interactions are mapped to canonical works and collapsed to one state per user/work. Edition duplicates use maximum rating and boolean-any read/review.

- Mode: **full**; source rows: **228,648,342**; user-work rows: **210,633,872**.
- Users: **870,607**; works: **523,869**; output: **1.09 GiB**.
- Rated: **98,854,143**; read but unrated: **7,008,040**; shelved/unread: **104,771,689**.
- Read-unrated share of recorded reads: **6.62%**.
- Reviewed: **13,630,476**; reviewed but unrated: **440,527**.
- Edition rows collapsed: **1,315,690**; extraction time: **1.7 min**.

`is_read=false` is only weak awareness/interest evidence. The selection audit uses `is_read=true, rating=0` as the defensible known-read missing-outcome state.
