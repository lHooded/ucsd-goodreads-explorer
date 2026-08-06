# Detailed Goodreads temporal extraction

The detailed gzip was scanned directly and joined to numeric users and canonical works. Only rated events and the four temporal fields were retained; no decompressed JSON intermediate was written.

- Mode: **full**; rows: **99,282,051**; users: **811,050**; works: **523,822**.
- Output: **1.46 GiB**; extraction time: **6.2 min**.
- Timestamp coverage — added: **100.00%**, updated: **100.00%**, read: **39.95%**, started: **27.61%**.
- Added equals updated: **37.05%**; updated before added: **0.117%**.
- Among populated read dates, read precedes Goodreads addition in **23.73%** of events.
- Only **2,391** `date_added` values (**0.0024%**) fall outside the plausible 2006–2017 Goodreads activity window; no `date_updated` values do. These are excluded from activity-time trajectories. `read_at` is treated separately because legitimate backfilled reading dates may predate Goodreads.
- Duplicate edition/user-work rows retained for explicit downstream collapse: **427,908**.

`added_at` and `updated_at` are Goodreads activity timestamps, not guaranteed rating timestamps. `read_at` and `started_at` are user-entered and nonrandomly missing. Trajectory models must carry timestamp-definition and bulk-import sensitivity axes.
