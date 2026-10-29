"""Train the EMBER-2018 LightGBM malware classifier.

Downloads are not handled here; point ``--data-dir`` at the extracted
``ember2018`` folder (from ``ember_dataset_2018_2.tar.bz2``).

Outputs:
    backend/app/ml/ember_model.txt      LightGBM text model (committed)
    backend/app/ml/ember_metrics.json   evaluation metrics
    backend/app/ml/ember_holdout.jsonl  test-set predictions for the dashboard

Usage:
    python scripts/train_ember_model.py \
        --data-dir "C:/Users/Kaustub Lade/Downloads/ember-data/ember2018" \
        --max-train 200000 --max-test 40000 --holdout 400
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

DIM = 2381
APP_ML = BACKEND_ROOT / "app" / "ml"


# --------------------------------------------------------------------------- #
# dataset loading
# --------------------------------------------------------------------------- #
def _memmap(path: Path, dtype=np.float32) -> np.ndarray:
    return np.memmap(path, dtype=dtype, mode="r")


def load_vectorized(data_dir: Path, split: str, limit: int | None):
    """Load EMBER's pre-vectorized matrices when present.

    Returns ``(X, y, idx)`` where ``idx`` holds the original row numbers so
    metadata rows can be matched up after sub-sampling.
    """
    x_path = data_dir / f"X_{split}.dat"
    y_path = data_dir / f"y_{split}.dat"
    if not x_path.exists() or not y_path.exists():
        return None
    X = _memmap(x_path)
    y = _memmap(y_path)
    rows = X.size // DIM
    X = X.reshape(rows, DIM)
    y = np.asarray(y[:rows])
    idx = np.arange(rows)
    if limit and rows > limit:
        # deterministic stride keeps the class balance intact
        step = max(1, rows // limit)
        idx = np.arange(0, rows, step)[:limit]
        X = np.asarray(X[idx])
        y = y[idx]
    else:
        X = np.asarray(X)
    return X, y, idx


def iter_jsonl(data_dir: Path):
    """Yield raw feature dicts from the JSONL shards of the archive."""
    shards = sorted(data_dir.glob(f"*features*.jsonl")) or sorted(data_dir.glob("*.jsonl"))
    for shard in shards:
        with shard.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def vectorize_jsonl(data_dir: Path, limit: int, seed: int):
    """Vectorize a random subset of raw JSONL rows using the vendored extractor."""
    from app.services.ember_features import PEFeatureExtractor

    extractor = PEFeatureExtractor(print_feature_warning=False)
    rng = np.random.default_rng(seed)
    X, y, meta = [], [], []
    seen = 0
    for obj in iter_jsonl(data_dir):
        seen += 1
        # keep roughly `limit` rows without knowing the total up front
        keep_prob = min(1.0, limit / max(seen, 1)) if len(X) < limit else 0.0
        if keep_prob <= 0 or rng.random() > keep_prob:
            continue
        label = int(obj.get("label", 0))
        if label < 0:
            continue  # unlabelled rows
        try:
            vec = extractor.process_raw_features(obj)
        except Exception:
            continue
        X.append(np.asarray(vec, dtype=np.float32))
        y.append(label)
        meta.append(
            {
                "sha256": obj.get("sha256"),
                "label": label,
                "family": (obj.get("avclass") or "").split(".")[0] or None,
                "appeared": obj.get("appeared"),
            }
        )
        if len(X) >= limit:
            break
    if not X:
        raise SystemExit("no usable rows found in JSONL")
    return np.vstack(X), np.asarray(y), meta


def load_pool(pool_dir: Path):
    """Load a vectorized pool produced by ``vectorize_ember_jsonl.py``."""
    x_path = pool_dir / "X_pool.dat"
    y_path = pool_dir / "y_pool.dat"
    if not x_path.exists() or not y_path.exists():
        return None
    y = np.fromfile(y_path, dtype=np.float32).astype(np.int8)
    X = np.memmap(x_path, dtype=np.float32, mode="r")
    if X.size % DIM:
        raise SystemExit(f"corrupt pool: {x_path} not a multiple of {DIM}")
    X = np.asarray(X.reshape(X.size // DIM, DIM))
    if len(y) != len(X):
        raise SystemExit(f"pool size mismatch: X={len(X)} y={len(y)}")
    meta = None
    meta_path = pool_dir / "metadata_pool.csv"
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            meta = list(csv.DictReader(fh))
    return X, y, meta


def split_pool(X, y, meta, val_fraction: float, seed: int):
    """Stratified random split so reported metrics come from unseen samples."""
    rng = np.random.default_rng(seed)
    test_parts = []
    for label in (0, 1):
        idx = np.flatnonzero(y == label)
        rng.shuffle(idx)
        n_val = max(1, int(round(len(idx) * val_fraction)))
        test_parts.append(idx[:n_val])
    test_idx = np.sort(np.concatenate(test_parts))
    train_idx = np.setdiff1d(np.arange(len(y)), test_idx)
    meta_train = [meta[i] for i in train_idx] if meta else None
    meta_test = [meta[i] for i in test_idx] if meta else None
    return (
        X[train_idx],
        y[train_idx],
        X[test_idx],
        y[test_idx],
        meta_train,
        meta_test,
    )


def load_metadata(data_dir: Path, split: str = "train"):
    """Load EMBER's metadata CSV for a split (train uses ``metadata.csv``)."""
    if split == "train":
        names = ["train_metadata.csv", "metadata.csv", "metadata"]
    else:
        names = ["test_metadata.csv", "test_metadata"]
    for name in names:
        path = data_dir / name
        if path.exists():
            with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
                rows = list(csv.DictReader(fh))
            # normalise headers (some releases pad them with spaces)
            return [
                {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                for row in rows
            ]
    return None


# --------------------------------------------------------------------------- #
# training
# --------------------------------------------------------------------------- #
def evaluate(y_true, proba, threshold=0.5):
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
        confusion_matrix,
    )

    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "accuracy": round(float(accuracy_score(y_true, pred)), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the EMBER-2018 LightGBM model")
    parser.add_argument("--data-dir", help="extracted ember2018 folder (with .dat matrices)")
    parser.add_argument("--pool-dir", help="vectorized pool from vectorize_ember_jsonl.py")
    parser.add_argument("--test-pool-dir", help="optional official test pool (overrides the split)")
    parser.add_argument("--val-fraction", type=float, default=0.15, help="pool mode: held-out share")
    parser.add_argument("--max-train", type=int, default=200_000)
    parser.add_argument("--max-test", type=int, default=40_000)
    parser.add_argument("--holdout", type=int, default=400, help="test rows written for the dashboard backfill")
    parser.add_argument("--trees", type=int, default=400)
    parser.add_argument("--leaves", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.data_dir and not args.pool_dir:
        parser.error("one of --data-dir or --pool-dir is required")

    import lightgbm as lgb

    if args.pool_dir:
        pool_dir = Path(args.pool_dir)
        pool = load_pool(pool_dir)
        if pool is None:
            raise SystemExit(f"no X_pool.dat/y_pool.dat in {pool_dir}")
        X_all, y_all, meta_all = pool
        print(f"[1/4] pool: {X_all.shape} from {pool_dir}")

        if args.test_pool_dir:
            test_pool = load_pool(Path(args.test_pool_dir))
            if test_pool is None:
                raise SystemExit(f"no X_pool.dat/y_pool.dat in {args.test_pool_dir}")
            X_train, y_train, meta_train = X_all, y_all, meta_all
            X_test, y_test, meta_test = test_pool
            idx_train = idx_test = None
            print(f"      train={X_train.shape} official test split={X_test.shape}")
        else:
            X_train, y_train, X_test, y_test, meta_train, meta_test = split_pool(
                X_all, y_all, meta_all, args.val_fraction, args.seed
            )
            idx_train = idx_test = None
            print(f"      train={X_train.shape} validation={X_test.shape} (val_fraction={args.val_fraction})")
    else:
        data_dir = Path(args.data_dir)
        if not data_dir.exists():
            raise SystemExit(f"data dir not found: {data_dir}")

        print(f"[1/4] loading dataset from {data_dir}")
        train = load_vectorized(data_dir, "train", args.max_train)
        test = load_vectorized(data_dir, "test", args.max_test)
        meta_train = load_metadata(data_dir, "train")
        meta_test = load_metadata(data_dir, "test")

        if train is None or test is None:
            print("      pre-vectorized .dat files not found, vectorizing JSONL instead")
            X_train, y_train, _ = vectorize_jsonl(data_dir, args.max_train, args.seed)
            X_test, y_test, meta_test = vectorize_jsonl(data_dir, args.max_test, args.seed + 1)
            idx_train = idx_test = None
            meta_train = None
        else:
            X_train, y_train, idx_train = train
            X_test, y_test, idx_test = test
            print(f"      train={X_train.shape} test={X_test.shape}")

    print(f"      malicious share: train={y_train.mean():.3f} test={y_test.mean():.3f}")

    print(f"[2/4] training LightGBM ({args.trees} trees, {args.leaves} leaves)")
    dtrain = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
    dvalid = lgb.Dataset(X_test, label=y_test, reference=dtrain, free_raw_data=False)
    params = {
        "objective": "binary",
        "metric": ["auc", "binary_logloss"],
        "num_leaves": args.leaves,
        "learning_rate": 0.08,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "min_data_in_leaf": 50,
        "max_bin": 255,
        "verbosity": -1,
        "seed": args.seed,
        "num_threads": 0,
        "force_row_wise": True,
    }
    booster = lgb.train(
        params,
        dtrain,
        num_boost_round=args.trees,
        valid_sets=[dvalid],
        valid_names=["test"],
        callbacks=[lgb.early_stopping(40, verbose=False), lgb.log_evaluation(50)],
    )

    print("[3/4] evaluating")
    proba = booster.predict(X_test, num_iteration=booster.best_iteration)
    metrics = evaluate(np.asarray(y_test), proba)
    metrics.update(
        {
            "dataset": "EMBER-2018 (ember_dataset_2018_2)",
            "model": "lightgbm",
            "feature_version": 2,
            "feature_count": DIM,
            "trees": int(booster.best_iteration or args.trees),
            "train_samples": int(X_train.shape[0]),
            "test_samples": int(X_test.shape[0]),
            "malicious_share_test": round(float(np.mean(y_test)), 4),
        }
    )
    print("      " + json.dumps(metrics))

    print("[4/4] writing artifacts")
    APP_ML.mkdir(parents=True, exist_ok=True)
    model_file = APP_ML / "ember_model.txt"
    booster.save_model(str(model_file), num_iteration=booster.best_iteration)
    (APP_ML / "ember_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    holdout_file = APP_ML / "ember_holdout.jsonl"

    # Records written for the dashboard must carry a real EMBER sha256, so the
    # split that actually has metadata is the one we export.
    if meta_test:
        src_X, src_y, src_idx, src_meta, split_name = X_test, y_test, idx_test, meta_test, "test"
    else:
        src_X, src_y, src_idx, src_meta, split_name = X_train, y_train, idx_train, meta_train, "train"

    rng = np.random.default_rng(args.seed)
    y_arr = np.asarray(src_y)
    n_mal = min(int(args.holdout * 0.65), int((y_arr == 1).sum()))
    n_ben = min(args.holdout - n_mal, int((y_arr == 0).sum()))
    mal_pos = np.flatnonzero(y_arr == 1)
    ben_pos = np.flatnonzero(y_arr == 0)
    sel = np.sort(
        np.concatenate(
            [
                rng.choice(mal_pos, size=n_mal, replace=False),
                rng.choice(ben_pos, size=n_ben, replace=False),
            ]
        )
    )
    sel_proba = booster.predict(np.asarray(src_X[sel]), num_iteration=booster.best_iteration)

    holdout_rows = 0
    skipped = 0
    with holdout_file.open("w", encoding="utf-8") as fh:
        for k, pos in enumerate(sel):
            orig = int(src_idx[pos]) if src_idx is not None else int(pos)
            info = src_meta[orig] if src_meta and 0 <= orig < len(src_meta) else {}
            sha = str(info.get("sha256") or "").lower()
            if len(sha) != 64:  # no real sample identity -> cannot be presented
                skipped += 1
                continue
            family = info.get("family") or info.get("avclass") or ""
            family = family.split(".")[0] if isinstance(family, str) and family.strip() else None
            fh.write(
                json.dumps(
                    {
                        "sha256": sha,
                        "label": int(y_arr[pos]),
                        "family": family,
                        "appeared": info.get("appeared") or info.get("appeared_date"),
                        "probability": round(float(sel_proba[k]), 4),
                        "split": split_name,
                    }
                )
                + "\n"
            )
            holdout_rows += 1

    print(f"      model={model_file} ({model_file.stat().st_size/1e6:.2f} MB)")
    print(f"      holdout rows for backfill: {holdout_rows} (skipped {skipped} rows without sha256)")
    if holdout_rows == 0:
        print("      WARNING: no metadata with sha256 found; dashboard backfill needs real samples")

    metrics["holdout_split"] = split_name
    metrics["holdout_samples"] = holdout_rows
    (APP_ML / "ember_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
