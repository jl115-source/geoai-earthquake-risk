# Final pre-2A amendment: two-event hazard and encoder preflight

This amendment precedes every learned damage-model fit. It preserves the target,
cohort, four primary arms, city folds, 16 engineered features, primary 1024-D
encoder representation and regularized readout family. B0 is unchanged.

## Hazard: two separate major-event components

Primary H is **[ln(PGA_M7.8_g), ln(PGA_M7.5_g)]**. The M7.8-only version is a
prespecified sensitivity on the identical records and folds. There is no fitted
hazard aggregation, no choice of shock by damage association, and no max-PGA
replacement of the primary vector.

The target was recorded after the sequence, so a single-shock hazard could leave
the EO representation acting as a geographic proxy for omitted second-event
shaking. Adding the second component addresses this specific omitted-hazard
concern; it does not identify a causal vulnerability effect or account for every
aftershock, duration, recovery/repair process or sequence interaction.

The existing M7.8 companion XML remains pinned and unchanged. The added source is
the [official USGS M7.5 event](https://earthquake.usgs.gov/earthquakes/eventpage/us6000jlqa/executive),
2023-02-06 **10:24:48 UTC** (event detail milliseconds: .811), `us6000jlqa`.
We selected the preferred USGS product from its official event metadata, not using
survey labels or model scores, then pinned the immutable version URL:

`https://earthquake.usgs.gov/product/shakemap/us6000jlqa/us/1756575631263/download/grid.xml`

- SHA256: `8847f001058139c933da760bf3eb8d6ff1dbecac154740c0492cd111f7d5a304`.
- ShakeMap version **12**, XML process timestamp **2025-08-30T17:39:36**;
  code version `4.4.5.dev0+g087a9359.d20250728`.
- 481×421 nodes, longitude 35.2–39.2, latitude 36.0–39.5. The grid is coarser
  than the companion M7.8 grid; retain separate sampling-distance provenance.
- XML PGA/PSA `%g` is divided by 100; PGV remains cm/s. Field indices are read
  by name, including the extra PSA06 column in this product.
- Nearest actual printed node, lower-coordinate tie break, no extrapolation.
  Invalid/outside/zero PGA fails eligibility for both-event primary H.
- This reconstructed product contains 75 seismic stations and 423 intensity
  observations. It is a retrospective hazard estimate, not a pre-event map or
  an assertion of perfectly exogenous ground truth. Its macroseismic inputs and
  differing product vintage add uncertainty beyond the original survey labels.

**Executed:** all 559 rows are in the second grid. PGA spans **0.01611–0.08479 g**;
maximum sampling distance is **579.895 m**. The cohort stays **498 records / 445
sites**. The full fold CSV is byte-identical to the pre-amendment file; all original
eligibility fields and weights are unchanged. No survey location is removed or
moved to accommodate the added hazard.

## Secondary probability diagnostics

Five-class normalized RPS remains primary. Alongside P(D>0), add **P(D≥3)** as
the sum of the grade-3 and grade-4 predicted probabilities. Report site-weighted
Brier scores and reliability tables with fixed [0,.1,…,1] bins, with bin record
counts and total site weight. Empty bins are explicitly null. These are
diagnostics from the same five-class probabilities, not separately fitted binary
models or held-out-city recalibration. `src/models/damage_metrics.py` implements
and tests these definitions using synthetic probability arrays only.

There are **112** eligible severe-or-worse observations, but only two grade-4
observations. Grade-4 recall remains descriptive and unstable, not a headline
performance claim.

## Fixed PCA robustness check

Keep all 1024 dimensions in the primary SatMAE arm. One sensitivity uses exactly
**64 PCA components**, deterministic full SVD, no whitening. Fit centering and
components on raw embeddings from **training sites only**, one vector per exact
coordinate. Apply that transform unchanged to validation/test; fit subsequent
score scaling only on training data. H/X, target, folds and C grid are unchanged.
Do not tune component count, select the primary conclusion by this check, or fit
PCA on all cities. Fewer than 65 training sites would produce an explicit failure,
not silent dimension reduction. **No PCA is fitted in this amendment.**

## Reproduce the actual checkpoint/inference preflight

The official pretraining checkpoint and source stay outside Git. Preserve the
weights' CC BY 4.0 attribution and the source's separate **CC BY-NC 4.0** licence.
Use an isolated inference environment; the data-pipeline environment is unchanged.

```bash
python3 -m venv .venv-eo
.venv-eo/bin/python -m pip install -r requirements-eo.txt
mkdir -p data/raw/geoai_1f/satmae
curl -L --fail --retry 3 -C - \
  -o data/raw/geoai_1f/satmae/pretrain-vit-large-e199.pth \
  'https://zenodo.org/records/7325339/files/pretrain-vit-large-e199.pth?download=1'
.venv-eo/bin/python -m src.features.satmae_preflight --fetch-source --run-name run_a
.venv-eo/bin/python -m src.features.satmae_preflight --run-name run_b \
  --compare data/processed/geoai_1f/satmae_preflight/run_a/embeddings.npy
```

Run the two-event data audit and freeze first using the README commands. The
preflight verifies published checkpoint bytes/MD5, records SHA256, checks pinned
source hashes and uses PyTorch weights-only deserialization (with only the
checkpoint's `argparse.Namespace` metadata type explicitly allowed).

Every tensor in the official architecture must load with strict key/shape checks.
Meta-device construction skips random initialization only because full strict
loading restores every tensor, including fixed positional/channel embeddings.
No unmatched encoder weight can silently remain random. The compatibility adapter
removes obsolete `qk_scale=None` from pinned source for timm 0.9.16; its default
attention scaling is unchanged. The decoder and optimizer are never executed.

An identity no-mask path prevents upstream mask-ratio-zero token shuffling.
CPU float32, four threads, deterministic algorithms and non-fused attention are
fixed. Mean-pool the 432 final-normalized non-CLS tokens into 1024 dimensions.
Read only eligibility/ID/city/location metadata to choose the first eligible
building ID in each city; labels never enter extraction. Ten city chips are
repeated with two RNG seeds, then repeated in a fresh process. Require finite,
nonconstant embeddings and byte-identical outputs. Local outputs include vectors,
row identities, input hashes, strict-load evidence, implementation hash, versions
and timings. This is a ten-chip smoke test, not full-cohort extraction or a claim
of bitwise portability across hardware/backends.

Execution evidence is recorded in `satmae_preflight_execution.json` after a
successful preflight. The separate CSB access check remains non-blocking. No
damage-model fit, PCA fit, architecture search or feature hunting is authorized
by running this preflight; the next fitting work is the deliberately fixed 2A.

## Executed preflight result

**Passed.** The 3,949,597,273-byte checkpoint matches published MD5
`436bcd815194afdae38f3e023c74e9cd`; its locally verified SHA256 is
`1b120cbe1beac0b70a53cc3554b13f1c1025ee3b3e360986d01095010ef9bb64`.
All **408 tensors** loaded strictly, covering **299 encoder tensors / 303,083,008
encoder elements**. All ten cities produced finite, distinct 1024-D vectors.
Different-seed repeats and two independent processes were **byte-identical**:
embedding-file SHA256 `e5be7f63b9afdf29577dbfa9b715f13b909345c59cb84fac2b1d76c5dadf6f75`.
Mean inference time was **0.51 and 0.63 seconds/chip** in the two runs, excluding
loading/checksum overhead, on the recorded CPU runtime. No decoder, optimizer,
PCA, readout or damage-model training was executed. [Machine-readable evidence](satmae_preflight_execution.json).

**82 unit/data tests pass.** The neural smoke test is separately executed locally
against the actual checkpoint; lightweight CI does not download four gigabytes
of weights. Full-cohort extraction and the fixed readout benchmark are 2A work.
