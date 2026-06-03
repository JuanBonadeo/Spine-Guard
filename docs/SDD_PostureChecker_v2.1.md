# SDD v2.1 — Especificación de Diseño Detallado
## Sistema de Corrección de Postura con OpenCV — Mejora del algoritmo de detección

---

## 1. Propósito

Versión incremental sobre la v2.0 enfocada **exclusivamente en perfeccionar el algoritmo de detección de postura**. No agrega funcionalidad de usuario nueva: mejora la *calidad* de la detección reduciendo falsos positivos, eliminando lag y aumentando la robustez ante oclusión y reposicionamientos.

Las decisiones de diseño se fundamentan en investigación del estado del arte (2024-2025) — ver §9 Referencias.

---

## 2. Problemas del algoritmo v2.0 que esta versión resuelve

| # | Problema en v2.0 | Causa raíz | Mejora v2.1 |
|---|------------------|-----------|-------------|
| 1 | Reacción lenta (~0.5s de lag) | Promedio móvil de 15 frames mete lag fijo | **One Euro Filter** (cutoff adaptativo) |
| 2 | Falsos positivos al ocluir un hombro o salir de cuadro | MediaPipe *adivina* landmarks no visibles y se usan igual | **Gating por `visibility`** |
| 3 | "Cabeza adelante" poco confiable | Única señal = ratio cara/hombros (proxy de tamaño) | **Segunda señal con coordenada Z** |
| 4 | Estado parpadea en el límite del umbral | Umbral único de entrada/salida | **Histéresis** (enter/exit) |
| 5 | Reposicionarse cómodo queda marcado como mala postura para siempre | Referencia de calibración 100% estática | **Re-baseline adaptativo** |

---

## 3. Alcance de v2.1

| Incluido | Excluido (queda para v3.0) |
|----------|----------------------------|
| One Euro Filter para suavizado | Clasificador ML personalizado |
| Gating por visibility/presence | Medición de CVA real (requiere vista de perfil) |
| Métrica de profundidad (Z) para forward head | Soporte multi-cámara |
| Histéresis enter/exit por métrica | — |
| Re-baseline adaptativo de la referencia | — |
| Indicador de confianza en el HUD | — |

**Módulos afectados:** `filters.py` (nuevo), `analyzer.py` (refactor), `config.py` (nuevos parámetros), `main.py` (HUD menor). El resto (`notifier`, `health_bar`, `session_stats`, `tray`, `capture`) **sin cambios**.

---

## 4. Mejora 1 — One Euro Filter

### 4.1 Motivación

El promedio móvil de N frames reduce jitter pero introduce **lag constante** proporcional a la ventana. El **1€ Filter** (Casiez et al.) usa un filtro paso-bajo de primer orden con **frecuencia de corte adaptativa a la velocidad de la señal**: a baja velocidad filtra fuerte (mata jitter cuando estás quieto), a alta velocidad filtra poco (responde rápido cuando te movés). Mejora ambos ejes simultáneamente con solo 2 parámetros.

### 4.2 Algoritmo

```
Para cada muestra x en tiempo t (dt = t - t_prev):

  α(fc) = 1 / (1 + τ/dt),   con  τ = 1 / (2π·fc)

  # 1) derivada suavizada
  dx       = (x - x_prev) / dt
  dx_hat   = α(d_cutoff)·dx + (1 - α(d_cutoff))·dx_hat_prev

  # 2) cutoff adaptativo
  cutoff   = min_cutoff + beta·|dx_hat|

  # 3) señal suavizada
  x_hat    = α(cutoff)·x + (1 - α(cutoff))·x_hat_prev
```

- `min_cutoff` ↓ ⇒ más suave en reposo (más jitter eliminado).
- `beta` ↑ ⇒ menos lag al moverse rápido.

### 4.3 Diseño — `filters.py` (NUEVO)

```
OneEuroFilter
├── __init__(min_cutoff: float, beta: float, d_cutoff: float = 1.0)
├── filter(value: float, timestamp: float) -> float
└── reset() -> None
```

