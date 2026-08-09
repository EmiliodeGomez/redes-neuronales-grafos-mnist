"""Ejecuta validacion, ajuste final y sensibilidad; guarda resultados JSON."""

from __future__ import annotations

from pathlib import Path
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from modelado_mnist import (
    SEED, GraphMLP, SoftmaxRegression, classification_metrics,
    graph_message_features, load_mnist, raw_features, save_json,
    stratified_folds, stratified_indices, stratified_split,
)


DATA = ROOT / "data" / "raw" / "mnist.npz"
RESULTS = ROOT / "data" / "processed" / "resultados.json"


def mean_std(rows, key):
    vals = np.array([r[key] for r in rows], dtype=float)
    return {"mean": float(vals.mean()), "std": float(vals.std(ddof=1))}


def fit_model(name, x_train, y_train, x_val, y_val, *, l2=1e-4, seed=SEED, epochs=9):
    if name == "Softmax":
        model = SoftmaxRegression(x_train.shape[1], l2=l2, seed=seed)
        history = model.fit(x_train, y_train, x_val, y_val, epochs=epochs, lr=2e-3, seed=seed)
    else:
        model = GraphMLP(x_train.shape[1], hidden=64, l2=l2, seed=seed)
        history = model.fit(x_train, y_train, x_val, y_val, epochs=epochs, lr=1e-3, seed=seed)
    return model, history


def main():
    started = time.time()
    x_train_img, y_train, x_test_img, y_test = load_mnist(DATA)
    raw_train = raw_features(x_train_img)
    raw_test = raw_features(x_test_img)
    graph_train = graph_message_features(x_train_img, alpha=0.35, steps=2)
    graph_test = graph_message_features(x_test_img, alpha=0.35, steps=2)

    # Validacion cruzada estratificada de 3 pliegues sobre una muestra balanceada.
    cv_idx = stratified_indices(y_train, 12000, seed=SEED)
    cv_y = y_train[cv_idx]
    cv_results = {"Softmax": [], "Graph-MLP": []}
    for fold, (tr, va) in enumerate(stratified_folds(cv_y, k=3, seed=SEED), start=1):
        for name, full_x in (("Softmax", raw_train), ("Graph-MLP", graph_train)):
            x = full_x[cv_idx]
            model, _ = fit_model(name, x[tr], cv_y[tr], x[va], cv_y[va], seed=SEED + fold, epochs=7)
            metrics = classification_metrics(cv_y[va], model.predict_proba(x[va]))
            metrics.pop("confusion_matrix")
            metrics["fold"] = fold
            cv_results[name].append(metrics)
            print(name, "fold", fold, metrics)

    cv_summary = {}
    for name, rows in cv_results.items():
        cv_summary[name] = {key: mean_std(rows, key) for key in (
            "accuracy", "precision_macro", "recall_macro", "f1_macro", "log_loss"
        )}

    # Ajuste final: misma muestra estratificada y misma validacion para ambos modelos.
    final_idx = stratified_indices(y_train, 30000, seed=SEED)
    final_y = y_train[final_idx]
    tr, va = stratified_split(final_y, val_fraction=0.15, seed=SEED)
    test_results, histories = {}, {}
    final_models = {}
    for name, full_train, full_test in (
        ("Softmax", raw_train, raw_test),
        ("Graph-MLP", graph_train, graph_test),
    ):
        x = full_train[final_idx]
        model, history = fit_model(name, x[tr], final_y[tr], x[va], final_y[va], seed=SEED, epochs=12)
        test_results[name] = classification_metrics(y_test, model.predict_proba(full_test))
        histories[name] = {
            "train_loss": history.train_loss,
            "val_loss": history.val_loss,
            "val_accuracy": history.val_accuracy,
        }
        final_models[name] = model
        print(name, "test", test_results[name])

    # Sensibilidad del Graph-MLP: regularizacion, pasos de propagacion y tamano muestral.
    sensitivity = []
    sens_train_idx = stratified_indices(y_train, 15000, seed=SEED)
    sens_y = y_train[sens_train_idx]
    strn, sva = stratified_split(sens_y, val_fraction=0.2, seed=SEED)
    for l2 in (0.0, 1e-4, 1e-3):
        gx = graph_train[sens_train_idx]
        model, _ = fit_model("Graph-MLP", gx[strn], sens_y[strn], gx[sva], sens_y[sva], l2=l2, seed=SEED, epochs=7)
        m = classification_metrics(sens_y[sva], model.predict_proba(gx[sva]))
        sensitivity.append({"assumption": "Regularizacion L2", "value": l2, "f1_macro": m["f1_macro"], "accuracy": m["accuracy"]})
    for steps in (0, 1, 2, 3):
        gx_all = raw_train if steps == 0 else graph_message_features(x_train_img, alpha=0.35, steps=steps)
        gx = gx_all[sens_train_idx]
        model, _ = fit_model("Graph-MLP", gx[strn], sens_y[strn], gx[sva], sens_y[sva], seed=SEED, epochs=7)
        m = classification_metrics(sens_y[sva], model.predict_proba(gx[sva]))
        sensitivity.append({"assumption": "Pasos de propagacion", "value": steps, "f1_macro": m["f1_macro"], "accuracy": m["accuracy"]})
    for size in (5000, 10000, 15000):
        idx = stratified_indices(sens_y, size, seed=SEED)
        gx = graph_train[sens_train_idx]
        local_tr, local_va = stratified_split(sens_y[idx], val_fraction=0.2, seed=SEED)
        model, _ = fit_model("Graph-MLP", gx[idx][local_tr], sens_y[idx][local_tr], gx[idx][local_va], sens_y[idx][local_va], seed=SEED, epochs=7)
        m = classification_metrics(sens_y[idx][local_va], model.predict_proba(gx[idx][local_va]))
        sensitivity.append({"assumption": "Tamano de entrenamiento", "value": size, "f1_macro": m["f1_macro"], "accuracy": m["accuracy"]})

    payload = {
        "seed": SEED,
        "dataset": {"train": 60000, "test": 10000, "image_shape": [28, 28], "classes": 10},
        "partitions": {"cv_sample": 12000, "cv_folds": 3, "final_train_sample": 30000, "final_validation_fraction": 0.15},
        "cv_folds": cv_results,
        "cv_summary": cv_summary,
        "test_results": test_results,
        "histories": histories,
        "sensitivity": sensitivity,
        "runtime_seconds": float(time.time() - started),
    }
    save_json(RESULTS, payload)
    print("Guardado:", RESULTS)


if __name__ == "__main__":
    main()

