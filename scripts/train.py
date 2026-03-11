from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml


def load_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def split_df(df: pd.DataFrame, val_split: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = []
    val_parts = []
    for label, sub in df.groupby("label"):
        sub = sub.sample(frac=1.0, random_state=seed)
        n_val = max(1, int(len(sub) * val_split))
        val_parts.append(sub.iloc[:n_val])
        parts.append(sub.iloc[n_val:])
    train_df = pd.concat(parts).sample(frac=1.0, random_state=seed)
    val_df = pd.concat(val_parts).sample(frac=1.0, random_state=seed)
    return train_df, val_df


def build_dataset(df: pd.DataFrame, image_size: int, batch_size: int, training: bool) -> tf.data.Dataset:
    paths = df["path"].values
    labels = df["label"].values

    def _load(path, label):
        image = tf.io.read_file(path)
        image = tf.image.decode_image(image, channels=1, expand_animations=False)
        image = tf.image.resize(image, [image_size, image_size])
        image = tf.cast(image, tf.float32) / 255.0
        return image, tf.cast(label, tf.float32)

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        ds = ds.shuffle(buffer_size=len(df), seed=42, reshuffle_each_iteration=True)
    ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def build_model(image_size: int, learning_rate: float) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(image_size, image_size, 1))
    x = tf.keras.layers.RandomRotation(0.03)(inputs)
    x = tf.keras.layers.RandomZoom(0.1)(x)

    x = tf.keras.layers.Conv2D(32, 3, activation="relu")(x)
    x = tf.keras.layers.MaxPool2D()(x)
    x = tf.keras.layers.Conv2D(64, 3, activation="relu")(x)
    x = tf.keras.layers.MaxPool2D()(x)
    x = tf.keras.layers.Conv2D(128, 3, activation="relu")(x)
    x = tf.keras.layers.MaxPool2D()(x)

    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def best_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    thresholds = np.linspace(0.1, 0.9, 81)
    best_t = 0.5
    best_f1 = -1.0
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        tp = int(((y_pred == 1) & (y_true == 1)).sum())
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())
        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
    return best_t


def main() -> None:
    cfg = load_config()
    manifest_path = Path(cfg["manifest_path"])
    if not manifest_path.exists():
        raise SystemExit("Manifest not found. Run scripts/prepare_data.py first.")

    df = pd.read_csv(manifest_path)
    train_df, val_df = split_df(df, float(cfg["val_split"]), int(cfg["seed"]))

    train_ds = build_dataset(train_df, int(cfg["image_size"]), int(cfg["batch_size"]), True)
    val_ds = build_dataset(val_df, int(cfg["image_size"]), int(cfg["batch_size"]), False)

    model = build_model(int(cfg["image_size"]), float(cfg["learning_rate"]))
    model.fit(train_ds, validation_data=val_ds, epochs=int(cfg["epochs"]))

    y_prob = model.predict(val_ds, verbose=0).ravel()
    y_true = val_df["label"].values.astype(int)
    threshold = best_threshold(y_true, y_prob)

    model_path = Path(cfg["model_path"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)

    with open(cfg["threshold_path"], "w", encoding="utf-8") as f:
        json.dump({"threshold": threshold}, f, indent=2)

    with open(cfg["label_map_path"], "w", encoding="utf-8") as f:
        json.dump({"0": "forged", "1": "genuine"}, f, indent=2)

    print(f"Saved model to {model_path}")
    print(f"Best threshold: {threshold:.3f}")


if __name__ == "__main__":
    main()
