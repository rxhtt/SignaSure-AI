from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import tensorflow as tf
import yaml
from PIL import Image


@dataclass
class ModelConfig:
    image_size: int
    model_path: Path
    threshold_path: Path
    label_map_path: Path


def load_config() -> ModelConfig:
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    model_path = Path(os.getenv("MODEL_PATH", raw["model_path"]))
    threshold_path = Path(os.getenv("THRESHOLD_PATH", raw["threshold_path"]))
    label_map_path = Path(os.getenv("LABEL_MAP_PATH", raw["label_map_path"]))

    return ModelConfig(
        image_size=int(raw["image_size"]),
        model_path=model_path,
        threshold_path=threshold_path,
        label_map_path=label_map_path,
    )


class SignatureModel:
    def __init__(self, cfg: ModelConfig) -> None:
        self.cfg = cfg
        self.model: tf.keras.Model | None = None
        self.threshold: float = 0.5
        self.label_map = {0: "forged", 1: "genuine"}

    def load(self) -> None:
        if self.model is not None:
            return

        if not self.cfg.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {self.cfg.model_path}. Train the model first."
            )

        self.model = tf.keras.models.load_model(self.cfg.model_path)

        if self.cfg.threshold_path.exists():
            with open(self.cfg.threshold_path, "r", encoding="utf-8") as f:
                self.threshold = float(json.load(f).get("threshold", 0.5))

        if self.cfg.label_map_path.exists():
            with open(self.cfg.label_map_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.label_map = {int(k): v for k, v in raw.items()}

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        image = image.resize((self.cfg.image_size, self.cfg.image_size))
        arr = np.asarray(image, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=-1)
        arr = np.expand_dims(arr, axis=0)
        return arr

    def _compute_signals(self, gray: np.ndarray) -> Dict[str, float]:
        # gray: HxW float32 in [0,1]
        ink_mask = gray < 0.5
        ink_ratio = float(ink_mask.mean())

        if ink_mask.any():
            ys, xs = np.where(ink_mask)
            y0, y1 = ys.min(), ys.max()
            x0, x1 = xs.min(), xs.max()
            bbox_h = max(1, int(y1 - y0 + 1))
            bbox_w = max(1, int(x1 - x0 + 1))
            bbox_area = float(bbox_h * bbox_w)
            bbox_coverage = float(ink_mask.sum() / bbox_area)
            aspect_ratio = float(bbox_w / bbox_h)
        else:
            bbox_coverage = 0.0
            aspect_ratio = 1.0

        # Simple Sobel edges
        kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

        pad = np.pad(gray, 1, mode="reflect")
        gx = np.zeros_like(gray)
        gy = np.zeros_like(gray)
        for i in range(gray.shape[0]):
            for j in range(gray.shape[1]):
                region = pad[i : i + 3, j : j + 3]
                gx[i, j] = np.sum(region * kx)
                gy[i, j] = np.sum(region * ky)
        edge_mag = np.sqrt(gx ** 2 + gy ** 2)
        edge_strength = float(edge_mag.mean())
        edge_density = float((edge_mag > 0.2).mean())
        stroke_consistency = float(ink_ratio / (edge_density + 1e-6))

        return {
            "ink_ratio": round(ink_ratio, 4),
            "bbox_coverage": round(bbox_coverage, 4),
            "aspect_ratio": round(aspect_ratio, 4),
            "edge_strength": round(edge_strength, 4),
            "edge_density": round(edge_density, 4),
            "stroke_consistency": round(stroke_consistency, 4),
        }

    def _explain(self, score: float, threshold: float, signals: Dict[str, float]) -> Tuple[str, list]:
        rationale = []
        if abs(score - threshold) < 0.08:
            rationale.append("Borderline score near the decision threshold; manual review recommended.")
        if signals["ink_ratio"] < 0.02:
            rationale.append("Very low ink density indicates faint or incomplete strokes.")
        if signals["edge_strength"] < 0.05:
            rationale.append("Low edge strength suggests blurred or shaky stroke boundaries.")
        if signals["bbox_coverage"] < 0.1:
            rationale.append("Signature occupies a small portion of its bounding box, indicating low stroke coverage.")

        if not rationale:
            rationale.append("Signature exhibits typical stroke density, edge definition, and spatial coverage.")

        detail = (
            "The model analyzes stroke continuity, edge sharpness, spatial proportions, "
            "and texture patterns learned from genuine and forged samples."
        )
        return detail, rationale

    def predict(self, image_bytes: bytes) -> Tuple[str, float, Dict[str, float], str, list]:
        self.load()
        assert self.model is not None
        x = self.preprocess(image_bytes)
        prob = float(self.model.predict(x, verbose=0)[0][0])
        gray = x[0, :, :, 0]
        signals = self._compute_signals(gray)
        label = self.label_map[1] if prob >= self.threshold else self.label_map[0]
        detail, rationale = self._explain(prob, self.threshold, signals)
        return label, prob, signals, detail, rationale


_model: SignatureModel | None = None


def get_model() -> SignatureModel:
    global _model
    if _model is None:
        cfg = load_config()
        _model = SignatureModel(cfg)
    return _model
