import argparse
import json

import pandas as pd
import yaml

from common import PROCESSED_DIR, RAW_DIR, RESULTS_DIR, TABLES_DIR, ensure_dirs


def direction(beta: float, ci_low: float, ci_high: float, perm_p: float) -> str:
    if beta > 0 and ci_low > 0 and perm_p < 0.05:
        return "Preliminary support for N-Frame boundary-selection."
    if beta < 0 and ci_high < 0 and perm_p < 0.05:
        return "Evidence against the predicted N-Frame boundary-selection direction."
    return "No evidence for N-Frame boundary-selection."


def main() -> None:
    parser = argparse.ArgumentParser(description="Write markdown summary of N-Frame boundary-selection results.")
    parser.add_argument("--input", default=PROCESSED_DIR / "signal_regions_scored.csv")
    parser.add_argument("--regression", default=TABLES_DIR / "regression_results.json")
    parser.add_argument("--output", default=RESULTS_DIR / "nframe_boundary_results.md")
    args = parser.parse_args()

    ensure_dirs()
    df = pd.read_csv(args.input)
    results = json.loads(open(args.regression, "r", encoding="utf-8").read())
    sources = yaml.safe_load(open(RAW_DIR / "selected_hepdata_sources.yml", "r", encoding="utf-8"))

    z = results["Z"]
    beta = z["ols"]["beta"]
    ci_low = z["bootstrap"]["ci_low"]
    ci_high = z["bootstrap"]["ci_high"]
    perm_p = z["permutation_p_value"]
    verdict = direction(beta, ci_low, ci_high, perm_p)
    sign = "beta > 0" if beta > 0 else "beta < 0" if beta < 0 else "beta ~= 0"

    source_lines = []
    for source in sources["sources"]:
        source_lines.append(
            f"- {source['analysis']} ({source['experiment']}), HEPData {source['hepdata_doi']}, "
            f"{source['luminosity']} fb^-1 at {source['sqrt_s']} TeV."
        )

    markdown = f"""# N-Frame Boundary-Selection Reanalysis

## Data Source Summary
This project is configured to start from public HEPData/published signal-region tables, not raw CERN Open Data.

{chr(10).join(source_lines)}

The current processed table contains {df['analysis'].nunique()} analyses and {len(df)} signal regions. If only `demo_signal_regions.csv` is present, the numerical results below are a pipeline check, not a physics result.

## Boundary-Access Definition
For each signal region,

`Delta_N = N_obs - N_exp`

`Z = (N_obs - N_exp) / sigma_exp`

`B_access = z(MET) + z(HT_or_meff) + z(N_jets) + z(N_leptons) + z(N_btags) + category_bonus`

Missing kinematic features are set to zero after z-scoring, so absent metadata does not create artificial high or low boundary access. `category_bonus` adds one point for compressed spectra, disappearing tracks, long-lived particles, displaced vertices, high-MET labels, and high-multiplicity labels.

In the N-Frame hypothesis, `B_access` is a proxy for event classes occupying high-boundary-access regimes defined by missing information, event complexity, entropy-like multiplicity, long-lived separation, and reconstruction difficulty.

## Regression Result: Z ~ B_access_z
- Signal regions: {results['n_signal_regions']}
- Beta: {beta:.4f}
- Standard error: {z['ols']['std_error']:.4f}
- OLS p-value: {z['ols']['p_value']:.4g}
- Bootstrap 95% CI: [{ci_low:.4f}, {ci_high:.4f}]
- Permutation p-value: {perm_p:.4g}
- Spearman rho: {results['spearman_B_access_z_vs_Z']['rho']:.4f}
- Spearman p-value: {results['spearman_B_access_z_vs_Z']['p_value']:.4g}
- Direction: {sign}

## Delta_N Regression
- Beta: {results['Delta_N']['ols']['beta']:.4f}
- OLS p-value: {results['Delta_N']['ols']['p_value']:.4g}
- Bootstrap 95% CI: [{results['Delta_N']['bootstrap']['ci_low']:.4f}, {results['Delta_N']['bootstrap']['ci_high']:.4f}]
- Permutation p-value: {results['Delta_N']['permutation_p_value']:.4g}

## Interpretation
{verdict}

This is a meta-analysis of signal-region deviations. It does not claim discovery of SUSY, hidden symmetry, or physics beyond the Standard Model.
"""
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
