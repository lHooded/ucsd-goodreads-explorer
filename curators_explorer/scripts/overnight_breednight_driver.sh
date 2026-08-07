#!/usr/bin/env bash
set -u
cd /home/ifrankling/unsw/novels
PY=.venv/bin/python
DATA=curators_explorer/data
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "waiting for novels-breeding to finish"
while systemctl --user is-active --quiet novels-breeding; do sleep 60; done
log "breeding done"

log "census beta 2.5 starts=1000"
env PYTHONPATH=. $PY curators_explorer/scripts/research_seedless_attractor_census.py \
  --starts 1000 --beta 2.5 --seed 20260807 --tag breednight_b25 \
  >> "$DATA/breednight_census_b25.log" 2>&1
log "census b25 done rc=$?"

log "census beta 4.0 starts=512"
env PYTHONPATH=. $PY curators_explorer/scripts/research_seedless_attractor_census.py \
  --starts 512 --beta 4.0 --seed 20260807 --tag breednight_b40 \
  >> "$DATA/breednight_census_b40.log" 2>&1
log "census b40 done rc=$?"

log "census beta 1.5 starts=512"
env PYTHONPATH=. $PY curators_explorer/scripts/research_seedless_attractor_census.py \
  --starts 512 --beta 1.5 --seed 20260807 --tag breednight_b15 \
  >> "$DATA/breednight_census_b15.log" 2>&1
log "census b15 done rc=$?"

log "breeding seed 20260808"
env PYTHONPATH=. $PY curators_explorer/scripts/research_canon_breeding.py \
  --tag overnight_b --reps 20 --seed 20260808 --hours 6 \
  >> "$DATA/canon_breeding_overnight_b.log" 2>&1
log "breeding_b done rc=$?"
