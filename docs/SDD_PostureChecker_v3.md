# SDD v3.0 — Especificacion de Diseno Detallado
## PostureChecker: Interfaz macOS-style con CustomTkinter

---

## 1. Proposito

Rediseno completo de la interfaz grafica de PostureChecker, migrando de la ventana basica de OpenCV (`imshow`) a una aplicacion de escritorio moderna con estetica inspirada en macOS. Se utiliza **CustomTkinter** como framework de UI, manteniendo intacto el motor de analisis postural (MediaPipe + OpenCV para procesamiento). El resultado es una app que se siente nativa, profesional y agradable de usar durante sesiones largas de trabajo.

---

## 2. Alcance

| Incluido (v3.0) | Excluido |
|------------------|----------|
| Migracion completa de UI a CustomTkinter | Almacenamiento en DB |
| Diseno visual estilo macOS (dark/light mode) | Multiples usuarios simultaneos |
| Dashboard con metricas en tiempo real | App movil |
| Panel de configuracion con sliders interactivos | Analisis de postura de pie |
| Historial de sesiones con graficos | Entrenamiento de modelo propio |
| Sistema de temas (dark/light) | Integracion con servicios cloud |
| Persistencia de preferencias en JSON | --- |
| Animaciones y transiciones suaves | --- |
| Todas las funcionalidades de v2.0 | --- |

---

## 3. Cambios respecto a v2.0

| Area | v2.0 | v3.0 |
|------|------|------|
| Framework UI | OpenCV `imshow` (primitiva) | CustomTkinter (moderna, nativa) |
| Apariencia | Texto sobre video, borde coloreado | Paneles glassmorphism, tarjetas, sidebar |
| Navegacion | Teclas del teclado unicamente | Sidebar + tabs + botones + atajos |
| Health bar | Barra vertical basica dibujada con cv2 | Indicador circular animado con gradiente |
| Configuracion | Constantes en `config.py` (hardcoded) | Panel interactivo con sliders + JSON persistente |
| Historial | CSV crudo exportado al cerrar | Vista de historial con graficos integrados |
| Tema | Solo oscuro (fondo de video) | Dark/Light mode toggle |
| Calibracion | Overlay sobre video con countdown | Modal dedicado con animacion y guia visual |
| Estadisticas | Toast del system tray | Dashboard con tarjetas de stats en vivo |
| Notificaciones | Toast de Windows + winsound | In-app toasts estilizados + sonido + toast OS |
| Layout | Ventana unica con todo superpuesto | Layout multi-panel: sidebar + area principal |
| Responsividad | Tamano fijo | Redimensionable con layout adaptativo |

---

## 4. Tecnologias

| Componente | Tecnologia | Justificacion |
|-----------|------------|---------------|
| Framework UI | **CustomTkinter** | Widgets modernos con apariencia macOS, dark/light mode nativo, sin dependencias pesadas |
| Renderizado video | OpenCV -> PIL -> CTkLabel | Conversion de frames a PhotoImage para mostrar en widget Tkinter |
| Deteccion de pose | MediaPipe Pose (Tasks API) | Sin cambios: 33 landmarks, sin GPU, tiempo real |
| Graficos/Charts | **matplotlib** (embebido) | Graficos de historial de sesiones dentro de la app |
| Iconos | **Pillow** | Generacion de iconos y assets dinamicos |
| Notificaciones OS | `plyer` | Toast nativo de Windows (complementa in-app toasts) |
| Sonido | `winsound` | Beep nativo sin dependencias |
| System tray | `pystray` + `Pillow` | Icono en bandeja del sistema |
| Persistencia config | JSON (`json` stdlib) | Preferencias del usuario persistentes |
| Persistencia stats | CSV (`csv` stdlib) | Compatibilidad con v2.0 |
| Lenguaje | Python 3.10+ | --- |

---

## 5. Sistema de Diseno

### 5.1 Filosofia visual

La interfaz sigue los principios de diseno de macOS:

- **Claridad**: contenido legible con jerarquia visual clara
- **Profundidad**: capas visuales con sombras sutiles y transparencias
- **Minimalismo**: solo mostrar lo necesario, sin ruido visual
- **Consistencia**: componentes uniformes en toda la app

### 5.2 Paleta de colores

**Dark Mode (default):**

| Elemento | Color | Hex |
|----------|-------|-----|
| Background principal | Gris oscuro profundo | `#1E1E1E` |
| Sidebar background | Gris mas oscuro | `#171717` |
| Card background | Gris elevado | `#2A2A2A` |
| Card hover | Gris claro | `#333333` |
| Texto primario | Blanco | `#FFFFFF` |
| Texto secundario | Gris claro | `#A0A0A0` |
| Acento principal | Azul macOS | `#007AFF` |
| Acento success | Verde | `#30D158` |
| Acento warning | Amarillo | `#FFD60A` |
| Acento danger | Rojo | `#FF453A` |
| Borde sutil | Gris | `#3A3A3A` |
| Divider | Gris tenue | `#2C2C2C` |

**Light Mode:**

| Elemento | Color | Hex |
|----------|-------|-----|
| Background principal | Blanco hueso | `#F5F5F7` |
| Sidebar background | Gris claro | `#E8E8ED` |
| Card background | Blanco | `#FFFFFF` |
| Card hover | Gris muy claro | `#F0F0F0` |
| Texto primario | Negro | `#1D1D1F` |
| Texto secundario | Gris | `#86868B` |
| Acento principal | Azul macOS | `#007AFF` |
| Acento success | Verde | `#34C759` |
| Acento warning | Naranja | `#FF9F0A` |
| Acento danger | Rojo | `#FF3B30` |
| Borde sutil | Gris claro | `#D2D2D7` |
| Divider | Gris | `#E5E5EA` |

