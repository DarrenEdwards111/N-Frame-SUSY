from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main():
    df = pd.read_csv(ROOT / "data" / "processed" / "event_features_nframe_scored.csv")
    out = pd.concat(
        [
            df.nlargest(max(1, int(0.001 * len(df))), "B_event_z").assign(outlier_set="top_0p1pct_B_event_z"),
            df.nlargest(max(1, int(0.01 * len(df))), "B_event_z").assign(outlier_set="top_1pct_B_event_z"),
            df.nlargest(max(1, int(0.05 * len(df))), "B_event_z").assign(outlier_set="top_5pct_B_event_z"),
        ],
        ignore_index=True,
    )
    out.to_csv(ROOT / "results" / "tables" / "top_boundary_events.csv", index=False)
    print(f"Wrote {len(out)} high-boundary event rows")


if __name__ == "__main__":
    main()
