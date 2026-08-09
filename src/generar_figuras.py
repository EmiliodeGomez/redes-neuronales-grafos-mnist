"""Genera visualizaciones del analisis con Pillow, sin dependencias externas."""

from pathlib import Path
import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw" / "mnist.npz"
RESULTS = ROOT / "data" / "processed" / "resultados.json"
OUT = Path(os.environ.get("GNN_FIG_OUT", Path(os.environ["TEMP"]) / "gnn_figuras"))
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#16324F"
BLUE = "#2F80ED"
TEAL = "#13A89E"
ORANGE = "#F2994A"
GRAY = "#667085"
LIGHT = "#EEF4F8"
WHITE = "#FFFFFF"


def font(size, bold=False):
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf"),
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def base(title, subtitle="", size=(1600, 900)):
    im = Image.new("RGB", size, WHITE)
    d = ImageDraw.Draw(im)
    d.text((80, 55), title, fill=NAVY, font=font(52, True))
    if subtitle:
        d.text((82, 125), subtitle, fill=GRAY, font=font(25))
    d.line((80, 170, size[0] - 80, 170), fill="#D8E2EA", width=3)
    return im, d


def save(im, name):
    im.save(OUT / name, quality=95)


def samples_and_distribution(x, y):
    im, d = base("MNIST contiene trazos diversos dentro de cada clase", "Muestra estratificada del conjunto de entrenamiento; intensidades normalizadas a [0, 1].")
    for k in range(10):
        idx = int(np.flatnonzero(y == k)[0])
        digit = Image.fromarray(x[idx]).resize((105, 105), Image.Resampling.NEAREST).convert("RGB")
        digit = Image.eval(digit, lambda p: 255 - p)
        x0 = 100 + k * 145
        im.paste(digit, (x0, 230))
        d.text((x0 + 39, 350), str(k), fill=NAVY, font=font(32, True))
    counts = np.bincount(y, minlength=10)
    maxc = counts.max()
    chart_left, chart_top, chart_bottom = 130, 470, 800
    d.line((chart_left, chart_bottom, 1500, chart_bottom), fill=NAVY, width=3)
    for k, c in enumerate(counts):
        x0 = chart_left + 25 + k * 130
        h = int(245 * c / maxc)
        d.rounded_rectangle((x0, chart_bottom - h, x0 + 72, chart_bottom), radius=6, fill=TEAL)
        d.text((x0 + 14, chart_bottom + 12), str(k), fill=NAVY, font=font(23, True))
        d.text((x0 - 2, chart_bottom - h - 34), f"{c:,}", fill=GRAY, font=font(19))
    save(im, "figura_1_muestras_distribucion.png")


def mean_images(x, y):
    im, d = base("El patrón medio conserva la geometría básica de cada dígito", "Promedio por clase de 60,000 imágenes de entrenamiento.")
    for k in range(10):
        mean = x[y == k].mean(axis=0)
        arr = np.clip(mean * 255 / max(1e-9, mean.max()), 0, 255).astype(np.uint8)
        digit = Image.fromarray(arr).resize((180, 180), Image.Resampling.BILINEAR).convert("RGB")
        digit = Image.eval(digit, lambda p: 255 - p)
        row, col = divmod(k, 5)
        x0, y0 = 155 + col * 285, 220 + row * 300
        im.paste(digit, (x0, y0))
        d.text((x0 + 78, y0 + 195), str(k), fill=NAVY, font=font(30, True))
    save(im, "figura_2_promedios_clase.png")


def comparison(results):
    im, d = base("Graph-MLP supera al modelo lineal en todas las métricas", "Evaluación final sobre las mismas 10,000 imágenes de prueba.")
    metrics = [("Exactitud", "accuracy"), ("Precisión macro", "precision_macro"), ("Exhaustividad macro", "recall_macro"), ("F1 macro", "f1_macro")]
    left, top, width = 365, 245, 1035
    for i, (label, key) in enumerate(metrics):
        y0 = top + i * 135
        d.text((80, y0 + 20), label, fill=NAVY, font=font(24, True))
        for j, (name, color) in enumerate((("Softmax", BLUE), ("Graph-MLP", TEAL))):
            val = results["test_results"][name][key]
            bar_y = y0 + j * 43
            d.rounded_rectangle((left, bar_y, left + int(width * val), bar_y + 30), radius=8, fill=color)
            d.text((left + int(width * val) + 15, bar_y - 2), f"{val*100:.2f}%", fill=NAVY, font=font(22, True))
    d.rectangle((1120, 770, 1160, 790), fill=BLUE)
    d.text((1175, 765), "Softmax", fill=GRAY, font=font(21))
    d.rectangle((1320, 770, 1360, 790), fill=TEAL)
    d.text((1375, 765), "Graph-MLP", fill=GRAY, font=font(21))
    save(im, "figura_3_comparacion_metricas.png")