### 5.3 Tipografia

| Uso | Font | Tamano | Peso |
|-----|------|--------|------|
| Titulo de seccion | Segoe UI / SF Pro | 24px | Bold |
| Subtitulo | Segoe UI | 18px | Semibold |
| Texto body | Segoe UI | 14px | Regular |
| Label de stat | Segoe UI | 12px | Regular |
| Valor de stat | Segoe UI | 28px | Bold |
| Caption/hint | Segoe UI | 11px | Regular |
| Monospace (metricas) | Cascadia Code / Consolas | 12px | Regular |

### 5.4 Componentes de diseno

**Tarjetas (Cards):**
- Border radius: 12px
- Padding interno: 16px
- Sombra sutil: 0 2px 8px rgba(0,0,0,0.1)
- Transicion hover: 150ms ease

**Botones:**
- Primario: fondo azul `#007AFF`, texto blanco, radius 8px
- Secundario: fondo transparente, borde gris, texto gris
- Danger: fondo rojo `#FF453A`, texto blanco
- Hover: opacity 0.85
- Alto: 36px

**Sidebar items:**
- Alto: 40px
- Padding: 12px horizontal
- Icono + texto
- Estado activo: fondo azul translucido + texto blanco
- Hover: fondo gris translucido

**Indicador circular de salud:**
- Diametro: 120px
- Grosor del arco: 8px
- Gradiente: verde -> amarillo -> rojo segun health
- Porcentaje centrado en texto bold 28px
- Animacion suave al cambiar valor (interpolacion)

---

## 6. Arquitectura

### 6.1 Diagrama de modulos

```
posture-checker/
├── main.py                          # Entry point
├── app.py                           # CTkApp principal + coordinacion
│
├── ui/                              # Capa de presentacion
│   ├── __init__.py
│   ├── theme.py                     # Sistema de temas (dark/light)
│   ├── sidebar.py                   # Sidebar de navegacion
│   ├── views/
│   │   ├── __init__.py
│   │   ├── monitor_view.py          # Vista principal: video + health
│   │   ├── dashboard_view.py        # Vista de dashboard con stats
│   │   ├── settings_view.py         # Vista de configuracion
│   │   └── history_view.py          # Vista de historial de sesiones
│   └── components/
│       ├── __init__.py
│       ├── health_ring.py           # Indicador circular de salud
│       ├── stat_card.py             # Tarjeta de estadistica
│       ├── video_panel.py           # Panel de video con overlay
│       ├── toast.py                 # Notificaciones in-app
│       ├── calibration_modal.py     # Modal de calibracion
│       └── metric_badge.py          # Badge individual de metrica
│
├── core/                            # Logica de negocio (sin cambios mayores)
│   ├── __init__.py
│   ├── capture.py                   # Captura de webcam (= v2.0)
│   ├── analyzer.py                  # Analisis postural (= v2.0)
│   ├── notifier.py                  # Alertas sonoras + toast OS
│   ├── health_bar.py                # Logica de salud (sin draw)
│   └── session_stats.py             # Estadisticas + CSV
│
├── config/
│   ├── __init__.py
│   ├── defaults.py                  # Constantes default (ex config.py)
│   ├── settings.py                  # Clase Settings (lee/escribe JSON)
│   └── user_settings.json           # Preferencias del usuario (generado)
│
├── assets/
│   ├── icons/                       # Iconos SVG/PNG para sidebar y UI
│   │   ├── monitor.png
│   │   ├── dashboard.png
│   │   ├── settings.png
│   │   ├── history.png
│   │   ├── pause.png
│   │   ├── play.png
│   │   ├── calibrate.png
│   │   └── app_icon.png
│   └── fonts/                       # Fuentes custom (opcional)
│
├── tray.py                          # System tray (= v2.0)
├── pose_landmarker_lite.task        # Modelo MediaPipe
├── requirements.txt                 # Dependencias actualizadas
├── session_log.csv                  # Log de sesiones (generado)
└── docs/
    ├── SDD_PostureChecker.md
    ├── SDD_PostureChecker_v2.md
    └── SDD_PostureChecker_v3.md     # Este documento
```

### 6.2 Diagrama de capas

```
┌───────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACION                       │
│                                                                   │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐   │
│  │         │  │              Area Principal                   │   │
│  │         │  │  ┌──────────────────────────────────────┐    │   │
│  │ Sidebar │  │  │ MonitorView / DashboardView /        │    │   │
│  │         │  │  │ SettingsView / HistoryView            │    │   │
│  │  - Mon  │  │  │                                       │    │   │
│  │  - Dash │  │  │  Compuesto por Components:            │    │   │
│  │  - Conf │  │  │  VideoPanel, HealthRing, StatCard,    │    │   │
│  │  - Hist │  │  │  MetricBadge, Toast, etc.             │    │   │
│  │         │  │  └──────────────────────────────────────┘    │   │
│  └─────────┘  └──────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────────────┤
│                      CAPA DE COORDINACION                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ app.py — PostureCheckerApp                                 │   │
│  │ Coordina UI <-> Core, maneja eventos, gestiona estado      │   │
│  └────────────────────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────────────┤
│                        CAPA DE NEGOCIO                            │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐      │
│  │ capture  │ │ analyzer │ │ notifier │ │ session_stats  │      │
│  │ .py      │ │ .py      │ │ .py      │ │ .py            │      │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘      │
│  ┌──────────┐ ┌──────────────────────┐                           │
│  │health_bar│ │ config/settings.py   │                           │
│  │ .py      │ │ (persistencia JSON)  │                           │
│  └──────────┘ └──────────────────────┘                           │
├───────────────────────────────────────────────────────────────────┤
│                      CAPA EXTERNA                                 │
│                                                                   │
│  [OpenCV]  [MediaPipe]  [pystray]  [matplotlib]  [CustomTkinter] │
│  [Webcam]  [Pose Model] [Pillow]   [winsound]    [plyer]         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 7. Diseno de Modulos

### 7.1 `main.py` — Entry point

```python
# Minimo: solo crea la app y ejecuta
import customtkinter as ctk
from app import PostureCheckerApp

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = PostureCheckerApp()
    app.mainloop()
