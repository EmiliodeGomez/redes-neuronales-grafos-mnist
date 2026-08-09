"""Genera el informe final de 15 páginas y lo guarda primero en TEMP."""

from pathlib import Path
import json
import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Image, KeepInFrame, PageBreak, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figuras"
RESULTS = json.loads((ROOT / "data" / "processed" / "resultados.json").read_text(encoding="utf-8"))
OUT = Path(os.environ.get("GNN_REPORT_OUT", Path(os.environ["TEMP"]) / "EntregaFinal_Grupo_RedesNeuronalesGrafos.pdf"))
REPO_URL = os.environ.get("GNN_REPO_URL", "https://github.com/EmiliodeGomez/redes-neuronales-grafos-mnist")

FONT_DIR = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))

NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#2F80ED")
TEAL = colors.HexColor("#13A89E")
LIGHT = colors.HexColor("#EEF4F8")
GRAY = colors.HexColor("#667085")
RULE = colors.HexColor("#D8E2EA")
PAGE_W, PAGE_H = A4

styles = getSampleStyleSheet()
BODY = ParagraphStyle("body", fontName="Arial", fontSize=9.4, leading=13, textColor=NAVY, alignment=TA_JUSTIFY, spaceAfter=7)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, leading=10.2, spaceAfter=4)
H1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=19, leading=23, textColor=NAVY, spaceAfter=10)
H2 = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=12.5, leading=15, textColor=TEAL, spaceBefore=4, spaceAfter=6)
CALLOUT = ParagraphStyle("callout", parent=BODY, fontName="Arial-Bold", fontSize=9.5, leading=12, textColor=colors.white, alignment=TA_LEFT)
CAPTION = ParagraphStyle("caption", parent=SMALL, fontSize=7.5, leading=9, textColor=GRAY, alignment=TA_LEFT)
REF = ParagraphStyle("ref", parent=SMALL, fontSize=7.4, leading=9.5, leftIndent=12, firstLineIndent=-12, spaceAfter=4)
LEFT = ParagraphStyle("left", parent=BODY, alignment=TA_LEFT)


def P(text, style=BODY):
    return Paragraph(text, style)


def table(data, widths, header=True, font_size=7.6):
    cell = ParagraphStyle("cell", fontName="Arial", fontSize=font_size, leading=font_size+2.2, textColor=NAVY)
    cell_head = ParagraphStyle("cell_head", parent=cell, fontName="Arial-Bold", textColor=colors.white)
    wrapped = []
    for r, row in enumerate(data):
        wrapped.append([Paragraph(str(value), cell_head if header and r == 0 else cell) for value in row])
    t = Table(wrapped, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, RULE),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold")]
    t.setStyle(TableStyle(commands))
    return t


def img(name, width=17.1*cm, height=9.6*cm):
    return Image(str(FIG / name), width=width, height=height)


def header_footer(c, page_no, section):
    if page_no == 1:
        return
    c.setStrokeColor(RULE); c.setLineWidth(0.7)
    c.line(1.7*cm, PAGE_H-1.35*cm, PAGE_W-1.7*cm, PAGE_H-1.35*cm)
    c.setFont("Arial", 7.5); c.setFillColor(GRAY)
    c.drawString(1.7*cm, PAGE_H-1.05*cm, "BCD5105 Modelado matemático · Proyecto integrador")
    c.drawRightString(PAGE_W-1.7*cm, PAGE_H-1.05*cm, section)
    c.line(1.7*cm, 1.25*cm, PAGE_W-1.7*cm, 1.25*cm)
    c.drawString(1.7*cm, .85*cm, "Redes neuronales sobre grafos · II Cuatrimestre 2026")
    c.drawRightString(PAGE_W-1.7*cm, .85*cm, str(page_no))


