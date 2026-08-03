#!/usr/bin/env bash
# Download UCSD Goodreads Book Graph files needed for SF ballot export.
# Academic use only — do not redistribute.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="${UCSD_RAW:-$ROOT/data/ucsd_goodreads/raw}"
BASE="https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads"
mkdir -p "$RAW"
cd "$RAW"

log() { echo "[$(date -Iseconds)] $*"; }

download() {
  local url="$1" out="$2"
  local min_bytes="${3:-0}"
  if [[ -f "$out" && "${FORCE:-0}" != "1" && "$min_bytes" -gt 0 ]]; then
    local size
    size=$(stat -c%s "$out" 2>/dev/null || echo 0)
    if [[ "$size" -ge "$min_bytes" ]]; then
      log "KEEP $out ($(du -h "$out" | cut -f1))"
      return 0
    fi
  fi
  log "START $out"
  local i=0
  while true; do
    i=$((i + 1))
    if curl -L --fail -C - \
      --connect-timeout 60 --max-time 0 \
      --retry 3 --retry-delay 5 \
      -o "$out" "$url"; then
      log "DONE $out ($(du -h "$out" | cut -f1))"
      return 0
    fi
    log "RESUME attempt=$i for $out"
    sleep 15
    if [[ "$i" -ge 50 ]]; then
      log "FAILED $out"
      return 1
    fi
  done
}

download "$BASE/book_id_map.csv" book_id_map.csv 1000000
download "$BASE/user_id_map.csv" user_id_map.csv 1000000
download "$BASE/goodreads_book_authors.json.gz" goodreads_book_authors.json.gz 1000000
download "$BASE/goodreads_book_genres_initial.json.gz" goodreads_book_genres_initial.json.gz 1000000
download "$BASE/goodreads_book_works.json.gz" goodreads_book_works.json.gz 70000000
download "$BASE/goodreads_books.json.gz" goodreads_books.json.gz 1900000000
download "$BASE/goodreads_interactions.csv" goodreads_interactions.csv 4000000000

# Optional genre slice (faster experiments; misses some pure-SF titles like Light)
if [[ "${WITH_FANTASY_SLICE:-0}" == "1" ]]; then
  download "$BASE/byGenre/goodreads_books_fantasy_paranormal.json.gz" \
    goodreads_books_fantasy_paranormal.json.gz 250000000
  download "$BASE/byGenre/goodreads_interactions_fantasy_paranormal.json.gz" \
    goodreads_interactions_fantasy_paranormal.json.gz 2500000000
fi

log "ALL_DONE → $RAW"