```

### 7.2 `app.py` — Coordinador principal

```
PostureCheckerApp(ctk.CTk)
├── __init__()
│   ├── Configura ventana (titulo, tamano, icono)
│   ├── Inicializa core: Camera, PostureAnalyzer, Notifier, Stats, HealthBar
│   ├── Inicializa settings: Settings (carga JSON)
│   ├── Crea layout: Sidebar + content area
│   ├── Registra vistas: monitor, dashboard, settings, history
│   ├── Inicia tray icon en thread
│   └── Lanza auto-calibracion
│
├── _setup_window()
│   ├── geometry("1200x750")
│   ├── minsize(900, 600)
│   ├── title("PostureChecker")
│   └── protocol("WM_DELETE_WINDOW", _on_close)
│
├── _create_layout()
│   ├── sidebar_frame (izquierda, ancho fijo 220px)
│   └── content_frame (derecha, expandible)
│
├── show_view(view_name: str) -> None
│   # Oculta la vista actual, muestra la nueva
│
├── _start_monitoring_loop() -> None
│   # Loop principal con self.after(33, ...) para ~30fps
│   # Lee frame, analiza, actualiza UI
│
├── _process_frame() -> None
│   # Un ciclo del loop:
│   # 1. camera.read_frame()
│   # 2. analyzer.analyze(frame)
│   # 3. health_bar.update(result.is_good)
│   # 4. session_stats.update(result.is_good)
│   # 5. Actualizar video_panel, health_ring, stat_cards
│   # 6. Verificar alertas
│   # 7. Programar siguiente frame con self.after()
│
├── toggle_pause() -> None
├── recalibrate() -> None
├── toggle_theme() -> None
├── _on_close() -> None
│   # Export CSV, release camera, stop tray, destroy
│
├── _update_from_settings(key, value) -> None
│   # Callback cuando el usuario cambia un setting
│
└── state: AppState
    ├── is_paused: bool
    ├── is_calibrated: bool
    ├── is_calibrating: bool
    ├── is_minimized: bool
    ├── current_view: str
    └── current_health: float
