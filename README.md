# Redes neuronales sobre grafos para clasificar dígitos MNIST

Proyecto integrador de **BCD5105 Modelado matemático**, II Cuatrimestre 2026, Lead University.

**Integrantes:** Diego Díaz, Bairon Horna, Ignacio Marín, Jordan López, Aaron Medrano y Emilio de Gomez.  
**Profesor:** Jordy Alfaro Brenes.  
**Semilla reproducible:** `default_rng(2026)`.
**Repositorio público:** https://github.com/EmiliodeGomez/redes-neuronales-grafos-mnist

## Problema

Se estudia si incorporar la vecindad espacial de los píxeles mejora la clasificación de dígitos manuscritos. Cada imagen MNIST se interpreta como un grafo no dirigido de 784 nodos, conectado mediante vecindad de Moore. Se comparan dos modelos con supuestos distintos: regresión Softmax lineal sobre píxeles y Graph-MLP, que agrega mensajes entre vecinos antes de una capa oculta no lineal.

## Datos

- Fuente original: [MNIST Database of Handwritten Digits](https://yann.lecun.com/exdb/mnist/).
- Copia utilizada: `data/raw/mnist.npz`, descargada el 9 de agosto de 2026.
- Tamaño: 60,000 imágenes de entrenamiento y 10,000 de prueba; 28×28 píxeles; 10 clases.
- Licencia/uso: datos derivados de bases NIST y distribuidos para investigación. El proyecto no contiene datos personales identificables.

## Resultados principales

Sobre las mismas 10,000 imágenes de prueba, Softmax obtuvo **92.30%** de exactitud y **92.19%** de F1 macro; Graph-MLP obtuvo **95.56%** y **95.51%**, respectivamente. En validación cruzada estratificada de tres pliegues, el F1 macro promedio fue 89.02% para Softmax y 91.32% para Graph-MLP. La sensibilidad muestra estabilidad frente a L2, deterioro leve por sobre-suavizado al aumentar la propagación y una dependencia clara del tamaño muestral.

## Cómo reproducir

### Google Colab

1. Abra los notebooks desde este repositorio.
2. Ejecute en orden `01_exploracion.ipynb`, `02_modelos.ipynb` y `03_validacion.ipynb`.
3. Si `mnist.npz` no está disponible, la primera celda lo descarga desde el almacenamiento público de TensorFlow/Keras.
4. Use **Runtime → Run all**. No se requieren rutas locales ni GPU.

### Entorno local

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/ejecutar_experimentos.py
```

El script completo tarda aproximadamente 15–30 segundos en una computadora moderna con NumPy enlazado a BLAS. Los resultados esperados quedan en `data/processed/resultados.json`.

## Estructura

```text
Entrega_Final_GNN_MNIST/
├── README.md
├── LICENSE
├── requirements.txt
├── data/
│   ├── raw/mnist.npz
│   └── processed/resultados.json
├── notebooks/
│   ├── 01_exploracion.ipynb
│   ├── 02_modelos.ipynb
│   └── 03_validacion.ipynb
├── src/
│   ├── modelado_mnist.py
│   ├── ejecutar_experimentos.py
│   └── generar_figuras.py
├── figuras/
├── docs/
└── presentacion/
```

## Decisiones metodológicas

- La partición oficial de prueba de MNIST se conserva intacta.
- La validación es estratificada y usa exactamente los mismos pliegues para ambos modelos.
- El ajuste final usa una muestra estratificada de 30,000 ejemplos, con 15% para validación.
- Las métricas son exactitud, precisión macro, exhaustividad macro, F1 macro y pérdida logarítmica.
- Graph-MLP realiza `H(t+1)=(1−α)H(t)+αD⁻¹AH(t)` con `α=0.35` y dos pasos antes del clasificador no lineal.

## Limitaciones

MNIST es un conjunto histórico, centrado y limpio; no representa documentos costarricenses ni variaciones reales de captura. Graph-MLP incorpora la topología como preprocesamiento fijo, no aprende pesos por arista. Los resultados no justifican automatizar decisiones de alto impacto sin validación externa, monitoreo de deriva y revisión humana.

## Licencia

El código y los documentos propios se publican bajo licencia MIT. La licencia no modifica los términos del conjunto MNIST.