def add_page(c, page_no, section, title, story, callout=None):
    header_footer(c, page_no, section)
    top = PAGE_H - 1.75*cm
    y_shift = 0
    if callout:
        c.setFillColor(TEAL)
        c.roundRect(1.7*cm, top-2.05*cm, PAGE_W-3.4*cm, 1.5*cm, 8, fill=1, stroke=0)
        f = Frame(2.05*cm, top-1.92*cm, PAGE_W-4.1*cm, 1.25*cm, showBoundary=0,
                  topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
        f.addFromList([KeepInFrame(f._width, f._height, [P(callout, CALLOUT)], mode="shrink")], c)
        y_shift = 1.8*cm
    frame = Frame(1.7*cm, 1.45*cm, PAGE_W-3.4*cm, PAGE_H-3.35*cm-y_shift, topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    content = [P(title, H1)] + story
    kif = KeepInFrame(frame._width, frame._height, content, mode="shrink")
    frame.addFromList([kif], c)
    c.showPage()


def main():
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Entrega final - Redes neuronales sobre grafos para MNIST")
    # 1. Portada
    c.setFillColor(NAVY); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(TEAL); c.rect(0, PAGE_H-1.1*cm, PAGE_W, 1.1*cm, fill=1, stroke=0)
    c.setFont("Arial-Bold", 30); c.setFillColor(colors.white)
    c.drawString(2.0*cm, PAGE_H-5.0*cm, "Redes neuronales sobre grafos")
    c.setFont("Arial-Bold", 22); c.drawString(2.0*cm, PAGE_H-6.25*cm, "para clasificar dígitos manuscritos")
    c.setFont("Arial", 13); c.setFillColor(colors.HexColor("#CFEAF0"))
    c.drawString(2.0*cm, PAGE_H-7.25*cm, "Comparación entre Softmax y Graph-MLP sobre MNIST")
    c.setStrokeColor(TEAL); c.setLineWidth(5); c.line(2*cm, PAGE_H-8.0*cm, 15.7*cm, PAGE_H-8.0*cm)
    y = PAGE_H-11.0*cm
    c.setFont("Arial-Bold", 11); c.setFillColor(colors.white)
    c.drawString(2*cm, y, "Integrantes")
    c.setFont("Arial", 10.5)
    for i, name in enumerate(["Diego Díaz", "Bairon Horna", "Ignacio Marín", "Jordan López", "Aaron Medrano", "Emilio de Gomez"]):
        c.drawString(2*cm, y-(i+1)*.50*cm, name)
    c.setFont("Arial-Bold", 11); c.drawString(11.2*cm, y, "Curso")
    c.setFont("Arial", 10.5)
    c.drawString(11.2*cm, y-.55*cm, "BCD5105 Modelado matemático")
    c.drawString(11.2*cm, y-1.1*cm, "Profesor: Jordy Alfaro Brenes")
    c.drawString(11.2*cm, y-1.65*cm, "Lead University")
    c.drawString(11.2*cm, y-2.2*cm, "19 de agosto de 2026")
    c.setFillColor(colors.HexColor("#CFEAF0")); c.setFont("Arial", 8.5)
    c.drawString(2*cm, 2.3*cm, "Carril temático: grafos y aprendizaje automático")
    c.drawString(2*cm, 1.75*cm, f"Repositorio: {REPO_URL}")
    c.showPage()

    # 2. Resumen y mejoras
    improvements = [
        ["Hallazgo en Avance 1", "Corrección incorporada"],
        ["Título de grafos, pero resumen sobre finanzas", "Problema, datos, modelos y conclusiones ahora se concentran en MNIST como grafo de píxeles."],
        ["Graph-RNN quedaba cerca del azar", "Se corrigió la contracción einsum: la versión anterior tomaba la diagonal nula de A. Se usa agregación D^-1 A H verificable."],
        ["Comparación informal de modelos", "Dos modelos, mismos pliegues y prueba; cinco métricas y tabla cuantitativa."],
        ["Sin sensibilidad ni ética específica", "Se mueven L2, pasos de propagación y tamaño; se documentan licencia, sesgo, privacidad y uso indebido."],
        ["Notebook aislado", "Repositorio con README, licencia, datos, tres notebooks, funciones y resultados persistidos."],
    ]
    add_page(c, 2, "Resumen", "Resumen ejecutivo y mejoras respecto al Avance 1", [
        P("<b>Resumen.</b> Este estudio evalúa si la estructura espacial de una imagen puede incorporarse explícitamente a un clasificador de dígitos. Cada imagen MNIST se representa como un grafo de 784 nodos, con aristas entre los ocho píxeles vecinos. Se comparan una regresión Softmax lineal y Graph-MLP, que aplica dos pasos de propagación fija y un clasificador neuronal no lineal. La validación cruzada estratificada de tres pliegues produjo F1 macro de 89.02% ± 0.22 para Softmax y 91.32% ± 0.39 para Graph-MLP. En la prueba oficial de 10,000 imágenes, los F1 fueron 92.19% y 95.51%. La sensibilidad indica estabilidad frente a regularización, sobre-suavizado con demasiados pasos y dependencia del tamaño muestral. Se recomienda validar con escritura costarricense antes de cualquier uso real."),
        P("<b>Palabras clave:</b> redes neuronales sobre grafos, MNIST, propagación de mensajes, clasificación multiclase, sensibilidad, reproducibilidad."),
        Spacer(1, 4), table(improvements, [5.3*cm, 11.3*cm], font_size=7.3),
    ], "La corrección del flujo de mensajes convierte un prototipo no funcional en una comparación reproducible y honesta." )

    # 3. Introducción y objetivos
    add_page(c, 3, "Introducción", "1. Problema, relevancia y objetivos", [
        P("La digitalización de formularios, archivos educativos, solicitudes y registros escritos puede reducir transcripción manual, pero exige reconocer trazos variables con errores controlados. En Costa Rica, un clasificador de caracteres podría apoyar tareas administrativas en instituciones públicas, centros educativos y entidades financieras; sin embargo, MNIST es únicamente una prueba de concepto internacional y no evidencia desempeño sobre escritura local."),
        P("Una imagen no es solo una lista de 784 intensidades: los píxeles adyacentes forman trazos. Las redes sobre grafos modelan explícitamente relaciones entre nodos [2–4]. El problema de investigación es: <i>¿un modelo que incorpora la vecindad local, combinado con una frontera no lineal, mejora la clasificación frente a un modelo lineal bajo una evaluación común?</i>"),
        P("<b>Objetivo general.</b> Evaluar matemáticamente y de forma reproducible el efecto de incorporar propagación local sobre un grafo de píxeles en la clasificación multiclase de MNIST."),
        P("<b>Objetivos específicos.</b> (1) describir MNIST y justificar su representación como grafo; (2) formular y ajustar dos modelos con supuestos diferentes; (3) comparar ambos con validación estratificada y métricas macro; (4) medir sensibilidad a regularización, profundidad de propagación y cantidad de datos; y (5) proponer salvaguardas para un eventual piloto costarricense."),
        P("La contribución es pedagógica: conecta álgebra matricial, funciones de activación, optimización y teoría de grafos con un experimento que puede ejecutarse sin GPU. No se afirma que Graph-MLP sea una GNN de frontera ni que MNIST represente el contexto nacional."),
        P("La relevancia del análisis no depende de que el modelo más complejo gane. Depende de que la comparación se realice sobre los mismos datos, que sus supuestos sean explícitos y que una conclusión adversa también pueda reportarse. Esa trazabilidad es central para el modelado matemático responsable [11–12]."),
    ])

    # 4. Teoría Softmax
    add_page(c, 4, "Marco teórico", "2.1. Modelo lineal, Softmax y aprendizaje", [
        P("Sea x∈R⁷⁸⁴ el vector de intensidades y y∈{0,…,9}. La regresión multiclase calcula un puntaje zₖ=wₖᵀx+bₖ para cada clase. La función Softmax transforma puntajes en probabilidades: p(y=k|x)=exp(zₖ)/Σⱼexp(zⱼ). Las probabilidades son no negativas y suman uno [5–6]."),
        P("El ajuste minimiza entropía cruzada regularizada: L(W,b)=−(1/n)Σᵢ log p(yᵢ|xᵢ)+(λ/2)||W||². El gradiente de un ejemplo respecto a z es p−e_y, donde e_y es el vector one-hot. Adam actualiza parámetros mediante promedios móviles del gradiente y su cuadrado."),
        P("<b>Supuestos.</b> La frontera entre clases es lineal en el espacio de píxeles; las observaciones son independientes; las etiquetas son correctas; y entrenamiento y prueba provienen de una distribución comparable. El modelo no utiliza vecindad, invariancia espacial ni interacción no lineal."),
        table([
            ["Símbolo", "Significado", "Dimensión/unidad"],
            ["xᵢ", "Intensidad normalizada de la imagen i", "784; sin unidad, [0,1]"],
            ["W, b", "Pesos y sesgos aprendidos", "784×10 y 10"],
            ["pᵢ", "Probabilidades predichas", "10; suma 1"],
            ["λ", "Penalización L2", "0, 10⁻⁴ o 10⁻³"],
            ["L", "Entropía cruzada promedio", "nats por observación"],
        ], [2.2*cm, 9.7*cm, 4.7*cm]),
        P("Softmax es adecuado como referencia porque ofrece un límite inferior fuerte, rápido y transparente. Si el segundo modelo no supera esta base sobre los mismos datos, la complejidad adicional no se justificaría. La exactitud no se usa sola: se añaden precisión, exhaustividad y F1 macro para tratar cada dígito con el mismo peso."),
    ])

    # 5. Teoría Graph
    add_page(c, 5, "Marco teórico", "2.2. Propagación de mensajes y Graph-MLP", [
        P("Cada imagen se representa como G=(V,E): V contiene 784 píxeles y E conecta vecinos horizontales, verticales y diagonales. A es la matriz de adyacencia y D la matriz diagonal de grados. La agregación normalizada es M = D^-1 A H; un nodo interior promedia ocho vecinos y uno de esquina, tres."),
        P("La recurrencia utilizada es H(t+1) = (1-alpha)H(t) + alpha D^-1 A H(t), con H(0)=x, alpha=0.35 y T=2. Después se aplana H(T) y se aplica h=ReLU(H(T)W1+b1), seguido de Softmax(hW2+b2). ReLU(u)=max(0,u) introduce fronteras no lineales."),
        P("Esta construcción es un clasificador con propagación de mensajes fija y lectura neuronal. Comparte la idea central de las GNN: actualizar cada nodo con información de su vecindad [2–4], pero no aprende pesos distintos por arista ni realiza atención. En una rejilla regular se relaciona con convoluciones locales [1,7]."),
        P("<b>Supuestos.</b> Los ocho vecinos son igualmente informativos; la continuidad local ayuda a recuperar trazos; dos pasos capturan contexto suficiente; el orden de nodos se conserva en la lectura; y una capa oculta de 64 unidades es adecuada. Un T grande puede producir <i>over-smoothing</i>: las representaciones se vuelven demasiado similares."),
        table([
            ["Componente", "Elección", "Criterio"],
            ["Grafo", "Rejilla 28×28, Moore-8", "Captura bordes y diagonales de trazos"],
            ["α", "0.35", "Conserva 65% de la señal propia"],
            ["T", "2 pasos", "Sensibilidad entre 0 y 3"],
            ["Capa oculta", "64 ReLU", "Capacidad moderada sin GPU"],
            ["Salida", "10 Softmax", "Clasificación mutuamente excluyente"],
        ], [3.7*cm, 4.5*cm, 8.4*cm]),
        P("La diferencia causal entre modelos no puede atribuirse solo al grafo, porque Graph-MLP también añade no linealidad. Por eso el análisis con T=0 funciona como ablación: cuantifica cuánto cambia el resultado al retirar únicamente la propagación."),
    ])

    # 6. Datos
    add_page(c, 6, "Datos", "3. Datos, preparación y gobernanza de origen", [
        P("MNIST reúne 70,000 imágenes de dígitos manuscritos centradas y normalizadas en tamaño: 60,000 para entrenamiento y 10,000 para prueba [1,10]. La copia `mnist.npz` fue descargada el 9 de agosto de 2026. Se conserva la partición oficial; el conjunto de prueba no interviene en selección de hiperparámetros."),
        table([
            ["Variable", "Tipo original", "Unidad/rango", "Uso"],
            ["x_train", "uint8, 60,000×28×28", "intensidad 0–255", "Ajuste y validación"],
            ["y_train", "uint8, 60,000", "dígito 0–9", "Etiqueta supervisada"],
            ["x_test", "uint8, 10,000×28×28", "intensidad 0–255", "Evaluación final"],
            ["y_test", "uint8, 10,000", "dígito 0–9", "Referencia final"],
        ], [2.7*cm, 5.3*cm, 3.7*cm, 4.9*cm]),
        P("<b>Procesamiento.</b> Se divide la intensidad entre 255 y se usa float32. No hay valores faltantes, imputación ni exclusiones. Para validación se selecciona una muestra estratificada de 12,000 ejemplos; para el ajuste final, 30,000, de los cuales 15% se reserva para validación. Las mismas observaciones alimentan ambos modelos."),
        P("<b>Prevención de fuga.</b> La transformación de grafo no usa etiquetas ni estadísticas del conjunto completo; depende únicamente de los vecinos de cada imagen. La semilla fija 2026 determina muestreo, pliegues e inicialización. La prueba oficial permanece cerrada hasta terminar el ajuste."),
        P("<b>Calidad.</b> Las clases están razonablemente balanceadas: la más frecuente es 1 (6,742) y la menos frecuente es 5 (5,421), razón 1.24. Esto permite interpretar exactitud, aunque F1 macro sigue siendo la métrica principal para dar el mismo peso a cada clase."),
        P("<b>Derechos de uso.</b> MNIST deriva de bases NIST y se distribuye ampliamente para investigación. El repositorio conserva atribución y separa la licencia MIT del código de los términos del dataset. No se mezclan licencias ni se afirma propiedad sobre los datos."),
    ])

    # 7 EDA
    add_page(c, 7, "Exploración", "3.1. Análisis exploratorio: balance, trazo y posición", [
        img("figura_1_muestras_distribucion.png", 17.1*cm, 9.6*cm),
        P("<b>Figura 1.</b> Muestras y conteo por clase. Los trazos varían aun dentro de una clase, mientras la distribución permanece suficientemente balanceada. Esto respalda métricas macro y particiones estratificadas." , CAPTION),
        Spacer(1, 6), img("figura_2_promedios_clase.png", 17.1*cm, 9.6*cm),
        P("<b>Figura 2.</b> Imagen promedio por clase. La energía se concentra en regiones distintas y las diagonales son informativas; la vecindad de Moore es razonable. También se observa fuerte centrado, una condición que puede no cumplirse en formularios reales.", CAPTION),
    ])

    # 8 metodología
    add_page(c, 8, "Métodos", "4. Ajuste, validación y métricas", [
        P("La evaluación tiene dos niveles. Primero, validación cruzada estratificada de tres pliegues sobre 12,000 ejemplos balanceados: cada pliegue se usa una vez para validar y los otros dos para ajustar. Ambos modelos reciben exactamente los mismos índices. Segundo, se ajustan sobre 30,000 ejemplos con 15% de validación y se evalúan una sola vez sobre las 10,000 imágenes oficiales."),
        table([
            ["Decisión", "Softmax", "Graph-MLP"],
            ["Entrada", "784 intensidades", "784 intensidades tras T=2"],
            ["Capacidad", "7,850 parámetros", "≈50,900 parámetros"],
            ["Optimizador", "Adam, lr=0.002", "Adam, lr=0.001"],
            ["Épocas / lote", "12 / 256", "12 / 256"],
            ["Regularización", "L2=10⁻⁴", "L2=10⁻⁴"],
            ["Semilla", "2026", "2026"],
        ], [3.7*cm, 6.3*cm, 6.6*cm]),
        P("<b>Métricas.</b> Exactitud=(aciertos/n); precisiónₖ=VPₖ/(VPₖ+FPₖ); exhaustividadₖ=VPₖ/(VPₖ+FNₖ); F1ₖ=2PR/(P+R). Las versiones macro promedian las diez clases. La pérdida logarítmica evalúa la probabilidad asignada a la clase verdadera y penaliza errores confiados."),
        P("<b>Criterio de elección.</b> Se prioriza F1 macro de prueba, acompañado de la media y desviación estándar en validación. Un aumento menor a un punto sin mejora de pérdida o con alta inestabilidad no justificaría más complejidad."),
        P("<b>Sensibilidad.</b> Se prueban λ∈{0,10⁻⁴,10⁻³}, T∈{0,1,2,3} y tamaños de entrenamiento {5,000;10,000;15,000}. Todos se evalúan en una validación estratificada fija; se reporta F1 macro. T=0 separa la contribución de no linealidad de la propagación."),
        P("El código evita la matriz densa A: suma ocho desplazamientos de la imagen, divide por el grado y mezcla con H. El costo por paso escala con el número de aristas, coherente con GNN eficientes [4]."),
    ])

    # 9 resultados
    test = RESULTS["test_results"]
    cv = RESULTS["cv_summary"]
    result_table = [
        ["Modelo", "CV F1 macro", "Prueba exactitud", "Prueba F1", "Log-loss"],
        ["Softmax", f"{cv['Softmax']['f1_macro']['mean']*100:.2f}% ± {cv['Softmax']['f1_macro']['std']*100:.2f}", f"{test['Softmax']['accuracy']*100:.2f}%", f"{test['Softmax']['f1_macro']*100:.2f}%", f"{test['Softmax']['log_loss']:.3f}"],
        ["Graph-MLP", f"{cv['Graph-MLP']['f1_macro']['mean']*100:.2f}% ± {cv['Graph-MLP']['f1_macro']['std']*100:.2f}", f"{test['Graph-MLP']['accuracy']*100:.2f}%", f"{test['Graph-MLP']['f1_macro']*100:.2f}%", f"{test['Graph-MLP']['log_loss']:.3f}"],
    ]
    add_page(c, 9, "Resultados", "5. Graph-MLP mejora 3.3 puntos de F1 en la prueba", [
        img("figura_3_comparacion_metricas.png", 17.1*cm, 9.6*cm),
        P("<b>Figura 3.</b> Métricas sobre las mismas 10,000 imágenes. Graph-MLP supera a Softmax de forma consistente; la diferencia entre precisión y exhaustividad macro es mínima.", CAPTION),
        Spacer(1, 6), table(result_table, [3.1*cm, 3.9*cm, 3.4*cm, 3.1*cm, 3.1*cm]),
        P("La mejora absoluta de F1 es 3.31 puntos y la pérdida logarítmica cae 45.7% (0.280 a 0.152). La validación cruzada también favorece Graph-MLP en los tres pliegues, con una ventaja media de 2.30 puntos y desviaciones pequeñas."),
        P("Se elige Graph-MLP para el prototipo porque mejora discriminación y calibración probabilística sin requerir GPU. Sin embargo, el experimento combina propagación con no linealidad; la sección de sensibilidad evita atribuir toda la ganancia al grafo."),
    ], "95.51% de F1 macro: la alternativa con propagación y frontera no lineal gana bajo una comparación común." )

    # 10 matrices
    cm_story = [
        Table([[img("figura_4_confusion_softmax.png", 8.3*cm, 4.7*cm), img("figura_5_confusion_graph_mlp.png", 8.3*cm, 4.7*cm)]], colWidths=[8.45*cm, 8.45*cm], style=TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"), ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),2)])),
        P("<b>Figuras 4 y 5.</b> Matrices de confusión normalizadas. Graph-MLP reduce errores en casi todas las clases. Persisten pares con trazos semejantes: 4→9 (28 casos), 9→4 (28), 8→5 (21) y 3→5 (15).", CAPTION),
        P("La clase 5 es la más difícil para Softmax: 792/892 correctos (88.8%). Graph-MLP eleva esa cifra a 848/892 (95.1%). La clase 1 es la más fácil para ambos por su forma distintiva y baja ambigüedad."),
        P("Los errores remanentes no parecen aleatorios: se concentran en cambios locales de bucles, inclinación y cierre de trazos. Esto es coherente con la hipótesis espacial, pero también muestra que el promedio de vecinos puede borrar detalles finos."),
        P("En un uso real no basta una etiqueta. Se recomienda conservar la probabilidad máxima, enviar a revisión humana los casos con confianza inferior a un umbral validado y permitir corrección. Las matrices deben recalcularse por fuente de captura, región, edad y dispositivo cuando esas variables estén disponibles."),
        P("No se informa significancia inferencial porque la partición oficial tiene dependencia histórica de construcción y los modelos comparten ejemplos. La comparación se interpreta como evidencia empírica reproducible, no como garantía poblacional."),
    ]
    add_page(c, 10, "Resultados", "5.1. Los errores se concentran en pares visualmente cercanos", cm_story)

    # 11 sensibilidad
    sens_rows = RESULTS["sensitivity"]
    sens_table = [["Supuesto", "Valores", "Efecto sobre F1 macro"]]
    sens_table += [
        ["Regularización L2", "0; 10⁻⁴; 10⁻³", "92.51%; 92.51%; 92.37%: robusto"],
        ["Pasos T", "0; 1; 2; 3", "92.73%; 92.56%; 92.51%; 92.21%: sobre-suavizado"],
        ["Tamaño", "5k; 10k; 15k", "88.82%; 92.16%; 92.59%: sensible"],
    ]
    add_page(c, 11, "Sensibilidad", "6. La conclusión es robusta a L2, no a la cantidad de datos", [
        img("figura_6_sensibilidad.png", 17.1*cm, 9.6*cm),
        P("<b>Figura 6.</b> Sensibilidad de F1 macro. Las escalas verticales son locales a cada supuesto para hacer visible el cambio; los valores se rotulan directamente.", CAPTION),
        Spacer(1, 6), table(sens_table, [4.2*cm, 4.2*cm, 8.2*cm]),
        P("<b>Robustez.</b> La elección de λ entre 0 y 10⁻⁴ es prácticamente irrelevante. La propagación no explica por sí sola la mejora: T=0 produce el mayor F1 en esta ablación. Por tanto, la frontera no lineal aporta más que el suavizado fijo; el grafo debe interpretarse como una hipótesis estructural modesta, no como causa demostrada de toda la ganancia."),
        P("<b>Fragilidad.</b> Reducir datos a 5,000 resta 3.8 puntos frente a 15,000. En un piloto con pocas muestras locales, la incertidumbre sería mayor. Se recomienda priorizar recolección y etiquetado antes que aumentar T o complejidad."),
    ])

    # 12 limitaciones
    add_page(c, 12, "Limitaciones", "6.1. Qué no captura el modelo y cuándo dejaría de ser válido", [
        P("<b>Validez externa.</b> MNIST contiene dígitos centrados, en escala de grises y fondo uniforme. Formularios costarricenses pueden incluir ruido, distintos bolígrafos, inclinación, celdas, sellos, compresión y combinaciones de caracteres. El desempeño reportado no se transfiere automáticamente."),
        P("<b>Atribución del efecto.</b> Softmax es lineal y Graph-MLP es no lineal además de propagar mensajes. La ablación T=0 sugiere que la no linealidad explica más mejora que el grafo fijo. Un diseño futuro debe comparar MLP crudo, MLP suavizado, CNN y GNN aprendible con capacidad semejante."),
        P("<b>Topología.</b> La vecindad Moore presupone una rejilla y pesos uniformes. En grafos irregulares, documentos segmentados o trazos vectoriales, las aristas tendrían otro significado. El modelo no aprende atención ni pesos por relación."),
        P("<b>Recursos.</b> Para asegurar ejecución sin GPU se utiliza una muestra de 30,000 y una capa oculta. Esto limita capacidad. El notebook original entrenó solo 5,000 ejemplos y además anuló mensajes por un error de índices; sus 12.6% no eran evidencia contra GNN."),
        P("<b>Métricas.</b> F1 macro no mide calibración por subgrupo, costo de revisión, latencia ni impacto de errores. La pérdida logarítmica ayuda, pero faltan curvas de confiabilidad, evaluación de rechazo y costo específico por confusión."),
        P("<b>Condiciones de invalidez.</b> El resultado deja de ser defendible si cambia la distribución de captura, aparecen nuevas clases, hay recortes incorrectos, se usan caracteres no centrados o la tasa de error por subgrupo supera el nivel acordado. Cualquier despliegue exige prueba local, monitoreo y retirada segura."),
        table([
            ["Con más tiempo/datos", "Prueba propuesta"],
            ["Muestra costarricense", "Recolectar y separar por institución/dispositivo"],
            ["Modelos equivalentes", "MLP, CNN y GNN con parámetros comparables"],
            ["Incertidumbre", "Calibración, bootstrap e intervalo por clase"],
            ["Robustez", "Rotación, ruido, desplazamiento y escritura fuera de muestra"],
        ], [6.2*cm, 10.4*cm]),
    ])

    # 13 ética
    add_page(c, 13, "Ética", "7. Consideraciones éticas y gobernanza de datos", [
        P("<b>Origen y permiso.</b> El dataset se atribuye a MNIST/NIST [1,10]. El código propio se publica con licencia MIT; la licencia no se extiende a los datos. Antes de añadir formularios reales se debe registrar base legal, propósito, retención y autorización de publicación."),
        P("<b>Privacidad.</b> MNIST no incluye nombres ni metadatos directos, pero la caligrafía puede convertirse en dato vinculable cuando se asocia con formularios. En un piloto se deben recortar solo dígitos necesarios, eliminar identificadores, cifrar almacenamiento, limitar accesos y fijar plazos de borrado."),
        P("<b>Sesgo y representación.</b> No hay variables demográficas ni procedencia de los escritores para auditar equidad. Pueden estar ausentes trazos de personas costarricenses, adultos mayores, niños, personas con discapacidad motora y estilos regionales. Un promedio global alto puede ocultar daño concentrado."),
        P("<b>Uso indebido.</b> Una clasificación incorrecta en calificaciones, montos, identificadores o expedientes puede afectar derechos. El modelo no debe tomar decisiones finales. Debe sugerir una lectura, mostrar confianza, conservar imagen original y escalar casos dudosos a una persona."),
        P("<b>Gobernanza.</b> Siguiendo NIST AI RMF [11], se proponen cuatro funciones: gobernar (responsable, documentación y auditoría); mapear (usuarios, contexto y daños); medir (F1 por clase/subgrupo, calibración y deriva); gestionar (umbral de rechazo, revisión y retiro). Las tarjetas de modelo ayudan a comunicar uso previsto y límites [12]."),
        table([
            ["Riesgo", "Control mínimo", "Evidencia"],
            ["Error confiado", "Umbral + revisión humana", "Tasa de rechazo y error residual"],
            ["Deriva", "Muestreo mensual", "F1 y calibración por fuente"],
            ["Acceso indebido", "Roles, cifrado y bitácora", "Auditoría de accesos"],
            ["Sesgo", "Muestra local y análisis por subgrupo", "Brechas con intervalos"],
            ["Uso fuera de alcance", "Ficha de modelo y controles de interfaz", "Incidentes y acciones correctivas"],
        ], [3.4*cm, 7.0*cm, 6.2*cm]),
    ])

    # 14 conclusiones
    add_page(c, 14, "Cierre", "8. Conclusiones y recomendaciones", [
        P("<b>Conclusión 1 — representación.</b> MNIST puede expresarse como una rejilla-grafo de 784 nodos; la vecindad de Moore formaliza la continuidad de trazos. Con esto se cumple el objetivo de conectar teoría de grafos y clasificación."),
        P("<b>Conclusión 2 — comparación.</b> Graph-MLP obtuvo 95.51% de F1 macro frente a 92.19% de Softmax y redujo log-loss de 0.280 a 0.152. La ventaja también apareció en cada pliegue. Por tanto, se selecciona Graph-MLP como prototipo, no como solución lista para producción."),
        P("<b>Conclusión 3 — sensibilidad.</b> El resultado es estable ante L2, se degrada con demasiada propagación y depende fuertemente de la cantidad de datos. La ablación T=0 advierte que la no linealidad, más que el grafo fijo, explica buena parte de la mejora."),
        P("<b>Conclusión 4 — uso responsable.</b> MNIST no representa escritura costarricense y carece de atributos para auditoría demográfica. El modelo debe limitarse a investigación hasta completar validación local, privacidad, revisión humana y monitoreo."),
        P("<b>Recomendaciones prácticas.</b> (1) ejecutar un piloto con al menos 1,000–5,000 dígitos locales separados por fuente; (2) comparar MLP, CNN y GNN con capacidad equivalente; (3) fijar un umbral que envíe baja confianza a revisión; (4) medir F1, calibración y tiempo ahorrado por institución; (5) documentar versión, datos y aprobaciones; y (6) detener el sistema si la deriva o la brecha por subgrupo supera el límite definido."),
        P("<b>Reproducibilidad.</b> El repositorio contiene la copia de datos (<100 MB), semilla 2026, tres notebooks ejecutables en orden, funciones NumPy, resultados JSON, figuras, requisitos y licencia. No contiene rutas personales, credenciales ni dependencias ocultas."),
        P(f"<b>Repositorio público:</b> {REPO_URL}"),
        P("La respuesta útil no es «las GNN siempre son mejores». Es más concreta: para este conjunto, una frontera no lineal con contexto local supera la referencia lineal; antes de usarla en Costa Rica, el valor marginal del grafo y la validez externa deben demostrarse con datos locales."),
    ], "Recomendación: invertir primero en datos locales y revisión humana; después decidir si una GNN aprendible agrega valor." )

    # 15 referencias
    refs = [
        "[1] LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). Gradient-based learning applied to document recognition. <i>Proceedings of the IEEE, 86</i>(11), 2278–2324. https://doi.org/10.1109/5.726791",
        "[2] Scarselli, F., Gori, M., Tsoi, A. C., Hagenbuchner, M., & Monfardini, G. (2009). The graph neural network model. <i>IEEE Transactions on Neural Networks, 20</i>(1), 61–80. https://doi.org/10.1109/TNN.2008.2005605",
        "[3] Li, Y., Tarlow, D., Brockschmidt, M., & Zemel, R. (2016). Gated graph sequence neural networks. <i>International Conference on Learning Representations</i>. https://arxiv.org/abs/1511.05493",
        "[4] Kipf, T. N., & Welling, M. (2017). Semi-supervised classification with graph convolutional networks. <i>International Conference on Learning Representations</i>. https://arxiv.org/abs/1609.02907",
        "[5] Goodfellow, I., Bengio, Y., & Courville, A. (2016). <i>Deep learning</i>. MIT Press. https://www.deeplearningbook.org/",
        "[6] Bishop, C. M. (2006). <i>Pattern recognition and machine learning</i>. Springer.",
        "[7] Bronstein, M. M., Bruna, J., Cohen, T., & Veličković, P. (2021). Geometric deep learning: Grids, groups, graphs, geodesics, and gauges. <i>IEEE Signal Processing Magazine, 38</i>(2), 18–42. https://doi.org/10.1109/MSP.2021.3052454",
        "[8] Hamilton, W. L., Ying, R., & Leskovec, J. (2017). Inductive representation learning on large graphs. <i>Advances in Neural Information Processing Systems, 30</i>. https://arxiv.org/abs/1706.02216",
        "[9] Xu, K., Hu, W., Leskovec, J., & Jegelka, S. (2019). How powerful are graph neural networks? <i>International Conference on Learning Representations</i>. https://arxiv.org/abs/1810.00826",
        "[10] National Institute of Standards and Technology. (2026). <i>MNIST database of handwritten digits</i>. Biometrics Research Database Catalog. https://tsapps.nist.gov/BDbC/Search/Details/387",
        "[11] Tabassi, E. (2023). <i>Artificial Intelligence Risk Management Framework (AI RMF 1.0)</i> (NIST AI 100-1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.AI.100-1",
        "[12] Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model cards for model reporting. <i>Proceedings of FAT*</i>, 220–229. https://doi.org/10.1145/3287560.3287596",
        "[13] Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., & Dennison, D. (2015). Hidden technical debt in machine learning systems. <i>Advances in Neural Information Processing Systems, 28</i>.",
    ]
    add_page(c, 15, "Referencias", "Referencias y declaración de uso de IA", [
        *[P(r, REF) for r in refs],
        Spacer(1, 5), P("<b>Declaración de uso de asistentes de IA.</b> Se utilizó un asistente para detectar y explicar el error de propagación, organizar el repositorio, proponer código reproducible, generar un borrador del informe y apoyar la revisión de formato. El grupo debe revisar, ejecutar y comprender cada sección antes de firmar y presentar. Los resultados numéricos fueron obtenidos al ejecutar el código incluido con semilla 2026; no fueron inventados."),
        P("<b>Disponibilidad.</b> Datos, notebooks, código, métricas y documentos: " + REPO_URL, LEFT),
    ])

    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