```

**Loop de monitoreo con Tkinter:**

A diferencia de v2.0 que usaba un `while True` con `cv2.waitKey()`, v3.0 usa el event loop de Tkinter con `self.after()`:

```
self.after(33, self._process_frame)   # ~30fps
```

Esto permite que la UI sea responsive mientras se procesan frames.

### 7.3 `ui/theme.py` — Sistema de temas

```
Theme
├── current: str                          # "dark" | "light"
├── colors: dict                          # Paleta activa
│
├── get_color(name: str) -> str           # Obtener color por nombre
├── toggle() -> None                      # Cambiar dark <-> light
├── apply(widget: CTkBaseClass) -> None   # Aplicar tema a widget
│
└── PALETTES: dict[str, dict]             # dark y light palettes
```

**Colores accesibles como:**
```python
theme.get_color("bg_primary")      # "#1E1E1E" en dark
theme.get_color("accent")          # "#007AFF"
theme.get_color("success")         # "#30D158" en dark
theme.get_color("text_primary")    # "#FFFFFF" en dark
```

### 7.4 `ui/sidebar.py` — Navegacion lateral

```
Sidebar(ctk.CTkFrame)
├── __init__(master, on_navigate: Callable)
│
├── items:
│   ├── ("Monitor",    monitor.png,    "monitor")
│   ├── ("Dashboard",  dashboard.png,  "dashboard")
│   ├── ("Ajustes",    settings.png,   "settings")
│   └── ("Historial",  history.png,    "history")
│
├── _create_nav_button(text, icon, view_name) -> CTkButton
├── set_active(view_name: str) -> None
│
├── --- (separator) ---
│
├── pause_button: CTkButton              # Pausar / Reanudar
├── calibrate_button: CTkButton          # Recalibrar
├── theme_toggle: CTkSwitch              # Dark / Light mode
│
├── --- (separator) ---
│
└── app_info: CTkLabel                   # "PostureChecker v3.0"
```

**Layout visual del sidebar:**

```
┌──────────────┐
│  PC          │  <- Logo/nombre
│  PostureCheck │
│              │
│ ● Monitor   │  <- Activo (highlighted)
│   Dashboard  │
│   Ajustes    │
│   Historial  │
│              │
│ ─────────── │
│              │
│ ▶ Pausar    │
│ ◎ Calibrar  │
│              │
│ ─────────── │
│              │
│ 🌙 Tema     │  <- Switch dark/light
│              │
│ v3.0        │
└──────────────┘
```

### 7.5 `ui/views/monitor_view.py` — Vista principal

La vista mas importante. Muestra el video en vivo con el analisis superpuesto.

```
MonitorView(ctk.CTkFrame)
├── __init__(master, app_ref)
│
├── Layout (grid 2 columnas):
│   │
│   ├── Columna izquierda (70% ancho):
│   │   └── VideoPanel
│   │       ├── Video en vivo con landmarks
│   │       ├── Overlay de estado (sutil, esquina superior)
│   │       └── Indicadores de problemas detectados
│   │
│   └── Columna derecha (30% ancho):
│       ├── HealthRing (indicador circular grande)
│       ├── Estado: "Postura correcta" / "Corregir postura"
│       ├── MetricBadges (6 metricas individuales)
│       │   ├── Cabeza adelante
│       │   ├── Encorvado (cabeza)
│       │   ├── Hombros adelante
│       │   ├── Hombros tensos
│       │   ├── Cabeza inclinada
│       │   └── Descentrado
│       └── Info de sesion (tiempo, % bueno)
│
├── update_frame(frame: np.ndarray, result: PostureResult) -> None
├── update_health(health: float) -> None
├── update_metrics(metrics: PostureMetrics, problems: list) -> None
└── show_calibration_overlay(progress: float) -> None
```

**Layout visual:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌───────────────────────────────┐  ┌────────────────────┐ │
│  │                               │  │                    │ │
│  │                               │  │    ┌──────────┐    │ │
│  │                               │  │    │          │    │ │
│  │         VIDEO EN VIVO         │  │    │   82%    │    │ │
│  │       (con landmarks)         │  │    │          │    │ │
│  │                               │  │    └──────────┘    │ │
│  │                               │  │   Health Ring      │ │
│  │                               │  │                    │ │
│  │                               │  │  ✓ Postura OK      │ │
│  │  ┌─────────────────────────┐  │  │                    │ │
│  │  │ POSTURA OK    12:34 min │  │  │  ┌──┐ Fwd    OK   │ │
│  │  └─────────────────────────┘  │  │  ┌──┐ Drop   OK   │ │
│  └───────────────────────────────┘  │  ┌──┐ ShW    OK   │ │
│                                      │  ┌──┐ Raise  !!   │ │
│                                      │  ┌──┐ Tilt   OK   │ │
│                                      │  ┌──┐ Lat    OK   │ │
│                                      │                    │ │
│                                      │  Sesion: 34 min    │ │
│                                      │  Buenos: 78%       │ │
│                                      └────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 7.6 `ui/views/dashboard_view.py` — Dashboard de estadisticas

```
DashboardView(ctk.CTkFrame)
├── __init__(master, app_ref)
│
├── Layout (grid):
│   │
│   ├── Fila 1: Tarjetas de stats (4 columnas)
│   │   ├── StatCard("Tiempo de sesion", "34 min", icon=clock)
│   │   ├── StatCard("Postura buena", "78%", icon=check, color=green)
│   │   ├── StatCard("Alertas", "5", icon=bell, color=yellow)
│   │   └── StatCard("Breaks", "2", icon=coffee, color=blue)
│   │
│   ├── Fila 2: Grafico de sesion actual (ancho completo)
│   │   └── matplotlib chart embebido
│   │       Linea temporal: health% a lo largo del tiempo
│   │
│   └── Fila 3: Desglose de problemas (ancho completo)
│       └── Barras horizontales mostrando frecuencia de cada problema
│
├── update_stats(summary: SessionSummary) -> None
├── update_health_history(history: list[float]) -> None
└── refresh() -> None
```

**Layout visual:**

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                                  │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ ⏱ Sesion │ │ ✓ Buena  │ │ 🔔 Alert │ │ ☕ Breaks│      │
│  │  34 min  │ │   78%    │ │    5     │ │    2     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Salud postural durante la sesion                    │   │
│  │  100%|     ___                                       │   │
│  │   80%|____/   \___      ____                         │   │
│  │   60%|            \____/    \___                      │   │
│  │   40%|                          \__                   │   │
│  │   20%|                                                │   │
│  │    0%|____________________________________________   │   │
│  │      0    5    10   15   20   25   30   34 min       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Problemas detectados                                │   │
│  │  Cabeza adelante    ████████░░░░░░  45%              │   │
│  │  Encorvado          ██████░░░░░░░░  32%              │   │
│  │  Hombros tensos     ████░░░░░░░░░░  18%              │   │
│  │  Cabeza inclinada   ██░░░░░░░░░░░░   5%              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7.7 `ui/views/settings_view.py` — Panel de configuracion

```
SettingsView(ctk.CTkFrame)
├── __init__(master, settings: Settings, on_change: Callable)
│
├── Secciones:
│   │
│   ├── "Camara"
│   │   └── Slider: Indice de camara (0-4)
│   │
│   ├── "Sensibilidad de deteccion"
│   │   ├── Slider: Cabeza adelante (0.05 - 0.30, default 0.15)
│   │   ├── Slider: Caida de cabeza (0.05 - 0.25, default 0.12)
│   │   ├── Slider: Hombros adelante (0.03 - 0.15, default 0.08)
│   │   ├── Slider: Hombros tensos (0.05 - 0.20, default 0.10)
│   │   ├── Slider: Inclinacion cabeza (3.0 - 15.0, default 8.0)
│   │   └── Slider: Inclinacion lateral (0.05 - 0.25, default 0.12)
│   │
│   ├── "Alertas"
│   │   ├── Slider: Intervalo entre alertas (60 - 600 seg)
│   │   ├── Slider: Frames consecutivos (5 - 30)
│   │   ├── Switch: Sonido habilitado (on/off)
│   │   └── Switch: Notificaciones del sistema (on/off)
│   │
│   ├── "Salud postural"
│   │   ├── Slider: Velocidad de deterioro (0.005 - 0.05)
│   │   └── Slider: Velocidad de recuperacion (0.005 - 0.03)
│   │
│   ├── "Descansos"
│   │   ├── Slider: Intervalo de break (15 - 90 min)
│   │   └── Switch: Recordatorio de break (on/off)
│   │
│   └── "Apariencia"
│       ├── SegmentedButton: Tema (Oscuro / Claro / Sistema)
│       └── Slider: Suavizado (5 - 30 frames)
│
├── _on_slider_change(key, value) -> None
├── _on_switch_change(key, value) -> None
├── reset_defaults() -> None               # Boton "Restaurar defaults"
└── _save() -> None                        # Auto-save al cambiar
```

**Layout visual:**

```
┌─────────────────────────────────────────────────────────────┐
│  Ajustes                                                    │
│                                                             │
│  Sensibilidad de deteccion                                  │
│  ─────────────────────────────────────────                  │
│  Cabeza adelante         ──●──────────  0.15                │
│  Caida de cabeza         ────●────────  0.12                │
│  Hombros adelante        ──────●──────  0.08                │
│  Hombros tensos          ────●────────  0.10                │
│  Inclinacion cabeza      ────────●────  8.0°                │
│  Inclinacion lateral     ────●────────  0.12                │
│                                                             │
│  Alertas                                                    │
│  ─────────────────────────────────────────                  │
│  Intervalo (seg)         ──────●──────  180                 │
│  Frames consecutivos     ────●────────  10                  │
│  Sonido                  [========●]   ON                   │
│  Notificaciones          [========●]   ON                   │
│                                                             │
│  Apariencia                                                 │
│  ─────────────────────────────────────────                  │
│  Tema       [ Oscuro | Claro | Sistema ]                    │
│                                                             │
│                              [ Restaurar defaults ]          │
└─────────────────────────────────────────────────────────────┘
```

### 7.8 `ui/views/history_view.py` — Historial de sesiones

```
HistoryView(ctk.CTkFrame)
├── __init__(master, csv_path: str)
│
├── Layout:
│   ├── Header: "Historial de sesiones" + boton "Exportar CSV"
│   │
│   ├── Grafico de resumen (matplotlib embebido):
│   │   └── Barras: % postura buena por sesion (ultimas 14 sesiones)
│   │
│   └── Tabla scrolleable:
│       ├── Columnas: Fecha | Inicio | Duracion | % Buena | Alertas | Breaks
│       └── Filas: cada sesion del CSV
│
├── _load_history() -> list[dict]
├── refresh() -> None
└── export_csv() -> None
```

**Layout visual:**

```
┌─────────────────────────────────────────────────────────────┐
│  Historial                              [ Exportar CSV ]    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Postura buena por sesion (ultimas 14)              │   │
│  │  100%|  █                █                           │   │
│  │   80%|  █  █  █     █    █  █     █                  │   │
│  │   60%|  █  █  █  █  █    █  █  █  █  █               │   │
│  │   40%|  █  █  █  █  █  █ █  █  █  █  █  █            │   │
│  │   20%|  █  █  █  █  █  █ █  █  █  █  █  █  █  █     │   │
│  │    0%|__|__|__|__|__|__|_|__|__|__|__|__|__|__|       │   │
│  │      21  22  23  24  25 26 27  28  29  30 31  1  2  3│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Fecha      │ Inicio │ Duracion │ Buena │ Alert │ Brk│   │
│  │────────────│────────│──────────│───────│───────│────│   │
│  │ 2026-06-03 │ 14:30  │  45 min  │  78%  │   5   │ 2 │   │
│  │ 2026-06-02 │ 09:15  │  62 min  │  85%  │   3   │ 3 │   │
│  │ 2026-06-01 │ 16:00  │  30 min  │  65%  │   8   │ 1 │   │
│  │ ...        │ ...    │  ...     │  ...  │  ...  │...│   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7.9 `ui/components/` — Componentes reutilizables

