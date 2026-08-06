# Goodreads observation ladder

All compact interactions are mapped to canonical works and collapsed to one state per user/work. Edition duplicates use maximum rating and boolean-any read/review.

- Mode: **quick**; source rows: **500,000**; user-work rows: **471,053**.
- Users: **1,034**; works: **133,192**; output: **0.00 GiB**.
- Rated: **224,424**; read but unrated: **14,238**; shelved/unread: **232,391**.
- Read-unrated share of recorded reads: **5.97%**.
- Reviewed: **32,788**; reviewed but unrated: **894**.
- Edition rows collapsed: **3,403**; extraction time: **0.0 min**.

`is_read=false` is only weak awareness/interest evidence. The selection audit uses `is_read=true, rating=0` as the defensible known-read missing-outcome state.
