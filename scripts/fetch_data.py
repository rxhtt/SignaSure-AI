from __future__ import annotations

import argparse
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi
import yaml


def load_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_latest_zip(raw_dir: Path) -> Path:
    zips = sorted(raw_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        raise FileNotFoundError("No zip file found after Kaggle download.")
    return zips[0]


def fetch_kaggle(dataset: str, raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = raw_dir / "_kaggle_tmp" / datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()

    api.dataset_download_files(dataset, path=tmp_dir, quiet=False, unzip=False)
    zip_path = find_latest_zip(tmp_dir)

    with zipfile.ZipFile(zip_path, "r") as zf:
        target = raw_dir / dataset.replace("/", "_")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        zf.extractall(target)

    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["kaggle"], default="kaggle")
    parser.add_argument("--dataset", default="divyanshrai/handwritten-signatures")
    args = parser.parse_args()

    cfg = load_config()
    raw_dir = Path(cfg["raw_dir"])

    if args.source == "kaggle":
        path = fetch_kaggle(args.dataset, raw_dir)
        print(f"Downloaded dataset to: {path}")


if __name__ == "__main__":
    main()