#### 7.9.1 `video_panel.py`

```
VideoPanel(ctk.CTkFrame)
├── __init__(master, width, height)
├── canvas: CTkLabel                     # Label que muestra la imagen
│
├── update_frame(frame: np.ndarray) -> None
│   # 1. cv2.cvtColor(frame, BGR2RGB)
│   # 2. PIL.Image.fromarray(rgb)
│   # 3. CTkImage(pil_image)
│   # 4. canvas.configure(image=ctk_image)
│
├── show_overlay(text: str, color: str) -> None
│   # Overlay semitransparente sobre el video
│
└── show_no_camera() -> None
    # Placeholder cuando no hay camara
```

**Conversion de frame OpenCV a Tkinter:**

```
OpenCV frame (BGR, numpy)
        │
        ▼
cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        │
        ▼
PIL.Image.fromarray(rgb_frame)
        │
        ▼
PIL.Image.resize((panel_width, panel_height))
        │
        ▼
CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
        │
        ▼
label.configure(image=ctk_image)
```

#### 7.9.2 `health_ring.py`

```
HealthRing(ctk.CTkCanvas)
├── __init__(master, size=120, thickness=8)
│
├── _draw_ring(health: float) -> None
│   # 1. Dibujar arco de fondo (gris)
│   # 2. Dibujar arco de progreso (coloreado segun health)
│   # 3. Dibujar texto del porcentaje centrado
│   # 4. Color del arco:
│   #    health > 0.6 → verde
│   #    health > 0.3 → amarillo
│   #    health <= 0.3 → rojo
│
├── update(health: float) -> None
│   # Interpolar del valor actual al nuevo (animacion suave)
│   # self.after(16, ...) para ~60fps de animacion
│
├── _interpolate(current, target, speed=0.1) -> float
│
└── _get_color(health: float) -> str
```

**Renderizado del anillo:**

```
    ┌───────────────┐
    │  ╭─────────╮  │
    │ ╭╯ ███████ ╰╮ │   █ = arco coloreado (progreso)
    │ │           │ │   ░ = arco de fondo (gris)
    │ │   82 %    │ │
    │ │           │ │
    │ ╰╮ ░░░░░░ ╭╯ │
    │  ╰─────────╯  │
    └───────────────┘
```

