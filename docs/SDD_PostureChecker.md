# SDD — Especificación de Diseño Detallado
## Sistema de Corrección de Postura con OpenCV

---

## 1. Propósito

Sistema de escritorio que utiliza la webcam del usuario para analizar su postura en tiempo real mediante visión por computadora. Cada 3 minutos evalúa la postura y, si detecta una posición incorrecta, emite una notificación de escritorio con recomendaciones.

---

## 2. Alcance

| Incluido | Excluido |
|----------|----------|
| Captura de video en tiempo real | Almacenamiento de historial en DB |
| Detección de landmarks corporales | Múltiples usuarios simultáneos |
| Cálculo de ángulos posturales | Análisis de postura de pie |
| Notificaciones de escritorio | App móvil |
| Visualización de landmarks en ventana | Entrenamiento de modelo propio |
| Calibración de postura de referencia | — |

---

## 3. Tecnologías

| Componente | Tecnología | Justificación |
|-----------|------------|---------------|
| Captura de video | OpenCV (`cv2.VideoCapture`) | Acceso directo a webcam, procesamiento de frames |
| Detección de pose | MediaPipe Pose | 33 landmarks corporales, sin GPU, tiempo real |
| Notificaciones | `plyer` | Notificaciones nativas multiplataforma |
| UI | OpenCV `imshow` | Ventana simple sin framework adicional |
| Lenguaje | Python 3.10+ | — |

---

## 4. Arquitectura

```
┌─────────────────────────────────────────────────┐
│                    main.py                       │
│              (loop principal)                    │
├─────────────┬──────────────┬────────────────────┤
│  capture.py │  analyzer.py │  notifier.py       │
│  Captura de │  Análisis de │  Notificaciones    │
│  frames     │  postura     │  de escritorio     │
├─────────────┴──────────────┴────────────────────┤
│                  config.py                       │
│           (constantes y umbrales)                │
└─────────────────────────────────────────────────┘
        │                │
   [OpenCV]        [MediaPipe]
   [Webcam]        [Pose Model]
```

---

## 5. Diseño de Módulos

### 5.1 `config.py` — Configuración y umbrales

| Constante | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `CAMERA_INDEX` | `int` | `0` | Índice de la webcam |
| `CHECK_INTERVAL_SEC` | `int` | `180` | Intervalo de chequeo (3 min) |
| `NECK_ANGLE_THRESHOLD` | `float` | `25.0` | Ángulo máximo de inclinación del cuello antes de considerar mala postura |
| `SHOULDER_ANGLE_THRESHOLD` | `float` | `10.0` | Diferencia máxima entre alturas de hombros |
| `BAD_POSTURE_FRAMES` | `int` | `5` | Cantidad de frames consecutivos con mala postura para confirmar |

### 5.2 `capture.py` — Captura de video

**Clase `Camera`**

```
Camera
├── __init__(device_index: int)
├── read_frame() -> tuple[bool, np.ndarray]
├── is_opened() -> bool
└── release() -> None
```

- Encapsula `cv2.VideoCapture`.
- `read_frame()` devuelve `(success, frame)` en formato BGR.

### 5.3 `analyzer.py` — Análisis de postura

**Clase `PostureAnalyzer`**

```
PostureAnalyzer
├── __init__()
├── analyze(frame: np.ndarray) -> PostureResult
├── calibrate(frame: np.ndarray) -> bool
├── _calculate_neck_angle(landmarks) -> float
├── _calculate_shoulder_diff(landmarks) -> float
├── _draw_landmarks(frame, landmarks, result) -> np.ndarray
└── close() -> None
```

**Dataclass `PostureResult`**

```python
@dataclass
class PostureResult:
    is_good: bool              # True si la postura es correcta
    neck_angle: float          # Ángulo de inclinación del cuello (grados)
    shoulder_diff: float       # Diferencia de altura entre hombros (px normalizado)
    message: str               # Mensaje descriptivo del estado
    landmarks: list | None     # Landmarks detectados (para dibujar)
```

**Landmarks clave utilizados (MediaPipe Pose):**

| Landmark ID | Nombre | Uso |
|-------------|--------|-----|
| 0 | Nose | Referencia de posición de cabeza |
| 7 | Left ear | Cálculo de inclinación lateral |
| 8 | Right ear | Cálculo de inclinación lateral |
| 11 | Left shoulder | Alineación de hombros |
| 12 | Right shoulder | Alineación de hombros |

**Algoritmo de detección:**

