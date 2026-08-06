# Detailed Goodreads temporal extraction

The detailed gzip was scanned directly and joined to numeric users and canonical works. Only rated events and the four temporal fields were retained; no decompressed JSON intermediate was written.

- Mode: **quick**; rows: **477,798**; users: **2,101**; works: **124,366**.
- Output: **0.01 GiB**; extraction time: **0.0 min**.
- Timestamp coverage — added: **100.00%**, updated: **100.00%**, read: **43.94%**, started: **30.09%**.
- Added equals updated: **36.28%**; updated before added: **0.113%**.
- Among populated read dates, read precedes Goodreads addition in **22.10%** of events.
- Duplicate edition/user-work rows retained for explicit downstream collapse: **2,285**.

`added_at` and `updated_at` are Goodreads activity timestamps, not guaranteed rating timestamps. `read_at` and `started_at` are user-entered and nonrandomly missing. Trajectory models must carry timestamp-definition and bulk-import sensitivity axes.