El arco empieza desde arriba (90 grados) y avanza en sentido horario. El extent es `health * 360`.

#### 7.9.3 `stat_card.py`

```
StatCard(ctk.CTkFrame)
├── __init__(master, title: str, value: str, icon: str = None,
│            accent_color: str = None)
│
├── icon_label: CTkLabel
├── title_label: CTkLabel        # "Postura buena"
├── value_label: CTkLabel        # "78%"
│
├── update_value(value: str) -> None
└── set_accent(color: str) -> None
```

#### 7.9.4 `toast.py`

```
ToastNotification
├── __init__(master: CTk)
│
├── show(message: str, type: str = "info", duration: int = 3000) -> None
│   # type: "info" | "success" | "warning" | "error"
│   # Crea un CTkFrame flotante en la esquina superior derecha
│   # Auto-dismiss despues de `duration` ms
│   # Animacion: slide-in desde arriba
│
├── _create_toast_widget(message, type) -> CTkFrame
├── _animate_in(widget) -> None
├── _animate_out(widget) -> None
└── _dismiss(widget) -> None
```

**Aparicion visual:**

```
                    ┌───────────────────────┐
                    │ ⚠ Corregir postura    │  <- toast warning
                    │   Cabeza adelante     │
                    └───────────────────────┘
┌─────────────────────────────────────────────┐
│                                             │
│          (contenido de la app)              │
│                                             │
```

#### 7.9.5 `calibration_modal.py`

```
CalibrationModal(ctk.CTkToplevel)
├── __init__(master, on_complete: Callable)
│
├── Layout:
│   ├── Titulo: "Calibracion"
│   ├── Instruccion: "Senta derecho y mira a la camara"
│   ├── Preview de video (pequeno)
│   ├── Barra de progreso (CTkProgressBar)
│   ├── Texto de progreso: "Calibrando... 67%"
│   └── Boton "Cancelar"
│
├── update_progress(progress: float) -> None
├── show_success() -> None
│   # Muestra checkmark, cierra despues de 1 seg
│
└── show_error(message: str) -> None
```

#### 7.9.6 `metric_badge.py`

```
MetricBadge(ctk.CTkFrame)
├── __init__(master, name: str, threshold: float)
│
├── Layout:
│   ├── indicator: CTkLabel (circulo verde/rojo)
│   ├── name_label: CTkLabel ("Cabeza adelante")
│   └── value_label: CTkLabel ("0.12")
│
├── update(value: float, is_ok: bool) -> None
│   # Cambia color del indicador y valor
│
└── _animate_alert() -> None
    # Flash rojo cuando detecta problema
```

### 7.10 `config/settings.py` — Persistencia de configuracion

```
Settings
├── __init__(path: str = "config/user_settings.json")
│
├── _defaults: dict                      # Valores de defaults.py
├── _user: dict                          # Valores del usuario (JSON)
│
├── get(key: str) -> Any
│   # Retorna user[key] si existe, sino defaults[key]
│
├── set(key: str, value: Any) -> None
│   # Guarda en _user y persiste a JSON
│
├── reset(key: str = None) -> None
│   # key=None reseta todo, sino solo esa clave
│
├── load() -> None
│   # Lee user_settings.json
│
├── save() -> None
│   # Escribe user_settings.json
│
└── as_dict() -> dict
    # Merge de defaults + user
```

**Formato del JSON:**

```json
{
    "camera_index": 0,
    "forward_lean_threshold": 0.15,
    "slouch_drop_threshold": 0.12,
    "slouch_shoulder_threshold": 0.08,
    "shoulder_raise_threshold": 0.10,
    "head_tilt_threshold": 8.0,
    "lateral_lean_threshold": 0.12,
    "check_interval_sec": 180,
    "bad_posture_frames": 10,
    "health_decay_rate": 0.02,
    "health_recovery_rate": 0.01,
    "break_interval_min": 45,
    "sound_enabled": true,
    "notifications_enabled": true,
    "break_reminder_enabled": true,
    "smoothing_window": 15,
    "theme": "dark"
}
```

### 7.11 Modulos core (sin cambios mayores)

Los siguientes modulos se mueven a `core/` pero su logica interna no cambia:

| Modulo | Cambio |
|--------|--------|
| `core/capture.py` | Igual que v2.0 |
| `core/analyzer.py` | Igual que v2.0 (se separa draw() a la capa UI) |
| `core/notifier.py` | Igual que v2.0, agrega callback para in-app toast |
| `core/health_bar.py` | Se elimina `draw()`, solo mantiene logica |
| `core/session_stats.py` | Igual que v2.0 |

**Cambio clave en `analyzer.py`:**

El metodo `draw()` que dibujaba landmarks sobre el frame con OpenCV se mantiene para el overlay del video, pero el renderizado de la UI (barra de salud, textos, bordes) se mueve completamente a los componentes de CustomTkinter.

---

## 8. Flujo de ejecucion v3.0

