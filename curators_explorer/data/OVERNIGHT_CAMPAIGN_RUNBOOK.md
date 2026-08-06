# Overnight consensus uncertainty campaign

Started 2026-08-06 00:18 AEST as the persistent user service:

`novels-overnight-consensus.service`

The service runs at nice level 10 and does not require further model/tool calls.

## Scientific stages

1. **Exact expected-inclusion pair estimator + 5,000 user-block replicates**
   - Analytically integrates out the arbitrary 12×12 hash sample.
   - Resamples whole jurors with Poisson(1) weights through all nine community partitions.
   - Estimates conditional score intervals, eligibility probability, and top-k probability.
2. **Teacher-composition jury bootstrap for up to 7.25 hours**
   - Gives the 3,264 covered positive teacher users Exp(1) Bayesian-bootstrap weights.
   - Refits the five-fold rich behavioral model each replicate.
   - Rebuilds a 4,929-person jury inside the fixed broad top 20,000.
   - Reranks 1,146 exact-pair/near-evidence books.
   - Checkpoints every five completed jury refits.

The quick paths completed successfully after catching and fixing an eligibility-reporting bug.
Observed jury-refit speed was 5.3–16.6 seconds/replicate depending on concurrent machine load,
so the wall-clock stop is more reliable than a fixed replicate target.

## Monitoring

```bash
systemctl --user status novels-overnight-consensus.service --no-pager
tail -n 40 /home/ifrankling/unsw/novels/curators_explorer/data/overnight_campaign.log
cat /home/ifrankling/unsw/novels/curators_explorer/data/overnight_uncertainty_full_status.json
cat /home/ifrankling/unsw/novels/curators_explorer/data/overnight_jury_bootstrap_full_status.json
```

The second status file appears only after the first stage finishes setup and begins jury
checkpointing.

## Outputs

- `OVERNIGHT_UNCERTAINTY_FULL_REPORT.md`
- `overnight_uncertainty_full.json`
- `overnight_uncertainty_full_checkpoint.npz`
- `OVERNIGHT_JURY_BOOTSTRAP_FULL_REPORT.md`
- `overnight_jury_bootstrap_full.json`
- `overnight_jury_bootstrap_full_checkpoint.npz`
- `overnight_campaign.log`

## Stop / recovery

Graceful stop:

```bash
systemctl --user stop novels-overnight-consensus.service
```

The jury bootstrap can be resumed from its last five-replicate checkpoint with:

```bash
cd /home/ifrankling/unsw/novels
PYTHONPATH=. .venv/bin/python -m \
  curators_explorer.scripts.research_overnight_jury_bootstrap \
  --mode full --hours 7.25 --max-reps 5000 --resume
```

## Interpretation guardrail

The user-block and teacher-composition intervals are different uncertainty components. Do not
blindly add their widths. Inspect their book-level dependence first. Neither component covers
the choice of teacher definition, missing exposure, or the systematic Γ sensitivity bound.