**Decisión de diseño — qué se filtra:** se filtran las **6 métricas derivadas** (un `OneEuroFilter` por métrica), no las coordenadas crudas de cada landmark.
- *Pro:* simple (6 filtros vs 21), reemplaza directamente el `deque` de suavizado actual, mantiene la estructura de `PostureMetrics`.
- *Contra:* las métricas son no lineales sobre los landmarks; filtrar la fuente sería marginalmente más preciso.
- *Veredicto:* el ruido dominante de MediaPipe se traslada casi linealmente a las métricas normalizadas; el costo/beneficio favorece filtrar métricas. Reevaluable en v3.0.

**Contenedor:** clase auxiliar `MetricsSmoother` que mantiene un `OneEuroFilter` por campo de `PostureMetrics` y expone `smooth(metrics, timestamp) -> PostureMetrics`.

```
MetricsSmoother
├── __init__(min_cutoff, beta)
├── smooth(metrics: PostureMetrics, t: float) -> PostureMetrics
└── reset() -> None
```

### 4.4 Parámetros iniciales sugeridos (postura = señal lenta)

| Parámetro | Valor inicial | Razón |
|-----------|---------------|-------|
| `ONE_EURO_MIN_CUTOFF` | `0.5` | Señal lenta → corte bajo en reposo |
| `ONE_EURO_BETA` | `0.01` | Reacción rápida al encorvarse |
| `ONE_EURO_D_CUTOFF` | `1.0` | Default de la literatura |

### 4.5 Cambio en `analyzer.py`

`_smooth()` (que usaba `deque` + promedio) se reemplaza por `MetricsSmoother.smooth(metrics, time.time())`. Se elimina `SMOOTHING_WINDOW`.

---

## 5. Mejora 2 — Gating por visibility

### 5.1 Motivación

Cada `NormalizedLandmark` de MediaPipe Tasks trae `.visibility` ∈ [0,1]. Cuando un punto no se ve, MediaPipe lo **infiere** y nuestras métricas disparan falsos positivos. El paper PoseTrack identifica la **oclusión como la principal causa de error**.

### 5.2 Diseño

- Constante `VISIBILITY_THRESHOLD = 0.5`.
- Cada métrica declara qué landmarks necesita. Antes de evaluar un problema, se verifica que **todos** sus landmarks superen el umbral; si no, esa métrica se marca **no confiable** y **no contribuye** a `problems` (no suma ni resta).
- Confianza global del frame: `confidence = min(visibility de NOSE, LEFT_SHOULDER, RIGHT_SHOULDER)`. Si `confidence < VISIBILITY_THRESHOLD`, el frame se trata como **"baja confianza"** → no se evalúa postura, no se actualiza la health bar negativamente (se congela), y el HUD lo indica.

### 5.3 Mapa métrica → landmarks requeridos

| Métrica | Landmarks | 
|---------|-----------|
| forward_lean | NOSE, LEFT_EYE_OUTER, RIGHT_EYE_OUTER, hombros |
| slouch_drop | NOSE, hombros |
| slouch_shoulder | hombros |
| shoulder_raise | orejas, hombros |
| head_tilt | LEFT_EAR, RIGHT_EAR |
| lateral_offset | NOSE, hombros |

### 5.4 Cambio en estructuras

`PostureResult` agrega:
```python
confidence: float          # 0..1, min visibility de landmarks core
reliable: bool             # confidence >= VISIBILITY_THRESHOLD
```

---

## 6. Mejora 3 — Profundidad (Z) para "cabeza adelante"

### 6.1 Motivación

Forward head detectado solo por tamaño relativo (cara/hombros) confunde "acercarse a la pantalla" con "adelantar la cabeza". MediaPipe entrega `z` relativo por landmark (negativo = más cerca de la cámara). Adelantar la cabeza **acerca la nariz en Z** respecto al plano de los hombros → señal independiente del tamaño.

### 6.2 Diseño

Nueva métrica en `PostureMetrics`:
```python
forward_z_ratio: float     # (z_mid_shoulder - z_nose) normalizado por shoulder_width
```
- Valor mayor ⇒ nariz más adelante que los hombros.

**Combinación de señales (reduce falsos positivos):** el problema *"Cabeza muy adelante"* se dispara si:
```
(forward_lean_delta > FWD_LEAN_TH) AND (forward_z_delta > FWD_Z_TH)
   OR
(forward_lean_delta > FWD_LEAN_TH * 1.6)   # ratio muy marcado, no requiere confirmación
```
Es decir, Z actúa como **confirmador**; salvo que el ratio sea extremo, se exige acuerdo de ambas señales.