```
[Inicio]
   │
   ▼
Crear CTk window (1200x750)
   │
   ▼
Cargar Settings (JSON)
   │
   ▼
Inicializar core modules
(Camera, Analyzer, Notifier, Stats, HealthBar)
   │
   ▼
Crear layout: Sidebar + Content
   │
   ▼
Registrar vistas: Monitor, Dashboard, Settings, History
   │
   ▼
Mostrar CalibrationModal
   │
   ├── Recolectar 90 frames con preview
   ├── Mostrar progreso animado
   ├── Promediar → referencia
   └── Cerrar modal → "Calibracion exitosa"
   │
   ▼
Iniciar tray icon (thread)
   │
   ▼
Mostrar MonitorView (default)
   │
   ▼
┌──────────────────────────────────────────────┐
│  LOOP PRINCIPAL (self.after ~30fps)          │
│                                              │
│  ┌─ ¿Pausado? ─Si─► Mostrar overlay pausa   │
│  │       No                                  │
│  ▼                                           │
│  camera.read_frame()                         │
│  │                                           │
│  ▼                                           │
│  analyzer.analyze(frame) → result            │
│  │                                           │
│  ▼                                           │
│  analyzer.draw(frame, result) → frame_drawn  │
│  │                                           │
│  ├──► health_bar.update(is_good)             │
│  ├──► session_stats.update(is_good)          │
│  │                                           │
│  ▼                                           │
│  Actualizar UI (si MonitorView activa):      │
│  ├──► video_panel.update_frame(frame_drawn)  │
│  ├──► health_ring.update(health)             │
│  ├──► metric_badges.update(metrics)          │
│  └──► stat_labels.update(stats)              │
│                                              │
│  ¿Mala postura x10 + intervalo?              │
│     Si → notifier.notify(severity)           │
│          toast.show(message, "warning")       │
│                                              │
│  ¿Break reminder?                            │
│     Si → toast.show("Toma un descanso")      │
│                                              │
│  self.after(33, _process_frame)              │
└──────────────────────────────────────────────┘
   │
   (window close)
   │
   ▼
┌─────────────────┐
│ Cleanup:        │
│ ├ export CSV    │
│ ├ save settings │
│ ├ release cam   │
│ ├ close analyzer│
│ └ stop tray     │
└─────────────────┘
```

---

## 9. Atajos de teclado

Todos los atajos de v2.0 se mantienen, con adiciones:

| Atajo | Accion | Nuevo |
|-------|--------|-------|
| `Ctrl+Q` | Cerrar app (exporta CSV) | Actualizado |
| `Ctrl+P` | Pausar / Reanudar | Actualizado |
| `Ctrl+C` | Recalibrar | Nuevo (era solo C) |
| `Ctrl+B` | Break manual | Nuevo (era solo B) |
| `Ctrl+M` | Minimizar a tray | Nuevo (era solo M) |
| `Ctrl+1` | Ir a Monitor | Nuevo |
| `Ctrl+2` | Ir a Dashboard | Nuevo |
| `Ctrl+3` | Ir a Ajustes | Nuevo |
| `Ctrl+4` | Ir a Historial | Nuevo |
| `Ctrl+T` | Toggle tema dark/light | Nuevo |

---

## 10. Dependencias

```
# Core (sin cambios)
opencv-python>=4.8
mediapipe>=0.10
numpy>=1.24
plyer>=2.1
pystray>=0.19
Pillow>=10.0

# Nuevas para v3.0
customtkinter>=5.2
matplotlib>=3.8
```

---

## 11. Migracion v2.0 → v3.0

### 11.1 Archivos que se mueven

| Origen (v2.0) | Destino (v3.0) | Cambios |
|----------------|----------------|---------|
| `capture.py` | `core/capture.py` | Sin cambios |
| `analyzer.py` | `core/analyzer.py` | `draw()` simplificado (solo landmarks) |
| `notifier.py` | `core/notifier.py` | Agrega callback para toast in-app |
| `health_bar.py` | `core/health_bar.py` | Se elimina `draw()` |
| `session_stats.py` | `core/session_stats.py` | Sin cambios |
| `config.py` | `config/defaults.py` | Renombrado, mismos valores |
| `tray.py` | `tray.py` | Sin cambios |
| `main.py` | `main.py` | Reescrito (minimal bootstrap) |

### 11.2 Archivos nuevos

| Archivo | Proposito |
|---------|-----------|
| `app.py` | Coordinador principal CTk |
| `ui/theme.py` | Sistema de temas |
| `ui/sidebar.py` | Sidebar de navegacion |
| `ui/views/monitor_view.py` | Vista principal |
| `ui/views/dashboard_view.py` | Dashboard |
| `ui/views/settings_view.py` | Configuracion |
| `ui/views/history_view.py` | Historial |
| `ui/components/video_panel.py` | Panel de video |
| `ui/components/health_ring.py` | Indicador circular |
| `ui/components/stat_card.py` | Tarjeta de stat |
| `ui/components/toast.py` | Notificaciones in-app |
| `ui/components/calibration_modal.py` | Modal de calibracion |
| `ui/components/metric_badge.py` | Badge de metrica |
| `config/settings.py` | Persistencia JSON |
| `assets/icons/*.png` | Iconos de la UI |

### 11.3 Compatibilidad

- `session_log.csv`: formato identico, compatible con sesiones previas
- `pose_landmarker_lite.task`: sin cambios
- Toda la logica de deteccion postural se mantiene intacta

---

## 12. Estructura de archivos final

