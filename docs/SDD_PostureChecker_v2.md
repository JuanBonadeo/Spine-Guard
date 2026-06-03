# SDD v2.0 — Especificación de Diseño Detallado
## Sistema de Corrección de Postura con OpenCV

---

## 1. Propósito

Sistema de escritorio que monitorea la postura del usuario sentado frente a una laptop mediante visión por computadora. Analiza en tiempo real múltiples indicadores posturales, emite alertas sonoras escalables, lleva estadísticas de sesión, y permite pausar/reanudar el monitoreo. Pensado para webcam frontal de laptop donde se ve el torso superior.

---

## 2. Alcance

| Incluido (v2.0) | Excluido |
|------------------|----------|
| 5 métricas posturales con promedio móvil | Almacenamiento en DB |
| Auto-calibración al inicio | Múltiples usuarios simultáneos |
| Alertas sonoras con severidad escalable | Análisis de postura de pie |
| Barra de salud postural en tiempo real | App móvil |
| Estadísticas de sesión + export CSV | Entrenamiento de modelo propio |
| Pausa/reanudación del monitoreo | — |
| Break reminders periódicos | — |
| System tray para minimizar | — |

---

## 3. Cambios respecto a v1.0

| Área | v1.0 | v2.0 |
|------|------|------|
| Métricas | 4 métricas crudas por frame | 5 métricas + promedio móvil (ventana de N frames) |
| Slouch | Solo caída de cabeza | Caída de cabeza + ancho de hombros + tensión hombros subidos |
| Calibración | Manual (tecla C) | Auto-calibración al inicio + recalibrar con C |
| Alertas | Beep único + toast | 3 niveles de severidad (leve → medio → fuerte) |
| Feedback visual | Texto + landmarks | Barra de salud postural + color del borde |
| Estadísticas | Ninguna | % de tiempo bueno, conteo de alertas, export CSV |
| Control | Solo Q/C | Q, C, P (pausa), B (break manual) |
| Ejecución | Solo ventana abierta | System tray para minimizar a fondo |

---

## 4. Tecnologías

| Componente | Tecnología | Justificación |
|-----------|------------|---------------|
| Captura de video | OpenCV (`cv2.VideoCapture`) | Acceso a webcam + procesamiento de frames |
| Detección de pose | MediaPipe Pose (Tasks API) | 33 landmarks, sin GPU, tiempo real |
| Notificaciones | `plyer` | Toast nativo de Windows |
| Sonido | `winsound` | Beep nativo sin dependencias |
| UI principal | OpenCV `imshow` | Ventana simple con overlay |
| System tray | `pystray` + `Pillow` | Ícono en bandeja del sistema |
| Persistencia | CSV (stdlib `csv`) | Export de estadísticas sin DB |
| Lenguaje | Python 3.10+ | — |

---

## 5. Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                         main.py                               │
│                    (loop principal + tray)                     │
├────────────┬──────────────┬──────────────┬───────────────────┤
│ capture.py │ analyzer.py  │ notifier.py  │ session_stats.py  │
│ Webcam     │ Métricas +   │ Sonido +     │ Estadísticas +    │
│            │ promedio      │ severidad    │ CSV export        │
│            │ móvil         │ escalable    │                   │
├────────────┴──────────────┴──────────────┴───────────────────┤
│                        config.py                              │
│                 (constantes y umbrales)                        │
├──────────────────────────────────────────────────────────────┤
│                        tray.py                                │
│              (system tray icon + menú)                        │
└──────────────────────────────────────────────────────────────┘
        │                │                │
   [OpenCV]        [MediaPipe]       [pystray]
   [Webcam]        [Pose Model]      [Pillow]