> Advertencia documentada: la `z` de MediaPipe es ruidosa y de escala relativa. Por eso se usa **como delta vs la referencia calibrada** (no en absoluto) y pasa por el One Euro Filter como las demás métricas.

---

## 7. Mejora 4 — Histéresis y re-baseline adaptativo

### 7.1 Histéresis enter/exit

Cada problema usa **dos umbrales**: entra a "activo" con `enter`, y solo sale cuando cae por debajo de `exit = enter · HYSTERESIS_FACTOR` (ej. `0.6`). El analyzer mantiene el conjunto de problemas activos del frame anterior.

```
para cada métrica:
    th = exit_th  si el problema ya estaba activo
         enter_th si no lo estaba
    activo = (delta > th)
```

Resultado: el estado no parpadea cuando el delta oscila alrededor del umbral.

### 7.2 Re-baseline adaptativo

La referencia deja de ser 100% estática. Cuando la postura es **buena y confiable de forma sostenida**, la referencia deriva lentamente hacia las métricas actuales (EMA):

```
si is_good y reliable:
    ref = (1 - REBASELINE_RATE)·ref + REBASELINE_RATE·smoothed
```

- `REBASELINE_RATE` muy bajo (ej. `0.001`) ⇒ absorbe reposicionamientos cómodos en ~decenas de segundos sin recalibrar a mano.
- **Solo deriva con postura buena** (ya pasó los umbrales), nunca con mala → no puede "normalizar" una mala postura.
- *Riesgo documentado:* drift excesivo si el usuario mantiene una postura levemente subóptima que el sistema considera "buena". Mitigado por el rate bajo y por mantener la calibración manual (`C`) como reset duro.

---

## 8. Diseño integrado — nuevo flujo de `analyze()`

```
analyze(frame):
    t = time.time()
    lm = _detect(frame)                       # landmarks o None
    if lm is None:
        return PostureResult(no_detection, confidence=0, reliable=False)

    raw     = _extract_metrics(lm)            # ahora incluye forward_z_ratio
    conf    = _core_confidence(lm)            # min visibility de NOSE + hombros
    smoothed = self._smoother.smooth(raw, t)  # 1€ Filter por métrica

    if conf < VISIBILITY_THRESHOLD:           # frame poco confiable
        return PostureResult(is_good=last_state, reliable=False, confidence=conf, ...)

    is_good, problems = _evaluate(smoothed, lm)   # visibility-gating + histéresis + Z
    if is_good and conf alto:
        _rebaseline(smoothed)                 # EMA suave de la referencia

    return PostureResult(is_good, raw, smoothed, problems, confidence=conf, reliable=True, ...)
```

`_evaluate()` ahora:
1. Salta toda métrica cuyos landmarks no superen `VISIBILITY_THRESHOLD`.
2. Aplica histéresis (enter/exit) usando `self._active_problems` del frame previo.
3. Para forward head, combina `forward_lean` + `forward_z`.

### 8.1 Estructuras actualizadas

```python
@dataclass
class PostureMetrics:
    forward_lean_ratio: float
    forward_z_ratio: float        # NUEVO
    slouch_drop_ratio: float
    shoulder_width_norm: float
    shoulder_raise_ratio: float
    head_tilt_angle: float
    lateral_offset: float

@dataclass
class PostureResult:
    is_good: bool
    metrics: PostureMetrics
    smoothed: PostureMetrics
    problems: list[str]
    message: str
    has_landmarks: bool
    landmarks_px: list[tuple[int, int]]
    confidence: float             # NUEVO
    reliable: bool                # NUEVO
```

### 8.2 Estado interno nuevo del `PostureAnalyzer`

| Atributo | Tipo | Rol |
|----------|------|-----|
| `_smoother` | `MetricsSmoother` | 1€ Filter por métrica |
| `_active_problems` | `set[str]` | Histéresis entre frames |
| `_last_is_good` | `bool` | Estado a sostener en frames de baja confianza |

---

## 9. Cambios en `config.py`