```
posture-checker/
├── main.py                          # Entry point (minimal)
├── app.py                           # PostureCheckerApp (CTk)
│
├── ui/
│   ├── __init__.py
│   ├── theme.py                     # Paletas dark/light
│   ├── sidebar.py                   # Navegacion lateral
│   ├── views/
│   │   ├── __init__.py
│   │   ├── monitor_view.py          # Video + health + metrics
│   │   ├── dashboard_view.py        # Stats + graficos
│   │   ├── settings_view.py         # Configuracion interactiva
│   │   └── history_view.py          # Historial de sesiones
│   └── components/
│       ├── __init__.py
│       ├── health_ring.py           # Indicador circular
│       ├── stat_card.py             # Tarjeta de stat
│       ├── video_panel.py           # Video en vivo
│       ├── toast.py                 # Notificaciones in-app
│       ├── calibration_modal.py     # Modal de calibracion
│       └── metric_badge.py          # Badge de metrica
│
├── core/
│   ├── __init__.py
│   ├── capture.py                   # Webcam
│   ├── analyzer.py                  # Metricas + MediaPipe
│   ├── notifier.py                  # Alertas sonoras + toast OS
│   ├── health_bar.py                # Logica de salud
│   └── session_stats.py             # Estadisticas + CSV
│
├── config/
│   ├── __init__.py
│   ├── defaults.py                  # Constantes default
│   ├── settings.py                  # Clase Settings (JSON)
│   └── user_settings.json           # Preferencias (generado)
│
├── assets/
│   └── icons/
│       ├── monitor.png
│       ├── dashboard.png
│       ├── settings.png
│       ├── history.png
│       ├── pause.png
│       ├── play.png
│       ├── calibrate.png
│       └── app_icon.png
│
├── tray.py                          # System tray
├── pose_landmarker_lite.task        # Modelo MediaPipe
├── requirements.txt                 # Dependencias
├── session_log.csv                  # Log (generado)
└── docs/
    ├── SDD_PostureChecker.md
    ├── SDD_PostureChecker_v2.md
    └── SDD_PostureChecker_v3.md     # Este documento
```

---

## 13. Mockup completo de la app

### 13.1 Vista Monitor (default)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PostureChecker                                              _ □ X     │
├──────────────┬──────────────────────────────────────────────────────────┤
│              │                                                          │
│  PC          │  ┌──────────────────────────────────┐  ┌──────────────┐ │
│              │  │                                    │  │              │ │
│ ● Monitor   │  │                                    │  │  ╭────────╮  │ │
│   Dashboard  │  │                                    │  │ ╭╯████████╰╮│ │
│   Ajustes    │  │         VIDEO EN VIVO              │  │ │          ││ │
│   Historial  │  │       (con landmarks)              │  │ │   82%    ││ │
│              │  │                                    │  │ │          ││ │
│ ────────── │  │                                    │  │ ╰╮░░░░░░░╭╯│ │
│              │  │                                    │  │  ╰────────╯  │ │
│ ▶ Pausar    │  │                                    │  │              │ │
│ ◎ Calibrar  │  │  ┌────────────────────────────┐   │  │ ✓ Postura OK │ │
│              │  │  │  ✓ OK        12:34 (82%)  │   │  │              │ │
│ ────────── │  │  └────────────────────────────┘   │  │ ──────────── │ │
│              │  └──────────────────────────────────┘  │              │ │
│ 🌙 Dark     │                                         │ ● Fwd   0.42 │ │
│              │                                         │ ● Drop  1.21 │ │
│ v3.0        │                                         │ ● ShW   0.38 │ │
│              │                                         │ ● Raise 0.55 │ │
│              │                                         │ ● Tilt  -2.1 │ │
│              │                                         │ ○ Lat   0.03 │ │
│              │                                         │              │ │
│              │                                         │ Sesion: 34m  │ │
│              │                                         │ Buenos: 78%  │ │
│              │                                         └──────────────┘ │
├──────────────┴──────────────────────────────────────────────────────────┤
│  Ctrl+P Pausar  │  Ctrl+C Calibrar  │  Ctrl+B Break  │  Ctrl+T Tema   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Vista con tema Light

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PostureChecker                                              _ □ X     │
├──────────────┬──────────────────────────────────────────────────────────┤
│ ░░░░░░░░░░░░ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░            │ ░                                                    ░ │
│ ░ PC         │ ░  (mismo layout, colores claros)                    ░ │
│ ░            │ ░  Background: #F5F5F7                               ░ │
│ ░ ● Monitor  │ ░  Cards: #FFFFFF con sombra sutil                   ░ │
│ ░   Dashboard│ ░  Texto: #1D1D1F                                    ░ │
│ ░   Ajustes  │ ░  Acentos: mismos colores vibrantes                 ░ │
│ ░   Historial│ ░                                                    ░ │
│ ░            │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░ ☀ Light   │                                                       │
│ ░░░░░░░░░░░░ │                                                       │
└──────────────┴──────────────────────────────────────────────────────────┘
```

---

## 14. Consideraciones de performance

| Aspecto | Solucion |
|---------|----------|
| Frame rate | `self.after(33)` para ~30fps. El procesamiento de frame no bloquea la UI |
| Conversion de imagen | PIL resize al tamano del panel, no del frame completo |
| matplotlib embebido | Solo se actualiza cuando la vista Dashboard esta activa |
| Historial CSV | Se carga una vez al abrir la vista, no en cada frame |
| Animaciones | Interpolacion con `self.after(16)` para ~60fps solo en el health ring |
| Memoria | CTkImage se reutiliza (no crear nueva instancia por frame) |
| Thread safety | Tray icon en daemon thread, UI updates solo en main thread |

---

## 15. Plan de implementacion sugerido

| Fase | Modulos | Prioridad |
|------|---------|-----------|
| 1 | `main.py`, `app.py`, `ui/theme.py`, `ui/sidebar.py` | Critico |
| 2 | `ui/components/video_panel.py`, `ui/views/monitor_view.py` | Critico |
| 3 | `ui/components/health_ring.py`, `ui/components/metric_badge.py` | Alto |
| 4 | `config/settings.py`, `ui/views/settings_view.py` | Alto |
| 5 | `ui/components/stat_card.py`, `ui/views/dashboard_view.py` | Medio |
| 6 | `ui/views/history_view.py` | Medio |
| 7 | `ui/components/toast.py`, `ui/components/calibration_modal.py` | Medio |
| 8 | Iconos, polish visual, animaciones | Bajo |
| 9 | Testing integral, ajuste de colores y espaciado | Bajo |