```

---

## 6. Diseño de Módulos

### 6.1 `config.py` — Configuración

| Constante | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `CAMERA_INDEX` | `int` | `0` | Índice de la webcam |
| `CHECK_INTERVAL_SEC` | `int` | `180` | Intervalo mínimo entre alertas (3 min) |
| `BAD_POSTURE_FRAMES` | `int` | `10` | Frames malos consecutivos para confirmar |
| `SMOOTHING_WINDOW` | `int` | `15` | Tamaño de ventana del promedio móvil |
| `AUTO_CALIBRATION_FRAMES` | `int` | `90` | Frames para auto-calibración (~3 seg a 30fps) |
| `FORWARD_LEAN_THRESHOLD` | `float` | `0.15` | Umbral de cabeza adelantada |
| `SLOUCH_DROP_THRESHOLD` | `float` | `0.12` | Umbral de caída de cabeza |
| `SLOUCH_SHOULDER_THRESHOLD` | `float` | `0.08` | Umbral de hombros adelante (ancho crece) |
| `SHOULDER_RAISE_THRESHOLD` | `float` | `0.10` | Umbral de hombros subidos (tensión) |
| `HEAD_TILT_THRESHOLD` | `float` | `8.0` | Umbral de inclinación lateral (grados) |
| `LATERAL_LEAN_THRESHOLD` | `float` | `0.12` | Umbral de inclinación lateral |
| `HEALTH_DECAY_RATE` | `float` | `0.02` | Cuánto baja la salud por frame malo |
| `HEALTH_RECOVERY_RATE` | `float` | `0.01` | Cuánto sube la salud por frame bueno |
| `SEVERITY_THRESHOLDS` | `tuple` | `(0.6, 0.3)` | Salud debajo de 0.6 → medio, debajo de 0.3 → fuerte |
| `BEEP_LEVELS` | `list[tuple]` | `[(800,300), (1200,500), (1600,800)]` | (freq, duración) por nivel de severidad |
| `BREAK_INTERVAL_SEC` | `int` | `2700` | Recordatorio de break (45 min) |
| `CSV_PATH` | `str` | `"session_log.csv"` | Ruta del log de sesiones |

### 6.2 `capture.py` — Captura de video

Sin cambios respecto a v1.0.

```
Camera
├── __init__(device_index: int)
├── read_frame() -> tuple[bool, np.ndarray]
├── is_opened() -> bool
└── release() -> None
```

### 6.3 `analyzer.py` — Análisis de postura

**Dataclass `PostureMetrics`**

```python
@dataclass
class PostureMetrics:
    forward_lean_ratio: float     # cara/hombros — sube al acercarse
    slouch_drop_ratio: float      # nariz-a-hombros — baja al encorvarse
    shoulder_width_norm: float    # ancho de hombros — sube al encorvarse
    shoulder_raise_ratio: float   # oreja-a-hombro — baja al subir hombros (NUEVO)
    head_tilt_angle: float        # ángulo oreja-oreja vs horizontal
    lateral_offset: float         # nariz descentrada de hombros
```

**Clase `PostureAnalyzer`**

```
PostureAnalyzer
├── __init__(thresholds, smoothing_window)
├── analyze(frame) -> PostureResult
├── calibrate(frame) -> bool
├── auto_calibrate(frame) -> bool | None    # NUEVO: acumula frames y calibra
├── is_calibrated() -> bool
├── _extract_metrics(landmarks) -> PostureMetrics
├── _smooth(metrics) -> PostureMetrics       # NUEVO: promedio móvil
├── _evaluate(metrics) -> tuple[bool, list[str]]
├── draw(frame, result) -> np.ndarray
└── close() -> None
```

**Promedio móvil (NUEVO):**

Se mantiene un buffer circular de los últimos `SMOOTHING_WINDOW` `PostureMetrics`. Cada campo se promedia antes de evaluar umbrales. Esto filtra ruido de MediaPipe frame a frame.

```
Buffer: [m1, m2, m3, ..., m15]
                 │
                 ▼
        promedio por campo
                 │
                 ▼
        PostureMetrics suavizado
                 │
                 ▼
        _evaluate(suavizado) → (is_good, problems)
```

**Detección de hombros subidos (NUEVO):**

```
    Oreja Izq (7)             Oreja Der (8)
        │                          │
        │ dist_y                   │ dist_y
        │                          │
    Hombro Izq (11)          Hombro Der (12)
```

- `shoulder_raise_ratio = promedio(dist_oreja_hombro) / shoulder_width`
- Cuando subís los hombros por tensión, la distancia oreja→hombro se achica.
- Si `ref_ratio - current_ratio > SHOULDER_RAISE_THRESHOLD` → "Hombros tensos".

**Auto-calibración (NUEVO):**

```
[Inicio]
   │
   ▼
Fase: AUTO_CALIBRATING
   │
   ├── Acumular métricas durante AUTO_CALIBRATION_FRAMES (≈3 seg)
   │   └── Mostrar countdown en pantalla: "Calibrando... sentate derecho"
   │
   ▼
Promediar todas las métricas acumuladas → referencia
   │
   ▼
Fase: MONITORING
```

- Al iniciar, se recolectan ~90 frames con la persona sentada derecha.
- Se promedian para obtener la referencia (más estable que un solo frame).
- En la UI se muestra un countdown de 3 segundos.

**Dataclass `PostureResult`**

```python
@dataclass
class PostureResult:
    is_good: bool
    metrics: PostureMetrics           # métricas crudas del frame
    smoothed: PostureMetrics          # métricas suavizadas (NUEVO)
    problems: list[str]
    message: str
    has_landmarks: bool
    landmarks_px: list[tuple[int, int]]