def heatmap(cm, title, name):
    cm = np.array(cm)
    norm = cm / cm.sum(axis=1, keepdims=True)
    im, d = base(title, "Filas: clase real. Columnas: clase predicha. Cada fila está normalizada.")
    x0, y0, cell = 390, 220, 58
    for r in range(10):
        d.text((x0 - 48, y0 + r * cell + 14), str(r), fill=NAVY, font=font(23, True))
        d.text((x0 + r * cell + 20, y0 - 42), str(r), fill=NAVY, font=font(23, True))
        for c in range(10):
            v = float(norm[r, c])
            color = (int(240 - 175 * v), int(247 - 105 * v), int(252 - 40 * v))
            d.rectangle((x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell - 2, y0 + (r + 1) * cell - 2), fill=color)
            if v >= 0.02:
                d.text((x0 + c * cell + 7, y0 + r * cell + 18), f"{v*100:.0f}", fill=WHITE if v > .55 else NAVY, font=font(17, True))
    d.text((1020, 310), "Lectura", fill=NAVY, font=font(30, True))
    errors = cm.copy(); np.fill_diagonal(errors, 0)
    pairs = np.dstack(np.unravel_index(np.argsort(errors.ravel())[::-1][:4], errors.shape))[0]
    for i, (r, c) in enumerate(pairs):
        d.text((1020, 380 + i * 70), f"{r} → {c}: {errors[r,c]} casos", fill=GRAY, font=font(24))
    save(im, name)


def sensitivity(rows):
    im, d = base("La cantidad de datos domina la sensibilidad del modelo", "F1 macro de Graph-MLP en validación; cambiar L2 casi no altera el resultado.")
    groups = {}
    for row in rows:
        groups.setdefault(row["assumption"], []).append(row)
    origins = [(110, 240), (570, 240), (1030, 240)]
    colors = [BLUE, TEAL, ORANGE]
    for (label, vals), (x0, y0), color in zip(groups.items(), origins, colors):
        d.text((x0, y0), label, fill=NAVY, font=font(26, True))
        chart_top, chart_bottom, chart_w = y0 + 80, 730, 360
        minv = min(v["f1_macro"] for v in vals) - .01
        maxv = max(v["f1_macro"] for v in vals) + .005
        pts = []
        for i, v in enumerate(vals):
            px = x0 + 25 + i * (chart_w - 50) / max(1, len(vals) - 1)
            py = chart_bottom - (v["f1_macro"] - minv) / max(1e-9, maxv - minv) * (chart_bottom - chart_top)
            pts.append((px, py))
            d.text((px - 28, chart_bottom + 18), str(v["value"]), fill=GRAY, font=font(18))
            d.text((px - 31, py - 38), f"{v['f1_macro']*100:.1f}%", fill=NAVY, font=font(18, True))
        if len(pts) > 1:
            d.line(pts, fill=color, width=6)
        for px, py in pts:
            d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=color)
    save(im, "figura_6_sensibilidad.png")


def training(history):
    im, d = base("El modelo con propagación converge con menor pérdida", "Pérdida de validación durante 12 épocas; misma muestra y semilla.")
    x0, y0, w, h = 160, 235, 1280, 500
    d.line((x0, y0 + h, x0 + w, y0 + h), fill=NAVY, width=3)
    d.line((x0, y0, x0, y0 + h), fill=NAVY, width=3)
    all_vals = history["Softmax"]["val_loss"] + history["Graph-MLP"]["val_loss"]
    vmax, vmin = max(all_vals) * 1.05, min(all_vals) * .9
    for name, color in (("Softmax", BLUE), ("Graph-MLP", TEAL)):
        vals = history[name]["val_loss"]
        pts = []
        for i, v in enumerate(vals):
            px = x0 + i * w / (len(vals) - 1)
            py = y0 + h - (v - vmin) / (vmax - vmin) * h
            pts.append((px, py))
        d.line(pts, fill=color, width=7)
        for px, py in pts:
            d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=color)
        d.text((pts[-1][0] - 120, pts[-1][1] - 35), f"{name}: {vals[-1]:.3f}", fill=color, font=font(22, True))
    for i in range(12):
        if i in (0, 2, 5, 8, 11):
            d.text((x0 + i * w / 11 - 8, y0 + h + 18), str(i + 1), fill=GRAY, font=font(18))
    d.text((720, 820), "Época", fill=GRAY, font=font(22))
    save(im, "figura_7_convergencia.png")


def main():
    data = np.load(DATA)
    x, y = data["x_train"], data["y_train"]
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    samples_and_distribution(x, y)
    mean_images(x.astype(np.float32) / 255.0, y)
    comparison(results)
    heatmap(results["test_results"]["Softmax"]["confusion_matrix"], "Softmax: confusiones principales", "figura_4_confusion_softmax.png")
    heatmap(results["test_results"]["Graph-MLP"]["confusion_matrix"], "Graph-MLP: menos errores", "figura_5_confusion_graph_mlp.png")
    sensitivity(results["sensitivity"])
    training(results["histories"])
    print(OUT)


if __name__ == "__main__":
    main()
