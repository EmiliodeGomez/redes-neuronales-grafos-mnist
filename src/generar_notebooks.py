"""Construye los tres notebooks reproducibles del repositorio."""

from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("GNN_NB_OUT", Path(os.environ["TEMP"]) / "gnn_notebooks"))
OUT.mkdir(parents=True, exist_ok=True)


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.splitlines(True)}


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SETUP = r'''from pathlib import Path
import sys, urllib.request
import numpy as np

SEED = 2026
rng = np.random.default_rng(SEED)

# Funciona desde notebooks/ en el repositorio y también en Colab.
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
DATA = ROOT / "data" / "raw" / "mnist.npz"
SRC = ROOT / "src"
if not SRC.exists():
    # Si se subió solo el notebook, crea una ruta local y descarga los datos.
    ROOT = Path.cwd()
    DATA = ROOT / "mnist.npz"
if not DATA.exists():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz", DATA
    )
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

data = np.load(DATA)
x_train = data["x_train"].astype(np.float32) / 255.0
y_train = data["y_train"].astype(np.int64)
x_test = data["x_test"].astype(np.float32) / 255.0
y_test = data["y_test"].astype(np.int64)
print("Semilla:", SEED, "| entrenamiento:", x_train.shape, "| prueba:", x_test.shape)'''


