# B0 — Transparent synthetic catastrophe-loss mechanics

This is the first-principles Track B implementation requested alongside 1F. It
does not fit a vulnerability model, use survey damage observations, or estimate
real Türkiye risk. All asset values, taxonomies, fragility parameters, consequence
parameters, intensities and event rates in `configs/risk_b0.json` are **invented
illustrative assumptions**. They are not GEM-calibrated inputs. The predictive
modelling freeze continues to apply to Track A.

## Reproduce

From the repository root, with the existing requirements installed:

```sh
python -m src.risk.b0 --config configs/risk_b0.json --output results/b0
python -m pytest tests/test_risk_b0.py -q
```

The CLI saves the exact configuration and its canonical JSON SHA-256, analytic
event/asset expectations, event occurrence losses, every simulated year's loss,
exact empirical EP curves, return-period loss tables, and AAL contributions by
taxonomy/geography. Outputs stay under ignored `results/b0/`. A seed plus the
same pinned NumPy environment and ordered configuration reproduces outputs.

## Calculation, units and assumptions

There are three assets (total value 450,000 arbitrary replacement-value units),
two synthetic taxonomies and three event types. PGA is in **g**; rates are
occurrences/year; loss has the same units as asset value; AAL has value units/year.
Event-specific PGA vectors are already specified at each asset. There is no
ground-motion model, hazard-map interpolation, or simulated ground-motion
uncertainty in this reference example.

For taxonomy threshold medians `m[k]` and shared positive log-space scale `b`,
the fixed log-logistic fragility is:

\[
q_k(h)=P(D\geq k\mid h)=\{1+\exp[-(\log h-\log m_k)/b]\}^{-1}.
\]

All exceedances are zero at zero PGA. Ordered positive medians and a common scale
prevent crossing curves. Exclusive states are `1-q1`, `q1-q2`, ..., `qK` and sum
to one. These synthetic states 0–4 are **not a harmonization of native survey
damage grades**. No state parameters are inferred from real observations.

Conditional on state `d` and taxonomy, damage ratio `R` has a Beta distribution
with `alpha = mean[d] * concentration` and
`beta = (1-mean[d]) * concentration`. Endpoint means 0 and 1 are point masses.
Consequently `0 <= R <= 1`, `E[R|d] = mean[d]`, and asset loss is `V * R`.
For interior means the conditional variance is `mean*(1-mean)/(concentration+1)`.
The mean-damage-ratio (MDR) table is the conditional mean; the actual sampled
damage ratio is random. We integrate the conditional means exactly:

\[
E[L_e]=\sum_i V_i\sum_d P(D_{ie}=d)\,E[R_i\mid d],
\qquad AAL=\sum_e\lambda_e E[L_e].
\]

Each event type has an independent Poisson count each year, including zero.
Each occurrence gets a fresh damage/consequence draw. Portfolio loss is the sum
of asset losses; annual aggregate is the sum of occurrence losses; annual
occurrence maximum is the largest event loss, zero for an empty year. Definitions
of OEP (annual maximum) and AEP (annual sum) agree with the
[OpenQuake event-based risk documentation](https://docs.openquake.org/oq-engine/3.21/manual/user-guide/configuration-file/event-based-risk-config.html).
This code has not yet been numerically validated against OpenQuake.

`ep_curves.csv` reports strict `P(annual loss > threshold)` at every unique annual
aggregate/maximum value, with all simulated years in the denominator.
Return-period losses use the inverse empirical CDF at `1-1/T`, explicitly NumPy
`method='inverted_cdf'`. With atoms/ties these are generalized quantiles; their
strict exceedance probabilities need not equal `1/T` exactly. They are annual
probability return levels, not inverse occurrence-rate EP levels. No tail
extrapolation or “PML” claim is made. `expected_tail_years = years/T` indicates
the nominal tail sample size; 250 years has only 400 nominal exceedance years in
this run. Monte Carlo error in tail estimates remains even with many years.

## Dependence and uncertainty

Default: damage states are conditionally independent across assets given their
fixed event shaking; Beta consequence draws are also independent. This generally
reduces diversification-tail risk compared with strongly dependent damage.
The optional `damage_dependence: common_uniform` uses one uniform damage-state
quantile per occurrence for all assets. It is a comonotonic damage-state
sensitivity, **not** a calibrated spatial correlation model. Consequence draws
remain independent conditional on states. It preserves each asset's marginal
probabilities and the analytic AAL.

Occurrence random streams are separate from damage/consequence streams, so the
same seed, rates and ordering retain precisely the same event/year occurrences
when comparing these dependence settings. Consequence draws are not deliberately
paired between settings. Reordering/adding event types changes stream assignment.

Poisson counts, damage draws and consequence draws are the implemented aleatory
uncertainty. Fragility medians, scales, rates, values, consequence means and the
dependence assumption are fixed epistemic assumptions; they are **not** sampled
from an epistemic posterior. AAL Monte Carlo standard error measures sampling
precision conditional on those assumptions, not knowledge of real-world risk.

The portfolio is effectively restored between occurrences; damage accumulation,
repair delays, aftershock clustering, depletion and replacement-value changes
are absent. An event cannot exceed total value, but an annual aggregate can.
Loss means direct replacement-cost-equivalent ground-up loss only: no deductible,
limit, insurance/reinsurance, contents, business interruption, inflation, or
currency conversion is asserted.

## Inspected reference result

With seed 17023 and 100,000 years, there are 25,962 event occurrences.

| Quantity | Independent damage | Common-uniform damage sensitivity |
|---|---:|---:|
| Analytic AAL | 8,283.57 | 8,283.57 |
| Simulated AAL | 8,380.73 | 8,279.83 |
| AAL Monte Carlo standard error | 110.33 | 129.78 |
| 100-year OEP loss | 190,107.94 | 242,898.35 |
| 100-year AEP loss | 193,848.36 | 246,214.81 |
| 250-year OEP loss | 264,908.39 | 352,501.20 |
| 250-year AEP loss | 273,473.76 | 366,622.91 |

All amounts are synthetic units. Both estimated AALs are within one Monte Carlo
standard error of the exact expectation. The tail difference illustrates why
dependence matters while marginal expected losses can remain fixed; it is not
evidence about actual earthquake portfolio correlation.

To reproduce the sensitivity without changing the checked-in baseline:

```sh
python - <<'PY'
import json
from pathlib import Path
from src.risk.b0 import run
c = json.loads(Path('configs/risk_b0.json').read_text())
c['damage_dependence'] = 'common_uniform'
summary, tables = run(c)
print(summary)
print(tables['return_period_losses'].to_string(index=False))
PY
```

Tests cover a hand-computed binary-state expectation, normalized/monotone damage
probabilities, Monte Carlo agreement with analytic AAL, same-seed reproducibility,
dependence sensitivity marginals, zero rates/intensities/values, event/annual loss
accounting, `OEP <= AEP`, bounded event loss, and invalid parameters. No external
data or credentials are needed. The next Track B step is a separately approved
GEM/OpenQuake comparison using documented real fragility/consequence inputs and
identical exposure/hazard, without confusing this synthetic B0 with a risk study.