```python
# ── One Euro Filter (reemplaza SMOOTHING_WINDOW) ──
ONE_EURO_MIN_CUTOFF = 0.5
ONE_EURO_BETA = 0.01
ONE_EURO_D_CUTOFF = 1.0

# ── Visibility gating ──
VISIBILITY_THRESHOLD = 0.5

# ── Profundidad Z ──
FORWARD_Z_THRESHOLD = 0.10

# ── Histéresis y re-baseline ──
HYSTERESIS_FACTOR = 0.6        # exit = enter * factor
REBASELINE_RATE = 0.001        # EMA de la referencia con postura buena
```

`SMOOTHING_WINDOW` y `AUTO_CALIBRATION_FRAMES` se mantienen (la auto-calibración no cambia). `SMOOTHING_WINDOW` queda obsoleto y se elimina.

---

## 10. Cambios en `main.py` (menores)

- El HUD muestra un indicador de **confianza**: si `not result.reliable`, dibujar `"SEÑAL DEBIL - acomodate frente a la camara"` en gris y **no** colorear el borde de rojo.
- En frames no confiables, **no** incrementar `bad_count` (evita alertas espurias).

Ningún otro módulo cambia.

---

## 11. Estructura de archivos (v2.1)

```
posture-checker/
├── main.py
├── capture.py
├── analyzer.py            # refactor: 1€ filter, visibility, Z, histéresis, re-baseline
├── filters.py             # NUEVO: OneEuroFilter + MetricsSmoother
├── notifier.py
├── health_bar.py
├── session_stats.py
├── tray.py
├── config.py             # nuevos parámetros
├── pose_landmarker_lite.task
├── requirements.txt
└── docs/
    ├── SDD_PostureChecker.md       # v1.0
    ├── SDD_PostureChecker_v2.md    # v2.0
    └── SDD_PostureChecker_v2.1.md  # este documento
```

Sin dependencias nuevas (el 1€ Filter se implementa a mano; no requиere librerías).

---

## 12. Plan de validación

| Caso | Esperado |
|------|----------|
| Quieto en buena postura 30s | Sin jitter de estado; health estable en ~100% |
| Encorvarse rápido | Detección en < 0.3s (vs ~0.5s en v2.0) |
| Taparse un hombro con la mano | Métrica de hombros se ignora; sin falso positivo |
| Salir del cuadro | "SEÑAL DEBIL"; sin alertas |
| Acercarse a la pantalla sin adelantar cabeza | NO dispara "cabeza adelante" (Z no confirma) |
| Reacomodarse cómodo y quedarse derecho 1 min | Re-baseline absorbe; vuelve a "OK" sin tocar C |
| Oscilar en el límite del umbral | Estado estable (histéresis), no parpadea |

Smoke test (sin cámara) extendido: `OneEuroFilter` converge a una constante; `MetricsSmoother` no introduce NaN; `_evaluate` respeta gating con visibility simulada baja.

---

## 13. Roadmap futuro (v3.0)

- **Clasificador ML personalizado** (logistic regression / SVM / MLP chico sobre los features ya calculados), con modo de entrenamiento etiquetado por el usuario. Los trabajos de referencia alcanzan 98-99% F1 con este enfoque. Requiere `scikit-learn`, recolección de datos y persistencia del modelo → cambio mayor de versión.
- **CVA real** mediante una calibración de perfil opcional o pose 3D.

---

## 14. Referencias

- Casiez, Roussel, Vogel — *1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems* — https://www.researchgate.net/publication/254005010
- *Building a Body Posture Analysis System using MediaPipe* — LearnOpenCV — https://learnopencv.com/building-a-body-posture-analysis-system-using-mediapipe/
- *An Intelligent Mobile Application to Monitor and Correct Sitting Posture Using MediaPipe* — arXiv 2508.11683 — https://arxiv.org/html/2508.11683 (oclusión como límite principal)
- *Recognition of Forward Head Posture Through 3D Human Pose Estimation with a GCN* — JMIR Formative Research 2024 — https://formative.jmir.org/2024/1/e55476 (CVA y límites de 2D)
- *MultiPosture* dataset — https://zenodo.org/records/14230872 · *SitPose* — https://arxiv.org/html/2412.12216v1 · *LGCSPNet* — https://www.sciencedirect.com/science/article/abs/pii/S0957417425021050 (clasificadores ML, v3.0)