def main():
    nb1 = notebook([
        md("# 01 — Exploración de MNIST como grafo de píxeles\n\nObjetivo: documentar fuente, dimensiones, balance de clases, intensidades y estructura espacial antes de modelar."),
        code(SETUP),
        md("## Diccionario de variables\n\n| Variable | Tipo | Unidad | Descripción |\n|---|---|---|---|\n| `x_train`, `x_test` | uint8 → float32 | intensidad [0,1] | Imágenes 28×28 |\n| `y_train`, `y_test` | entero | clase 0–9 | Dígito real |"),
        code('''import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 5, figsize=(12, 5))
for k, ax in enumerate(axes.ravel()):
    idx = np.flatnonzero(y_train == k)[0]
    ax.imshow(x_train[idx], cmap="gray")
    ax.set_title(f"Clase {k}")
    ax.axis("off")
plt.suptitle("Una observación por clase")
plt.tight_layout(); plt.show()'''),
        code('''counts = np.bincount(y_train, minlength=10)
plt.figure(figsize=(9, 4))
plt.bar(range(10), counts, color="#13A89E")
plt.xticks(range(10)); plt.xlabel("Clase"); plt.ylabel("Observaciones")
plt.title("Distribución de clases en entrenamiento")
for k, c in enumerate(counts): plt.text(k, c + 50, f"{c:,}", ha="center", fontsize=8)
plt.show()
print("Razón mayor/menor:", counts.max()/counts.min())'''),
        code('''fig, axes = plt.subplots(2, 5, figsize=(12, 5))
for k, ax in enumerate(axes.ravel()):
    ax.imshow(x_train[y_train == k].mean(axis=0), cmap="viridis")
    ax.set_title(f"Promedio {k}"); ax.axis("off")
plt.suptitle("Imagen promedio por clase")
plt.tight_layout(); plt.show()'''),
        md("## Lectura\n\nLas clases son aproximadamente balanceadas (la clase mayor no duplica a la menor), por lo que se reporta exactitud junto con métricas macro. Los promedios conservan geometría local; por eso tiene sentido probar un modelo que utilice la vecindad de Moore entre píxeles."),
    ])

    nb2 = notebook([
        md("# 02 — Dos modelos: Softmax y Graph-MLP\n\nSe corrige el error del prototipo original: `einsum('nn,bnf->bnf')` tomaba solo la diagonal nula de A. La implementación reproducible usa sumas de vecinos y la ecuación `H(t+1)=(1−α)H(t)+αD⁻¹AH(t)`."),
        code(SETUP),
        code('''from modelado_mnist import (
    GraphMLP, SoftmaxRegression, graph_message_features, raw_features,
    stratified_indices, stratified_split, classification_metrics
)

raw_train, raw_test = raw_features(x_train), raw_features(x_test)
graph_train = graph_message_features(x_train, alpha=0.35, steps=2)
graph_test = graph_message_features(x_test, alpha=0.35, steps=2)
idx = stratified_indices(y_train, 30000, seed=SEED)
tr, va = stratified_split(y_train[idx], val_fraction=0.15, seed=SEED)
print(raw_train.shape, graph_train.shape)'''),
        md("## Modelo 1 — Regresión Softmax\n\n`P(y=k|x)=exp(w_kᵀx+b_k)/Σ_j exp(w_jᵀx+b_j)`. Es un límite inferior interpretable: separa clases mediante fronteras lineales."),
        code('''softmax = SoftmaxRegression(784, l2=1e-4, seed=SEED)
hist_softmax = softmax.fit(raw_train[idx][tr], y_train[idx][tr], raw_train[idx][va], y_train[idx][va], epochs=12, seed=SEED)
m_softmax = classification_metrics(y_test, softmax.predict_proba(raw_test))
{k: round(v, 4) for k, v in m_softmax.items() if k != "confusion_matrix"}'''),
        md("## Modelo 2 — Graph-MLP\n\nPrimero propaga intensidad por el grafo de 8 vecinos durante dos pasos; después aplica una capa ReLU de 64 unidades y una salida Softmax. Combina el supuesto de localidad espacial con una frontera no lineal."),
        code('''graph_mlp = GraphMLP(784, hidden=64, l2=1e-4, seed=SEED)
hist_graph = graph_mlp.fit(graph_train[idx][tr], y_train[idx][tr], graph_train[idx][va], y_train[idx][va], epochs=12, seed=SEED)
m_graph = classification_metrics(y_test, graph_mlp.predict_proba(graph_test))
{k: round(v, 4) for k, v in m_graph.items() if k != "confusion_matrix"}'''),
        code('''import matplotlib.pyplot as plt
plt.figure(figsize=(8,4))
plt.plot(hist_softmax.val_loss, marker="o", label="Softmax")
plt.plot(hist_graph.val_loss, marker="o", label="Graph-MLP")
plt.xlabel("Época"); plt.ylabel("Pérdida de validación"); plt.legend(); plt.grid(alpha=.2)
plt.title("Convergencia bajo la misma partición")
plt.show()'''),
        md("## Resultado esperado\n\nSoftmax: exactitud ≈ 0.923 y F1 macro ≈ 0.922. Graph-MLP: exactitud ≈ 0.956 y F1 macro ≈ 0.955. Pequeñas variaciones pueden aparecer por la implementación BLAS, pero la semilla y las particiones permanecen fijas."),
    ])

    nb3 = notebook([
        md("# 03 — Validación, comparación y sensibilidad\n\nValidación cruzada estratificada de tres pliegues sobre los mismos 12,000 ejemplos para ambos modelos. Luego se mueven L2, pasos de propagación y tamaño de entrenamiento."),
        code(SETUP),
        code('''from modelado_mnist import *
raw = raw_features(x_train)
graph = graph_message_features(x_train, alpha=0.35, steps=2)
idx = stratified_indices(y_train, 12000, seed=SEED)
y = y_train[idx]
rows = []
for fold, (tr, va) in enumerate(stratified_folds(y, 3, SEED), 1):
    for name, feats in (("Softmax", raw[idx]), ("Graph-MLP", graph[idx])):
        model = SoftmaxRegression(784, seed=SEED+fold) if name == "Softmax" else GraphMLP(784, seed=SEED+fold)
        model.fit(feats[tr], y[tr], feats[va], y[va], epochs=7, seed=SEED+fold)
        m = classification_metrics(y[va], model.predict_proba(feats[va]))
        rows.append((fold, name, m["accuracy"], m["f1_macro"], m["log_loss"]))
rows'''),
        code('''for name in ("Softmax", "Graph-MLP"):
    r = np.array([[a, f, l] for _, n, a, f, l in rows if n == name])
    print(name, "media [accuracy, F1, log-loss] =", r.mean(axis=0).round(4), "DE =", r.std(axis=0, ddof=1).round(4))'''),
        md("## Sensibilidad reproducida desde el experimento completo"),
        code('''import json
results_path = ROOT / "data" / "processed" / "resultados.json"
if results_path.exists():
    results = json.loads(results_path.read_text(encoding="utf-8"))
    for row in results["sensitivity"]:
        print(f"{row['assumption']:24s} {str(row['value']):>8s} | F1={row['f1_macro']:.4f}")
else:
    print("Ejecute src/ejecutar_experimentos.py para regenerar la tabla completa.")'''),
        md("## Interpretación\n\nEl resultado es estable ante L2 entre 0 y 10⁻⁴. Tres pasos reducen el F1 por sobre-suavizado: los nodos vecinos se vuelven demasiado parecidos. La conclusión es más sensible al tamaño de entrenamiento; con 5,000 ejemplos el F1 cae cerca de cuatro puntos. La ablation con cero pasos también revela que la no linealidad explica una parte mayor de la mejora que la propagación fija, por lo que no se atribuye toda la ganancia al grafo."),
    ])

    for name, nb in (("01_exploracion.ipynb", nb1), ("02_modelos.ipynb", nb2), ("03_validacion.ipynb", nb3)):
        (OUT / name).write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    # Copia integrada para quienes prefieren un solo archivo.
    combined = notebook(nb1["cells"] + [md("---\n# Continuación: modelos y validación")] + nb2["cells"][1:] + nb3["cells"][1:])
    (OUT / "RedNeuronal_Corregido.ipynb").write_text(json.dumps(combined, ensure_ascii=False, indent=1), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()