```

### 6.4 `notifier.py` — Alertas con severidad escalable

**Clase `PostureNotifier`**

```
PostureNotifier
├── __init__(interval_sec, beep_levels, break_interval)
├── should_notify() -> bool
├── notify(message, severity) -> None         # NUEVO: severity 0/1/2
├── should_break_remind() -> bool             # NUEVO
├── break_remind() -> None                    # NUEVO
├── reset_timer() -> None
└── reset_break_timer() -> None
```

**Severidad escalable (NUEVO):**

| Nivel | Condición | Beep | Mensaje |
|-------|-----------|------|---------|
| 0 - Leve | `health > 0.6` | 800Hz, 300ms | "Corregí un poco la postura" |
| 1 - Medio | `0.3 < health ≤ 0.6` | 1200Hz, 500ms | "Tu postura empeoró bastante" |
| 2 - Fuerte | `health ≤ 0.3` | 1600Hz, 800ms | "Postura muy mala, sentate derecho" |

**Break reminders (NUEVO):**

- Cada `BREAK_INTERVAL_SEC` (45 min) se emite un toast: "Llevas 45 min sentado, levantate y estirá".
- Se resetea si el usuario pausa manualmente o presiona B.

### 6.5 `session_stats.py` — Estadísticas de sesión (NUEVO)

**Clase `SessionStats`**

```
SessionStats
├── __init__()
├── update(is_good: bool) -> None        # llamado cada frame
├── get_summary() -> SessionSummary
├── export_csv(path: str) -> None
└── reset() -> None
```

**Dataclass `SessionSummary`**

```python
@dataclass
class SessionSummary:
    total_time_sec: float
    good_time_sec: float
    bad_time_sec: float
    good_percentage: float       # 0-100
    total_alerts: int
    breaks_taken: int
```

**Export CSV:**

Cada sesión agrega una fila a `session_log.csv`:

```csv
fecha,inicio,duracion_min,postura_buena_pct,alertas,breaks
2026-06-03,14:30:00,45.2,78.3,5,2
```

### 6.6 `health_bar.py` — Barra de salud postural (NUEVO)

**Clase `HealthBar`**

```
HealthBar
├── __init__(decay_rate, recovery_rate)
├── update(is_good: bool) -> None
├── get_health() -> float                # 0.0 a 1.0
├── get_severity() -> int                # 0, 1 o 2
└── draw(frame, x, y, w, h) -> np.ndarray
```

**Mecánica:**

```
health = 1.0 (inicio)

Cada frame:
  si postura buena → health += RECOVERY_RATE  (capped a 1.0)
  si postura mala  → health -= DECAY_RATE     (capped a 0.0)

Color de la barra:
  health > 0.6  → verde
  health > 0.3  → amarillo
  health ≤ 0.3  → rojo