1. Procesar frame con `mp.solutions.pose`.
2. Extraer landmarks 0, 7, 8, 11, 12.
3. Calcular **ángulo del cuello**: ángulo entre la línea nariz→punto medio de hombros y la vertical.
   - Si `neck_angle > NECK_ANGLE_THRESHOLD` → forward head posture.
4. Calcular **diferencia de hombros**: diferencia absoluta en coordenada Y entre hombro izq y der, normalizada.
   - Si `shoulder_diff > SHOULDER_ANGLE_THRESHOLD` → hombros desalineados.
5. Si cualquiera falla → `is_good = False`.

```
          Nariz (0)
            │
            │ ← ángulo vs vertical
            │
    ┌───────┼───────┐
  Hombro   Mid    Hombro
  Izq(11)  point  Der(12)
    │               │
    └── diff_y ─────┘
```

### 5.4 `notifier.py` — Notificaciones

**Clase `PostureNotifier`**

```
PostureNotifier
├── __init__(interval_sec: int)
├── should_notify() -> bool
├── notify(result: PostureResult) -> None
└── reset_timer() -> None
```

- `should_notify()`: devuelve `True` si pasaron al menos `interval_sec` desde la última notificación.
- `notify()`: usa `plyer.notification.notify()` para lanzar un toast de Windows con el mensaje del `PostureResult`.
- Evita spam: no notifica dos veces dentro del intervalo.

### 5.5 `main.py` — Loop principal

```
main()
├── Inicializar Camera, PostureAnalyzer, PostureNotifier
├── Loop:
│   ├── camera.read_frame()
│   ├── analyzer.analyze(frame)
│   ├── analyzer._draw_landmarks(frame, ...) → frame anotado
│   ├── cv2.imshow(frame anotado)
│   ├── Si notifier.should_notify() AND not result.is_good:
│   │   └── notifier.notify(result)
│   ├── Tecla 'q' → break
│   └── Tecla 'c' → analyzer.calibrate(frame)
├── Cleanup: camera.release(), analyzer.close()
```

---

## 6. Interfaz de usuario (ventana OpenCV)

```
┌──────────────────────────────────┐
│  POSTURA: ✓ CORRECTA             │ ← Verde si ok, Rojo si mal
│  Cuello: 12.3°  Hombros: 4.1°   │ ← Métricas en tiempo real
│                                   │
│         ┌─────┐                   │
│        ╱       ╲                  │
│       │  👤    │  ← landmarks    │
│       │  /|\   │    dibujados     │
│       │  / \   │    sobre el      │
│                                   │
│  [C] Calibrar  [Q] Salir         │ ← Controles
└──────────────────────────────────┘
```

- **Barra superior**: estado actual (verde/rojo) + métricas numéricas.
- **Centro**: video de la webcam con landmarks de MediaPipe superpuestos.
- **Líneas de referencia**: línea vertical desde nariz a punto medio de hombros.
- **Barra inferior**: teclas disponibles.

---

## 7. Flujo de ejecución

```
[Inicio]
   │
   ▼
Abrir webcam ──No──► [Error: "No se detecta cámara"]
   │ Sí
   ▼
Mostrar ventana con video
   │
   ▼
┌──────────────────────┐
│  Loop cada frame:    │
│  1. Leer frame       │
│  2. Detectar pose    │◄─────────────────┐
│  3. Calcular ángulos │                  │
│  4. Dibujar overlay  │                  │
│  5. Mostrar frame    │                  │
│  6. ¿Pasaron 3 min?  │                  │
│     │ Sí      │ No   │                  │
│     ▼         └──────┼──────────────────┘
│  ¿Postura mala?      │
│     │ Sí      │ No   │
│     ▼         └──────┼──────────────────┘
│  Notificar()         │
│     │                │
│     └────────────────┼──────────────────┘
│                      │
│  ¿Tecla 'q'?        │
│     │ Sí             │
│     ▼                │
│  [Fin]               │
└──────────────────────┘
```

---

## 8. Estructura de archivos

```
posture-checker/
├── main.py               # Entry point y loop principal
├── capture.py            # Captura de webcam
├── analyzer.py           # Análisis de postura con MediaPipe
├── notifier.py           # Notificaciones de escritorio
├── config.py             # Constantes y umbrales
├── requirements.txt      # Dependencias
└── docs/
    └── SDD_PostureChecker.md   # Este documento
```

---

## 9. Dependencias

```
opencv-python>=4.8
mediapipe>=0.10
plyer>=2.1
numpy>=1.24
```

---

## 10. Controles del usuario

| Tecla | Acción |
|-------|--------|
| `Q` | Cerrar la aplicación |
| `C` | Calibrar postura de referencia (sentarse derecho y presionar) |
