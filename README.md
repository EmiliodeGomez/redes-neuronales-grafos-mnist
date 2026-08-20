# Digitalización inteligente de archivos públicos en papel

Proyecto de **BCD5105 Modelado Matemático**, Lead University, 19 de agosto de 2026.

**Integrantes:** Diego Díaz, Bairon Horna, Ignacio Marín, Jordan López, Aaron Medrano y Emilio de Gomez.  
**Profesor:** Jordy Alfaro Brenes.  
**Repositorio:** <https://github.com/EmiliodeGomez/redes-neuronales-grafos-mnist>

## Enfoque

Se conserva el mismo experimento del proyecto anterior: clasificación de dígitos con Softmax y Graph-MLP sobre MNIST. El nuevo enfoque lo ubica como un **componente experimental de OCR** para apoyar la migración de protocolos, formularios y expedientes físicos de municipalidades y entidades públicas.

MNIST es el banco de prueba reproducible; no representa documentos costarricenses ni autoriza un despliegue. Un piloto real debe entrenarse y validarse de nuevo con recortes etiquetados de la serie documental elegida, conservar cada imagen original y enviar resultados dudosos a revisión humana.

## Resultados

| Modelo | CV F1 macro | Exactitud de prueba | F1 de prueba | Log-loss |
|---|---:|---:|---:|---:|
| Softmax | 89.02% ± 0.22 | 92.30% | 92.19% | 0.280 |
| Graph-MLP | **91.32% ± 0.39** | **95.56%** | **95.51%** | **0.152** |

Graph-MLP mejora 3.31 puntos de F1 y reduce 45.7% la pérdida logarítmica. La sensibilidad muestra estabilidad ante L2, deterioro por propagación excesiva y dependencia del tamaño muestral. La ablación `T=0` advierte que la no linealidad explica más mejora que el suavizado fijo.

## Datos

- MNIST: 60,000 imágenes de entrenamiento y 10,000 de prueba, 28×28 píxeles, 10 clases.
- Copia incluida: `data/raw/mnist.npz`.
- Semilla fija: `2026`.
- Contexto público: normativa NTN-003 y servicios de digitalización del [Archivo Nacional de Costa Rica](https://archivonacional.go.cr/).

## Reproducción

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/ejecutar_experimentos.py
python src/generar_figuras.py
```

Ejecute en orden, con **Run all**:

1. `notebooks/01_exploracion.ipynb`
2. `notebooks/02_modelos.ipynb`
3. `notebooks/03_validacion.ipynb`

No hay rutas personales ni credenciales. Los resultados quedan en `data/processed/resultados.json`.

## Uso institucional propuesto

1. Elegir una serie de bajo riesgo y definir el propósito archivístico.
2. Etiquetar 1,000–5,000 recortes locales separados por institución, tipo documental y escáner.
3. Comparar MLP, CNN y GNN con el mismo conjunto y medir F1, calibración, rechazo y tiempo ahorrado.
4. Conservar el folio original, metadatos, confianza, corrección humana y bitácora.
5. No automatizar decisiones, eliminación de papel ni modificación de expedientes.

## Estructura

```text
data/           datos originales y resultados
notebooks/      exploración, modelos y validación
src/            implementación reproducible
figuras/        siete visualizaciones numeradas
docs/           informe, guion y revisión de requisitos
presentacion/   PPTX editable y PDF
```

## Licencia y límites

El código y documentos propios usan licencia MIT; MNIST conserva sus términos. Antes de incorporar archivos reales deben definirse base legal, permisos, acceso, retención, privacidad y preservación. Este repositorio es un prototipo académico, no un sistema OCR listo para producción.