```

- La barra se dibuja en el lado izquierdo de la ventana, vertical.
- Da feedback visual inmediato sin necesidad de leer números.

### 6.7 `tray.py` — System tray (NUEVO)

**Clase `TrayIcon`**

```
TrayIcon
├── __init__(on_show, on_pause, on_quit)
├── start() -> None              # corre en thread separado
├── update_icon(is_good) -> None # cambia ícono verde/rojo
└── stop() -> None
```

**Menú del tray:**

```
PostureChecker ▼
├── Mostrar ventana
├── Pausar / Reanudar
├── Estadísticas
└── Salir
```

- Al minimizar la ventana de OpenCV (tecla M), se oculta y queda solo el tray icon.
- El ícono cambia de color según el estado: verde (ok) / rojo (mala postura).

### 6.8 `main.py` — Loop principal

```
main()
├── Inicializar Camera, PostureAnalyzer, PostureNotifier,
│   SessionStats, HealthBar, TrayIcon
│
├── Fase AUTO-CALIBRACIÓN (3 seg):
│   └── Mostrar countdown, recolectar frames, promediar → referencia
│
├── Fase MONITOREO (loop):
│   ├── Si pausado → mostrar "PAUSADO" en frame, skip análisis
│   ├── camera.read_frame()
│   ├── analyzer.analyze(frame) → result
│   ├── health_bar.update(result.is_good)
│   ├── session_stats.update(result.is_good)
│   ├── health_bar.draw(frame)
│   ├── analyzer.draw(frame, result) → frame anotado
│   ├── cv2.imshow(frame anotado)
│   │
│   ├── Si BAD_POSTURE_FRAMES alcanzado AND should_notify():
│   │   ├── severity = health_bar.get_severity()
│   │   └── notifier.notify(result.message, severity)
│   │
│   ├── Si should_break_remind():
│   │   └── notifier.break_remind()
│   │
│   ├── Tecla Q → break
│   ├── Tecla C → recalibrar
│   ├── Tecla P → toggle pausa
│   ├── Tecla B → reset break timer
│   └── Tecla M → minimizar a tray
│
├── Cleanup:
│   ├── session_stats.export_csv()
│   ├── camera.release()
│   ├── analyzer.close()
│   └── tray.stop()
```

---

## 7. Interfaz de usuario (ventana OpenCV)

```
┌─────────────────────────────────────────────────┐
│  POSTURA: ✓ OK          Sesión: 12:34  (82%)    │ ← Estado + stats
│  Fwd:0.42 Drop:1.21 ShW:0.38 Raise:0.55 T:-2.1 │ ← Métricas
│  Postura correcta                                │ ← Mensaje
│ ┌──┐                                            │
│ │▓▓│     ┌─────┐                                │
│ │▓▓│    ╱       ╲                               │
│ │▓▓│   │  👤    │  ← landmarks                  │
│ │▓▓│   │  /|\   │    superpuestos               │
│ │▓▓│   │  / \   │                               │
│ │▓▓│                                            │
│ │▓▓│  ← Barra de salud (verde/amarillo/rojo)    │
│ └──┘                                            │
│  [C] Calibrar [P] Pausa [B] Break [M] Min [Q] X │
└─────────────────────────────────────────────────┘
```

**Borde de la ventana:** cambia de color según severidad (verde → amarillo → rojo).

---

## 8. Flujo de ejecución

```
[Inicio]
   │
   ▼
Abrir webcam ──No──► [Error: "No se detecta cámara"]
   │ Sí
   ▼
┌─────────────────────────┐
│  AUTO-CALIBRACIÓN       │
│  "Sentate derecho..."   │
│  Countdown: 3...2...1   │
│  Recolectar 90 frames   │
│  Promediar → referencia │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LOOP MONITOREO                     │
│                                     │
│  ┌─ ¿Pausado? ─Sí─► Skip análisis  │
│  │       No                         │
│  ▼                                  │
│  Leer frame                         │
│  │                                  │
│  ▼                                  │
│  Extraer métricas                   │
│  │                                  │
│  ▼                                  │
│  Suavizar (promedio móvil)          │
│  │                                  │
│  ▼                                  │
│  Evaluar vs referencia              │
│  │                                  │
│  ├─► Actualizar HealthBar           │
│  ├─► Actualizar SessionStats        │
│  ├─► Dibujar overlay + barra        │
│  │                                  │
│  ├─ ¿Mala x10 frames + intervalo?   │
│  │    Sí → Beep(severidad) + Toast  │
│  │                                  │
│  ├─ ¿45 min sin break?              │
│  │    Sí → "Levantate y estirá"     │
│  │                                  │
│  ├─ Tecla Q → Exportar CSV → Fin   │
│  ├─ Tecla C → Recalibrar           │
│  ├─ Tecla P → Toggle pausa         │
│  ├─ Tecla B → Reset break timer    │
│  └─ Tecla M → Minimizar a tray     │
└─────────────────────────────────────┘
```

---

## 9. Estructura de archivos

```
posture-checker/
├── main.py                          # Entry point, loop, coordinación
├── capture.py                       # Captura de webcam
├── analyzer.py                      # Métricas + promedio móvil + evaluación
├── notifier.py                      # Beep escalable + toast + break remind
├── health_bar.py                    # Barra de salud postural
├── session_stats.py                 # Estadísticas + export CSV
├── tray.py                          # System tray icon
├── config.py                        # Constantes y umbrales
├── pose_landmarker_lite.task        # Modelo de MediaPipe
├── requirements.txt                 # Dependencias
├── session_log.csv                  # Log de sesiones (generado)
└── docs/
    ├── SDD_PostureChecker.md        # SDD v1.0
    └── SDD_PostureChecker_v2.md     # Este documento
```

---

## 10. Dependencias

```
opencv-python>=4.8
mediapipe>=0.10
plyer>=2.1
numpy>=1.24
pystray>=0.19
Pillow>=10.0
```

---

## 11. Controles del usuario

| Tecla | Acción |
|-------|--------|
| `Q` | Cerrar (exporta CSV automáticamente) |
| `C` | Recalibrar postura de referencia |
| `P` | Pausar / reanudar monitoreo |
| `B` | Resetear timer de break (tomé un descanso) |
| `M` | Minimizar a system tray |
