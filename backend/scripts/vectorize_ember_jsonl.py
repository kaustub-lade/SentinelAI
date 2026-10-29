"""Vectorize the raw EMBER-2018 JSONL features into train-ready matrices.

EMBER-2018 ships only raw feature JSONL (``ember2018/train_features_*.jsonl``
and ``test_features.jsonl``), so training needs this step. Sampling is a
single-pass reservoir over labelled rows, which keeps memory flat and gives an
unbiased random subset regardless of shard ordering.

Outputs (in ``--out-dir``):
    X_pool.dat          float32 memmap, shape (n, 2381)
    y_pool.dat          float32 labels, shape (n,)
    metadata_pool.csv   sha256,label,family,appeared  (row-aligned)

Usage:
    python scripts/vectorize_ember_jsonl.py \
        --shards "D:/ember-data/ember2018/train_features_0.jsonl" \
                 "D:/ember-data/ember2018/train_features_1.jsonl" \
        --limit 120000 --out-dir "D:/ember-data/pool"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

DIM = 2381


def main() -> None:
    parser = argparse.ArgumentParser(description="Vectorize EMBER-2018 JSONL features")
    parser.add_argument("--shards", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=120_000)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from app.services.ember_features import PEFeatureExtractor

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extractor = PEFeatureExtractor(print_feature_warning=False)
    if extractor.dim != DIM:
        raise SystemExit(f"unexpected feature dimension {extractor.dim}")

    rng = np.random.default_rng(args.seed)
    X = np.memmap(out_dir / "X_pool.dat", dtype=np.float32, mode="w+", shape=(args.limit, DIM))
    y = np.memmap(out_dir / "y_pool.dat", dtype=np.float32, mode="w+", shape=(args.limit,))
    meta: list[dict | None] = [None] * args.limit

    seen = 0          # labelled rows encountered
    skipped_label = 0
    skipped_error = 0
    started = time.time()

    for shard in args.shards:
        shard_path = Path(shard)
        print(f"reading {shard_path.name} ({shard_path.stat().st_size/1e6:.0f} MB)", flush=True)
        with shard_path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                label = int(obj.get("label", -1))
                if label < 0:
                    skipped_label += 1
                    continue

                # Reservoir: first `limit` rows fill it, later rows replace a
                # random slot with probability limit/seen.
                seen += 1
                if seen <= args.limit:
                    slot = seen - 1
                    keep = True
                else:
                    slot = int(rng.integers(0, seen))
                    keep = slot < args.limit
                if not keep:
                    continue

                try:
                    vector = extractor.process_raw_features(obj)
                except Exception:
                    skipped_error += 1
                    continue
                X[slot] = np.asarray(vector, dtype=np.float32)
                y[slot] = float(label)
                family = obj.get("avclass") or ""
                meta[slot] = {
                    "sha256": (obj.get("sha256") or "").lower(),
                    "label": label,
                    "family": family.split(".")[0] if family else "",
                    "appeared": obj.get("appeared") or "",
                }

                if seen % 5000 == 0:
                    print(f"  seen={seen} elapsed={time.time()-started:.0f}s", flush=True)

    # Drop unfilled trailing slots (reservoir not saturated or skips) and keep
    # rows with a usable sha256 only.
    valid = np.array(
        [i for i in range(args.limit) if meta[i] and len(meta[i]["sha256"]) == 64],
        dtype=np.int64,
    )
    X.flush()
    y.flush()
    if len(valid) == 0:
        raise SystemExit("no usable labelled rows found")

    pool_x = out_dir / "X_pool.dat"
    pool_y = out_dir / "y_pool.dat"
    if len(valid) != args.limit:
        # Compact in chunks so peak memory stays flat even for large pools.
        final_X = np.memmap(pool_x, dtype=np.float32, mode="r", shape=(args.limit, DIM))
        tmp_x = np.memmap(out_dir / "X_pool.tmp", dtype=np.float32, mode="w+", shape=(len(valid), DIM))
        tmp_y = np.memmap(out_dir / "y_pool.tmp", dtype=np.float32, mode="w+", shape=(len(valid),))
        for start in range(0, len(valid), 10000):
            chunk = valid[start : start + 10000]
            tmp_x[start : start + len(chunk)] = final_X[chunk]
            tmp_y[start : start + len(chunk)] = np.asarray(y[chunk])
        tmp_x.flush()
        tmp_y.flush()
        del tmp_x, tmp_y, final_X
        (out_dir / "X_pool.tmp").replace(pool_x)
        (out_dir / "y_pool.tmp").replace(pool_y)

    labels = np.fromfile(pool_y, dtype=np.float32)
    with (out_dir / "metadata_pool.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["sha256", "label", "family", "appeared"])
        writer.writeheader()
        for i in valid:
            writer.writerow(meta[i])

    malicious = int((labels == 1).sum())
    print(
        f"kept {len(valid)} rows ({malicious} malicious / {len(valid)-malicious} benign); "
        f"unlabelled={skipped_label} extract_errors={skipped_error} in {time.time()-started:.0f}s",
        flush=True,
    )
    print(f"wrote {out_dir}", flush=True)


if __name__ == "__main__":
    main()
