"""Modelos reproducibles para clasificar MNIST con y sin estructura de grafo.

El modulo usa solo NumPy para que los notebooks corran en Google Colab sin
instalaciones pesadas. La semilla oficial del proyecto es 2026.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np


SEED = 2026
NUM_CLASSES = 10


def load_mnist(path: str | Path):
    data = np.load(Path(path))
    x_train = data["x_train"].astype(np.float32) / 255.0
    x_test = data["x_test"].astype(np.float32) / 255.0
    y_train = data["y_train"].astype(np.int64)
    y_test = data["y_test"].astype(np.int64)
    return x_train, y_train, x_test, y_test


def stratified_indices(y: np.ndarray, n: int, seed: int = SEED) -> np.ndarray:
    """Selecciona aproximadamente n observaciones preservando las 10 clases."""
    rng = np.random.default_rng(seed)
    per_class = n // NUM_CLASSES
    chunks = []
    for klass in range(NUM_CLASSES):
        candidates = np.flatnonzero(y == klass)
        rng.shuffle(candidates)
        chunks.append(candidates[:per_class])
    idx = np.concatenate(chunks)
    rng.shuffle(idx)
    return idx


def stratified_split(y: np.ndarray, val_fraction: float = 0.15, seed: int = SEED):
    rng = np.random.default_rng(seed)
    train_idx, val_idx = [], []
    for klass in range(NUM_CLASSES):
        candidates = np.flatnonzero(y == klass)
        rng.shuffle(candidates)
        cut = max(1, int(round(len(candidates) * val_fraction)))
        val_idx.append(candidates[:cut])
        train_idx.append(candidates[cut:])
    train_idx = np.concatenate(train_idx)
    val_idx = np.concatenate(val_idx)
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return train_idx, val_idx


def stratified_folds(y: np.ndarray, k: int = 3, seed: int = SEED):
    rng = np.random.default_rng(seed)
    class_parts = {}
    for klass in range(NUM_CLASSES):
        idx = np.flatnonzero(y == klass)
        rng.shuffle(idx)
        class_parts[klass] = np.array_split(idx, k)
    all_idx = np.arange(len(y))
    for fold in range(k):
        val = np.concatenate([class_parts[c][fold] for c in range(NUM_CLASSES)])
        mask = np.ones(len(y), dtype=bool)
        mask[val] = False
        train = all_idx[mask]
        rng.shuffle(train)
        rng.shuffle(val)
        yield train, val


def graph_message_features(images: np.ndarray, alpha: float = 0.35, steps: int = 2):
    """Propaga intensidad en el grafo Moore de 8 vecinos.

    H^(t+1) = (1-alpha) H^(t) + alpha D^-1 A H^(t).
    La implementacion evita construir A de 784x784 y suma vecinos por desplazamiento.
    """
    h = images.astype(np.float32, copy=True)
    degree = np.full((28, 28), 8.0, dtype=np.float32)
    degree[0, :] -= 3
    degree[-1, :] -= 3
    degree[:, 0] -= 3
    degree[:, -1] -= 3
    degree[0, 0] = degree[0, -1] = degree[-1, 0] = degree[-1, -1] = 3
    for _ in range(steps):
        p = np.pad(h, ((0, 0), (1, 1), (1, 1)), mode="constant")
        agg = np.zeros_like(h)
        for dr in range(3):
            for dc in range(3):
                if dr == 1 and dc == 1:
                    continue
                agg += p[:, dr:dr + 28, dc:dc + 28]
        mean = agg / degree[None, :, :]
        h = (1.0 - alpha) * h + alpha * mean
    return h.reshape(len(h), -1)


def raw_features(images: np.ndarray):
    return images.reshape(len(images), -1).astype(np.float32)


def one_hot(y: np.ndarray):
    out = np.zeros((len(y), NUM_CLASSES), dtype=np.float32)
    out[np.arange(len(y)), y] = 1.0
    return out


def softmax(logits: np.ndarray):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


@dataclass
class TrainingHistory:
    train_loss: list[float]
    val_loss: list[float]
    val_accuracy: list[float]


class Adam:
    def __init__(self, params, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr, self.beta1, self.beta2, self.eps = lr, beta1, beta2, eps
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0

    def step(self, params, grads):
        self.t += 1
        for i, (p, g) in enumerate(zip(params, grads)):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * g
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (g * g)
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)
            p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class SoftmaxRegression:
    def __init__(self, n_features: int, l2: float = 1e-4, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.W = rng.normal(0, 0.01, (n_features, NUM_CLASSES)).astype(np.float32)
        self.b = np.zeros(NUM_CLASSES, dtype=np.float32)
        self.l2 = l2

    @property
    def params(self):
        return [self.W, self.b]

    def predict_proba(self, x):
        return softmax(x @ self.W + self.b)

    def fit(self, x, y, x_val, y_val, epochs=12, batch_size=256, lr=2e-3, seed=SEED):
        rng = np.random.default_rng(seed)
        opt = Adam(self.params, lr=lr)
        hist = TrainingHistory([], [], [])
        target = one_hot(y)
        for _ in range(epochs):
            order = rng.permutation(len(x))
            for start in range(0, len(x), batch_size):
                idx = order[start:start + batch_size]
                xb, yb = x[idx], target[idx]
                probs = self.predict_proba(xb)
                dz = (probs - yb) / len(xb)
                grads = [xb.T @ dz + self.l2 * self.W, dz.sum(axis=0)]
                opt.step(self.params, grads)
            hist.train_loss.append(log_loss(y, self.predict_proba(x)) + 0.5 * self.l2 * float((self.W ** 2).sum()))
            val_p = self.predict_proba(x_val)
            hist.val_loss.append(log_loss(y_val, val_p))
            hist.val_accuracy.append(float((val_p.argmax(1) == y_val).mean()))
        return hist


class GraphMLP:
    def __init__(self, n_features: int, hidden: int = 64, l2: float = 1e-4, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.W1 = (rng.normal(0, np.sqrt(2 / n_features), (n_features, hidden))).astype(np.float32)
        self.b1 = np.zeros(hidden, dtype=np.float32)
        self.W2 = (rng.normal(0, np.sqrt(2 / hidden), (hidden, NUM_CLASSES))).astype(np.float32)
        self.b2 = np.zeros(NUM_CLASSES, dtype=np.float32)
        self.l2 = l2

    @property
    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]

    def forward(self, x):
        z1 = x @ self.W1 + self.b1
        h = np.maximum(z1, 0)
        return z1, h, softmax(h @ self.W2 + self.b2)

    def predict_proba(self, x):
        return self.forward(x)[2]

    def fit(self, x, y, x_val, y_val, epochs=12, batch_size=256, lr=1e-3, seed=SEED):
        rng = np.random.default_rng(seed)
        opt = Adam(self.params, lr=lr)
        hist = TrainingHistory([], [], [])
        target = one_hot(y)
        for _ in range(epochs):
            order = rng.permutation(len(x))
            for start in range(0, len(x), batch_size):
                idx = order[start:start + batch_size]
                xb, yb = x[idx], target[idx]
                z1, h, probs = self.forward(xb)
                dz2 = (probs - yb) / len(xb)
                dW2 = h.T @ dz2 + self.l2 * self.W2
                db2 = dz2.sum(axis=0)
                dh = dz2 @ self.W2.T
                dz1 = dh * (z1 > 0)
                dW1 = xb.T @ dz1 + self.l2 * self.W1
                db1 = dz1.sum(axis=0)
                opt.step(self.params, [dW1, db1, dW2, db2])
            train_p = self.predict_proba(x)
            hist.train_loss.append(log_loss(y, train_p) + 0.5 * self.l2 * float((self.W1 ** 2).sum() + (self.W2 ** 2).sum()))
            val_p = self.predict_proba(x_val)
            hist.val_loss.append(log_loss(y_val, val_p))
            hist.val_accuracy.append(float((val_p.argmax(1) == y_val).mean()))
        return hist


def log_loss(y: np.ndarray, probs: np.ndarray):
    return float(-np.log(np.clip(probs[np.arange(len(y)), y], 1e-8, 1)).mean())


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray):
    cm = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    return cm


def classification_metrics(y_true: np.ndarray, probs: np.ndarray):
    pred = probs.argmax(axis=1)
    cm = confusion_matrix(y_true, pred)
    precision, recall, f1 = [], [], []
    for k in range(NUM_CLASSES):
        tp = cm[k, k]
        fp = cm[:, k].sum() - tp
        fn = cm[k, :].sum() - tp
        p = tp / max(1, tp + fp)
        r = tp / max(1, tp + fn)
        precision.append(p)
        recall.append(r)
        f1.append(2 * p * r / max(1e-12, p + r))
    return {
        "accuracy": float((pred == y_true).mean()),
        "precision_macro": float(np.mean(precision)),
        "recall_macro": float(np.mean(recall)),
        "f1_macro": float(np.mean(f1)),
        "log_loss": log_loss(y_true, probs),
        "confusion_matrix": cm.tolist(),
    }


def save_json(path: str | Path, obj):
    payload = json.dumps(obj, indent=2, ensure_ascii=False)
    try:
        Path(path).write_text(payload, encoding="utf-8")
    except PermissionError:
        # Algunos entornos administrados permiten a Python escribir solo en TEMP.
        import tempfile
        fallback = Path(tempfile.gettempdir()) / Path(path).name
        fallback.write_text(payload, encoding="utf-8")
        print("RESULTS_FALLBACK:", fallback)
