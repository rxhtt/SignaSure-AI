from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

VALID_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
FORGED_KEYS = ["forg", "forgery", "forgeries", "fake", "imitation"]
GENUINE_KEYS = ["genuine", "real", "auth", "original", "true"]


def load_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def infer_label(path: Path) -> int | None:
    parts = [p.lower() for p in path.parts]
    text = " ".join(parts)
    if any(k in text for k in FORGED_KEYS):
        return 0
    if any(k in text for k in GENUINE_KEYS):
        return 1
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=None)
    args = parser.parse_args()

    cfg = load_config()
    raw_dir = Path(args.raw_dir) if args.raw_dir else Path(cfg["raw_dir"])
    manifest_path = Path(cfg["manifest_path"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in raw_dir.rglob("*"):
        if path.suffix.lower() not in VALID_EXTS:
            continue
        label = infer_label(path)
        if label is None:
            continue
        rows.append({"path": str(path), "label": int(label)})

    if not rows:
        raise SystemExit("No labeled images found. Ensure folders include 'genuine' or 'forged'.")

    df = pd.DataFrame(rows).sample(frac=1.0, random_state=int(cfg["seed"]))
    df.to_csv(manifest_path, index=False)

    print(f"Wrote manifest with {len(df)} samples to {manifest_path}")


if __name__ == "__main__":
    main()
