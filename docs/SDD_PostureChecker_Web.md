# SDD Web v1.0 — Especificacion de Diseno Detallado
## PostureChecker: Interfaz Web (Flask) con paridad visual macOS-style

> Documento hermano de `SDD_PostureChecker_v3.md`. Define como llevar la
> estetica de la app de escritorio (CustomTkinter, estilo macOS) a la version
> web servida por Flask, de forma que **se vea identica**. Reutiliza el mismo
> motor de analisis (`core/`) y el mismo sistema de diseno (paleta, tipografia,
> componentes) que la v3.0 de escritorio.

---

## 1. Proposito

PostureChecker ya cuenta con dos frentes que comparten el mismo cerebro
(`core/` + `config/`):

- **Escritorio** (`app.py` + `ui/`, CustomTkinter) — interfaz macOS-style v3.0.
- **Web** (`web/` + `main_web.py`, Flask) — interfaz de navegador.

La version web actual es funcional pero tiene un estilo propio mas simple. El
objetivo de este SDD es **unificar la identidad visual**: que la web replique
1:1 la paleta, la tipografia, el layout y los componentes del escritorio, sin
tocar la logica de deteccion postural (que es compartida y ya esta resuelta).

El principio rector es **paridad visual**: un usuario que conoce la app de
escritorio debe reconocer la web de inmediato como "la misma app, en el
navegador".

---

## 2. Alcance

| Incluido (Web v1.0) | Excluido |
|---------------------|----------|
| Sidebar de navegacion identico al escritorio (220px) | Reescribir la logica de `core/` |
| Paleta de colores portada (dark/light) como variables CSS | Camara desde el navegador (modo remoto, ver SDD futuro) |
| Tipografia y escala tipografica identicas | Persistencia en base de datos |
| HealthRing replicado en SVG (mismo arco, colores y umbrales) | Multiusuario simultaneo |
| MetricBadges (6 metricas) con el mismo formato | App movil nativa |
| Vista Monitor con layout video + panel derecho | --- |
| Toggle de tema dark/light con persistencia (localStorage) | --- |
| Toasts in-app estilizados | --- |
| Overlay de calibracion con barra de progreso | --- |
| Estado en vivo via polling de `/status` | --- |

**Vistas en alcance:** la **Vista Monitor** alcanza paridad completa en esta
version. Dashboard, Ajustes e Historial se contemplan en el sistema de diseno
y el sidebar (placeholders navegables), con implementacion fase a fase
(seccion 14), espejando las vistas del escritorio.

---

## 3. Relacion con el escritorio v3.0

La web **no reimplementa** nada del dominio. Solo cambia la *tecnologia de
render*: donde el escritorio usa widgets CustomTkinter, la web usa HTML + CSS.

| Capa | Escritorio v3.0 | Web v1.0 |
|------|------------------|----------|
| Deteccion postural | `core/analyzer.py` | **el mismo** `core/analyzer.py` |
| Estadisticas / salud | `core/session_stats.py`, `core/health_bar.py` | **los mismos** |
| Configuracion | `config/` | **el mismo** |
| Coordinacion | `app.py` (CTk loop con `after`) | `web/engine.py` + `web/server.py` (hilo de captura) |
| Render | `ui/` (CustomTkinter) | `web/templates/` + `web/static/` (HTML/CSS/JS) |
| Sistema de diseno | `ui/theme.py` (dict de colores) | `web/static/css/tokens.css` (variables CSS, **mismos hex**) |

**Fuente unica de verdad del diseno:** los valores de `ui/theme.py` se portan
literalmente a variables CSS (seccion 6.1). Si en el futuro cambia un color del
escritorio, se actualiza el token equivalente en la web.

---

## 4. Tecnologias

| Componente | Tecnologia | Justificacion |
|-----------|------------|---------------|
| Servidor web | **Flask** | Ligero, integra con el `core/` Python sin capa extra |
| Plantillas | **Jinja2** (incluido en Flask) | `base.html` + parciales, evita duplicar el layout |
| Estilos | **CSS3** (variables nativas) | Tokens y theming dark/light sin framework |
| Interactividad | **JavaScript vanilla** (fetch) | Polling de estado y toggle de tema, sin dependencias |
| Video en vivo | **MJPEG** (`multipart/x-mixed-replace`) | El server transmite frames ya anotados por `analyzer.draw()` |
| Indicador de salud | **SVG** (stroke-dasharray) | Replica fiel del arco del HealthRing del escritorio |
| Iconos | Glifos Unicode / SVG inline | Sin assets binarios; ligero |
| Persistencia tema | `localStorage` | Equivalente web al `user_settings.json["theme"]` |
| Lenguaje | Python 3.10+ / ES2017+ | --- |

**Mapeo de widgets CustomTkinter -> equivalente web:**

| Escritorio (CTk) | Web (HTML/CSS) |
|------------------|----------------|
| `CTkFrame` (card) | `<div class="card">` |
| `CTkButton` | `<button class="btn">` / `<a class="nav-item">` |
| `CTkLabel` | `<span>` / `<p>` / `<h1>` |
| `CTkSwitch` (tema) | `<button class="theme-toggle">` + clase en `<html>` |
| `tk.Canvas` (HealthRing) | `<svg>` con `<circle>` y `stroke-dasharray` |
| `CTkProgressBar` (calibracion) | `<div class="progress"><div class="progress-fill">` |
| Toast CTk | `<div class="toast">` con auto-dismiss |
| `VideoPanel` (CTkLabel + CTkImage) | `<img src="/video_feed">` |

---

## 5. Sistema de Diseno (portado del escritorio)

### 5.1 Filosofia visual

Identica a la v3.0 de escritorio (seccion 5.1 de `SDD_PostureChecker_v3.md`):
**claridad, profundidad, minimalismo, consistencia**, estetica macOS.

### 5.2 Tokens de color — `web/static/css/tokens.css`

Portados literalmente de `ui/theme.py`. El tema activo se controla con un
atributo en `<html>` (`data-theme="dark"` | `"light"`).

```css
:root,
html[data-theme="dark"] {
  --bg-primary:     #1E1E1E;
  --bg-sidebar:     #171717;
  --bg-card:        #2A2A2A;
  --bg-card-hover:  #333333;
  --bg-input:       #333333;
  --text-primary:   #FFFFFF;
  --text-secondary: #A0A0A0;
  --text-muted:     #666666;
  --accent:         #007AFF;
  --accent-hover:   #0066D6;
  --success:        #30D158;
  --warning:        #FFD60A;
  --danger:         #FF453A;
  --border:         #3A3A3A;
  --divider:        #2C2C2C;
  --ring-track:     #3A3A3A;
  --nav-active-bg:  rgba(0, 122, 255, 0.15);
  --nav-active-text:#4DA3FF;
  --card-shadow:    0 2px 8px rgba(0, 0, 0, 0.35);
}

html[data-theme="light"] {
  --bg-primary:     #F5F5F7;
  --bg-sidebar:     #E8E8ED;
  --bg-card:        #FFFFFF;
  --bg-card-hover:  #F0F0F0;
  --bg-input:       #FFFFFF;
  --text-primary:   #1D1D1F;
  --text-secondary: #86868B;
  --text-muted:     #AEAEB2;
  --accent:         #007AFF;
  --accent-hover:   #0056B3;
  --success:        #34C759;
  --warning:        #FF9F0A;
  --danger:         #FF3B30;
  --border:         #D2D2D7;
  --divider:        #E5E5EA;
  --ring-track:     #E5E5EA;
  --nav-active-bg:  rgba(0, 122, 255, 0.12);
  --nav-active-text:#007AFF;
  --card-shadow:    0 2px 8px rgba(0, 0, 0, 0.08);
}
```

> **Nota de armonizacion:** en el escritorio el item de nav activo en modo claro
> usa fondo gris; en la web se unifica a "fondo de acento translucido + texto de
> acento" en ambos temas (mas fiel a la guia macOS y consistente con el modo
> oscuro del propio escritorio, que ya usa azul: `#1A3A5C` / `#4DA3FF`).

### 5.3 Tipografia

| Uso | Token / Clase | Tamano | Peso | Origen escritorio |
|-----|---------------|--------|------|-------------------|
| Titulo de seccion | `.title` | 24px | 700 | SDD v3 §5.3 |
| Subtitulo | `.subtitle` | 18px | 600 | SDD v3 §5.3 |
| Logo "Spine Guard" | `.brand h1` | 17px | 700 | `sidebar.py` |
| Estado postura | `.status-text` | 15px | 700 | `monitor_view.py` |
| Body / nav item | base | 14px | 400 | `sidebar.py` |
| Header de seccion / btn sec. | `.section-label` | 13px | 600 | `monitor_view.py` |
| Stat label / info sesion | `.muted` | 12px | 400 | `monitor_view.py` |
| Caption / hint / version | `.caption` | 11px | 400 | `sidebar.py` |
| Valor del HealthRing | `.ring-pct` | 28px | 700 | `health_ring.py` |
| Valor de metrica (badge) | `.badge-value` | 12px | 400 (mono) | `metric_badge.py` |

**Familia tipografica** (stack de sistema, replica "SF Pro / Segoe UI"):

```css
--font-ui: -apple-system, BlinkMacSystemFont, "SF Pro Display",
           "Segoe UI", Roboto, sans-serif;
--font-mono: "Cascadia Code", "Consolas", ui-monospace, monospace;
```

### 5.4 Especificacion de componentes

**Tarjetas (`.card`):** `border-radius: 12px`, `padding: 16px`,
`background: var(--bg-card)`, `box-shadow: var(--card-shadow)`,
`transition: background .15s ease`.

**Botones:**
- Primario (`.btn`): `background: var(--accent)`, texto blanco, `radius 8px`,
  `height 36px`, `:hover { background: var(--accent-hover) }`.
- Secundario / accion (`.btn-ghost`): fondo transparente, `radius 8px`,
  `height 36px`, `:hover { background: var(--bg-card-hover) }`.

**Sidebar (`.sidebar`):** `width: 220px` fijo, `background: var(--bg-sidebar)`,
sin radius, columna flex. Estructura identica al escritorio: logo + version,
divisor, 4 items de nav, divisor, Pausar + Calibrar, divisor, toggle de tema.

**Nav item (`.nav-item`):** `height: 38px`, `radius 8px`, padding horizontal
12px, alineado a la izquierda. Estado activo: `background: var(--nav-active-bg)`
+ `color: var(--nav-active-text)`. Hover: `background: var(--bg-card-hover)`.

**HealthRing (`.health-ring`):** ver seccion 9.4. Diametro 150px, grosor de
arco 10px, arranca arriba (12 h) y avanza en sentido horario. Color por salud:
`>0.6` verde, `>0.3` amarillo, `<=0.3` rojo. Porcentaje centrado 28px bold del
mismo color que el arco; debajo, texto de estado ("Excelente / Buena / Regular
/ Mala").

**MetricBadge (`.badge`):** fila con punto indicador (10px) + nombre + valor
(mono, alineado a la derecha). Punto verde si OK, rojo si hay problema en esa
metrica. `padding: 8px 12px`, `radius 8px`.

**Toast (`.toast`):** flotante abajo-centro, `radius 12px`, color de fondo segun
tipo (`info`=accent, `warning`=warning, `error`=danger, `success`=success),
auto-dismiss configurable, animacion de entrada slide-up.

**Overlay de calibracion (`.calib-overlay`):** capa sobre el video con blur,
spinner, barra de progreso (`.progress` + `.progress-fill` con
`background: var(--accent)`) y porcentaje.

---

## 6. Mapeo de componentes escritorio -> web

| Componente desktop | Archivo desktop | Equivalente web | Render |
|--------------------|-----------------|-----------------|--------|
| Sidebar | `ui/sidebar.py` | `templates/partials/sidebar.html` + `.sidebar` | nav flex |
| MonitorView | `ui/views/monitor_view.py` | `templates/index.html` (bloque monitor) | grid 2 col |
| VideoPanel | `ui/components/video_panel.py` | `<img id="video">` (MJPEG) | `/video_feed` |
| HealthRing | `ui/components/health_ring.py` | `.health-ring` (SVG) | seccion 9.4 |
| MetricBadge | `ui/components/metric_badge.py` | `.badge` (div) | seccion 9.5 |
| Status label | `monitor_view.py` | `.status-text` | seccion 9.3 |
| Toast | `ui/components/toast.py` | `.toast` (div + JS) | seccion 9.6 |
| CalibrationModal | `ui/components/calibration_modal.py` | `.calib-overlay` | seccion 9.7 |
| Theme (dark/light) | `ui/theme.py` | `tokens.css` + `theme.js` | seccion 9.8 |

---

## 7. Arquitectura web (ya implementada)

```
                    Navegador (cliente)
   ┌───────────────────────────────────────────────┐
   │  index.html  +  app.css  +  app.js             │
   │   <img src="/video_feed">  (MJPEG)             │
   │   fetch("/status") cada 500ms  -> actualiza UI │
   │   POST /recalibrate                            │
   └───────────────────────────────────────────────┘
                    │  HTTP
                    ▼
   ┌───────────────────────────────────────────────┐
   │  web/server.py  (Flask)                        │
   │   GET /            -> render index.html        │
   │   GET /video_feed  -> stream MJPEG             │
   │   GET /status      -> JSON de estado           │
   │   POST /recalibrate                            │
   │   + hilo de captura: lee webcam, flip,         │
   │     engine.process_frame(frame)                │
   └───────────────────────────────────────────────┘
                    │
                    ▼
   ┌───────────────────────────────────────────────┐
   │  web/engine.py  (PostureEngine)                │
   │   agnostico al transporte:                     │
   │   process_frame(frame) -> analiza, dibuja,     │
   │   actualiza stats/health, codifica JPEG        │
   └───────────────────────────────────────────────┘
                    │  reutiliza
                    ▼
   ┌───────────────────────────────────────────────┐
   │  core/ : analyzer, session_stats, health_bar   │
   │  config/ : defaults, settings                  │
   │  (COMPARTIDO con el escritorio, sin cambios)   │
   └───────────────────────────────────────────────┘
```

Este SDD **no modifica esta arquitectura**: trabaja sobre la capa de
presentacion (`templates/` + `static/`). El `PostureEngine` ya expone todo lo
que la UI necesita via `get_status()`.

---

## 8. Contrato de datos — `GET /status`

La UI se alimenta de este JSON (provisto por `PostureEngine.get_status()`):

```json
{
  "calibrating": false,
  "calib_progress": 1.0,
  "is_good": true,
  "reliable": true,
  "message": "Postura correcta",
  "problems": [],
  "confidence": 0.92,
  "health": 0.82,
  "severity": 0,
  "alert_id": 3,
  "session_min": 34.0,
  "good_pct": 78.0,
  "alerts": 5
}
```

**Mapeo campo -> elemento visual:**

| Campo | Elemento UI | Comportamiento |
|-------|-------------|----------------|
| `calibrating`, `calib_progress` | overlay de calibracion | muestra/oculta + barra de progreso |
| `health`, `severity` | HealthRing | offset del arco + color (verde/amarillo/rojo) |
| `is_good`, `reliable`, `message` | `.status-text` + punto | color y texto de estado |
| `problems[]` | MetricBadges | punto rojo en las metricas en problema |
| `session_min`, `good_pct`, `alerts` | info de sesion | textos de la parte inferior |
| `alert_id` | Toast | dispara toast cuando incrementa |
| `confidence` | caption | "Confianza: NN%" cuando la senal es debil |

> El campo `problems[]` trae los nombres largos del analyzer (p.ej.
> "Cabeza muy adelante"). Se traducen a la clave de metrica con el mismo
> `PROBLEM_MAP` que usa `monitor_view.py` (seccion 9.5).

---

## 9. Diseno de modulos web

### 9.1 Estructura de archivos objetivo

```
web/
├── __init__.py
├── engine.py                       # (existente) motor agnostico al transporte
├── server.py                       # (existente) rutas + hilo de captura
├── templates/
│   ├── base.html                   # NUEVO: layout (sidebar + content)
│   ├── index.html                  # vista Monitor (extiende base)
│   └── partials/
│       └── sidebar.html            # NUEVO: sidebar reutilizable
└── static/
    ├── css/
    │   ├── tokens.css              # NUEVO: variables de color (de theme.py)
    │   ├── base.css                # NUEVO: reset, tipografia, layout, sidebar
    │   └── monitor.css             # NUEVO: video, ring, badges, toast, overlay
    └── js/
        ├── theme.js                # NUEVO: toggle dark/light + localStorage
        └── monitor.js              # polling de /status + render (ex app.js)
```

> Migracion desde el estado actual: el `index.html`, `style.css` y `app.js`
> unicos de hoy se reorganizan en esta estructura (parciales + CSS por
> responsabilidad). No cambia el backend.

### 9.2 `base.html` — layout maestro

```
base.html
├── <head>: tokens.css, base.css, (bloque) css extra por vista
├── <body data-theme="dark">  (theme.js ajusta segun localStorage)
│   ├── {% include "partials/sidebar.html" %}
│   └── <main class="content"> {% block content %}{% endblock %} </main>
│   ├── <div id="toast" class="toast hidden"></div>
│   └── theme.js + (bloque) js por vista
```

El sidebar y el contenedor `.content` viven en `base.html`, de modo que toda
vista futura (Dashboard, Ajustes, Historial) herede el mismo marco — igual que
en el escritorio todas las vistas comparten `Sidebar` + `content`.

### 9.3 Vista Monitor — `index.html`

Replica el `MonitorView`: grid de 2 columnas, video a la izquierda (peso 3),
panel derecho de 240px.

```
.monitor (grid: 1fr 240px)
├── .video-card
│   ├── <img id="video" src="/video_feed">
│   └── .calib-overlay   (spinner + progreso)
└── .side-panel (240px)
    ├── .health-ring  (SVG 150px)
    ├── .status-text  ("Postura correcta" / mensaje)
    ├── hr.divider
    ├── .section-label "Metricas"
    ├── .badge x6  (las 6 metricas)
    ├── hr.divider
    ├── .muted  "Sesion: NN min"
    ├── .muted  "Buenos: NN%"
    └── .caption "Confianza: NN%"  (solo si senal debil)
```

**Layout visual (paridad con escritorio §13.1):**

```
┌──────────────┬───────────────────────────────────┬──────────────┐
│  Spine Guard │                                   │  ╭────────╮  │
│  v1.0 web    │                                   │ ╭╯████████╰╮ │
│              │                                   │ │   82%    │ │
│ ● Monitor    │          VIDEO EN VIVO            │ ╰╮░░░░░░░░╭╯ │
│   Dashboard  │        (con landmarks)            │  ╰────────╯  │
│   Ajustes    │                                   │ ✓ Postura OK │
│   Historial  │                                   │ ──────────── │
│ ──────────   │  ┌─────────────────────────────┐  │ Metricas     │
│ ▶ Pausar     │  │ (overlay calibracion si     │  │ ● Cab adel.  │
│ ◎ Calibrar   │  │  corresponde)               │  │ ● Cab baja   │
│ ──────────   │  └─────────────────────────────┘  │ ● Hom adel.  │
│ Tema   [◐]   │                                   │ ● Hom tensos │
│              │                                   │ ● Cab incl.  │
│              │                                   │ ○ Descentr.  │
│              │                                   │ ──────────── │
│              │                                   │ Sesion: 34m  │
│              │                                   │ Buenos: 78%  │
└──────────────┴───────────────────────────────────┴──────────────┘
```

### 9.4 HealthRing en SVG

Replica fiel de `health_ring.py`. Estructura:

```html
<div class="health-ring">
  <svg viewBox="0 0 150 150" class="ring-svg">
    <circle class="ring-track"    cx="75" cy="75" r="70"/>
    <circle class="ring-progress" cx="75" cy="75" r="70"/>
  </svg>
  <div class="ring-center">
    <span class="ring-pct">100%</span>
    <span class="ring-status">Excelente</span>
  </div>
</div>
```

```css
.ring-svg { transform: rotate(-90deg); }        /* arranca arriba (12 h) */
.ring-track, .ring-progress {
  fill: none; stroke-width: 10; stroke-linecap: butt;
}
.ring-track { stroke: var(--ring-track); }
.ring-progress {
  stroke-dasharray: 439.82;                      /* 2*pi*70 */
  stroke-dashoffset: 0;                          /* JS: C*(1-health) */
  transition: stroke-dashoffset .4s ease, stroke .4s ease;
}
```

**Logica JS (equivalente a `_render_ring` + `_animate`):**

```js
const C = 2 * Math.PI * 70;                       // 439.82
function renderRing(health) {                     // health en [0,1]
  prog.style.strokeDashoffset = C * (1 - health);
  const color = health > 0.6 ? "var(--success)"
              : health > 0.3 ? "var(--warning)"
              : "var(--danger)";
  prog.style.stroke = color;
  pct.style.color = color;
  pct.textContent = Math.round(health * 100) + "%";
  status.textContent = health > 0.8 ? "Excelente"
                     : health > 0.6 ? "Buena"
                     : health > 0.3 ? "Regular" : "Mala";
}
```

La animacion suave la da `transition` de CSS (mas simple que el bucle
`after(16)` del escritorio, mismo resultado visual). Umbrales de color y textos
de estado **identicos** al desktop.

### 9.5 MetricBadge

Las 6 metricas, en el mismo orden y nombres que `monitor_view.py`:

```js
const METRICS = [
  ["Cabeza adelante",  "forward_lean_ratio"],
  ["Cabeza baja",      "slouch_drop_ratio"],
  ["Hombros adelante", "shoulder_width_norm"],
  ["Hombros tensos",   "shoulder_raise_ratio"],
  ["Cabeza inclinada", "head_tilt_angle"],
  ["Descentrado",      "lateral_offset"],
];
const PROBLEM_MAP = {
  "Cabeza muy adelante":          "forward_lean_ratio",
  "Encorvado (cabeza baja)":      "slouch_drop_ratio",
  "Encorvado (hombros adelante)": "shoulder_width_norm",
  "Hombros tensos":               "shoulder_raise_ratio",
  "Cabeza inclinada":             "head_tilt_angle",
  "Inclinado a un lado":          "lateral_offset",
};
```

```html
<div class="badge" data-key="forward_lean_ratio">
  <span class="badge-dot"></span>
  <span class="badge-name">Cabeza adelante</span>
  <span class="badge-value">0.00</span>
</div>
```

El punto es verde (`--success`) por defecto y rojo (`--danger`) cuando la clave
esta en el set de problemas (derivado de `problems[]` via `PROBLEM_MAP`).

### 9.6 Toast

Equivalente a `ui/components/toast.py`. Se dispara cuando `alert_id` del
`/status` incrementa respecto al ultimo visto. Color por severidad. Auto-dismiss
a los 4000 ms, animacion slide-up.

### 9.7 Overlay de calibracion

Equivalente a `calibration_modal.py`, pero sobre el video. Visible mientras
`calibrating === true`; la barra interna se llena con `calib_progress` (0→1) y
muestra el porcentaje. Al terminar, se oculta y aparece la vista en vivo.

### 9.8 Tema dark/light — `theme.js`

```js
const saved = localStorage.getItem("pc-theme") || "dark";
document.documentElement.setAttribute("data-theme", saved);

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark"
             ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("pc-theme", next);
}
```

Equivale al `Theme.toggle()` del escritorio + persistencia en
`user_settings.json`. Aqui la persistencia es por navegador (`localStorage`).
El switch del sidebar llama a `toggleTheme()`.

---

## 10. Mockups

### 10.1 Vista Monitor — Dark (default)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Spine Guard  ·  web                                                  │
├──────────────┬───────────────────────────────────────┬───────────────┤
│ Spine Guard  │                                       │   ╭────────╮  │
│ v1.0 web     │                                       │  ╭╯████████╰╮ │
│              │                                       │  │   82%    │ │
│ ● Monitor    │            VIDEO EN VIVO              │  ╰╮░░░░░░░░╭╯ │
│   Dashboard  │          (con landmarks)              │   ╰────────╯  │
│   Ajustes    │                                       │  ✓ Postura OK │
│   Historial  │                                       │ ───────────── │
│ ───────────  │                                       │ Metricas      │
│ ▶ Pausar     │                                       │ ● Cab adel.   │
│ ◎ Calibrar   │                                       │ ● Cab baja    │
│ ───────────  │                                       │ ● Hom adel.   │
│ Tema    [◐]  │                                       │ ● Hom tensos  │
│              │                                       │ ● Cab incl.   │
│              │                                       │ ○ Descentr.   │
│              │                                       │ ───────────── │
│              │                                       │ Sesion: 34m   │
│              │                                       │ Buenos: 78%   │
└──────────────┴───────────────────────────────────────┴───────────────┘
   bg #171717            bg #1E1E1E / video                panel cards #2A2A2A
```

### 10.2 Vista Monitor — Light

```
Mismo layout, tokens claros:
  bg-primary  #F5F5F7   ·  sidebar #E8E8ED   ·  cards #FFFFFF (sombra sutil)
  texto       #1D1D1F   ·  acentos identicos (verde/amarillo/rojo vibrantes)
```

---

## 11. Responsividad

A diferencia del escritorio (ventana redimensionable con minsize), la web se
adapta a viewport variable:

| Breakpoint | Comportamiento |
|------------|----------------|
| `>= 1024px` | Layout completo: sidebar 220px + video + panel 240px |
| `768–1023px` | Sidebar 220px + video + panel apilado debajo del video |
| `< 768px` | Sidebar colapsa a barra superior; video full-width; panel debajo |

El sistema de diseno (tokens, tipografia, componentes) no cambia entre
breakpoints; solo el flujo del layout.

---

## 12. Consideraciones de performance

| Aspecto | Solucion |
|---------|----------|
| Video | MJPEG ya codificado en el server (JPEG q=80); el navegador solo pinta un `<img>` |
| Estado | Polling `/status` cada 500ms (no por frame); payload JSON minimo |
| HealthRing | Animacion via `transition` CSS (GPU), sin bucle JS |
| Reflows | Actualizaciones puntuales de `textContent`/`style`, sin reconstruir el DOM |
| Tema | Cambio de atributo en `<html>`; las variables CSS recalculan solas |
| Concurrencia | Un unico hilo de captura; multiples pestanas comparten el mismo stream |

---

## 13. Checklist de paridad visual (criterio de aceptacion)

| Elemento | Igual al escritorio cuando... |
|----------|-------------------------------|
| Paleta | Los hex de `tokens.css` coinciden con `ui/theme.py` (dark y light) |
| Sidebar | 220px, mismos items, mismo orden, item activo en azul translucido |
| Tipografia | Tamanos/pesos de la tabla §5.3 aplicados; stack SF Pro/Segoe UI |
| HealthRing | 150px, grosor 10, arranca arriba, horario, umbrales 0.6/0.3, % 28px |
| Estado | "Postura correcta" verde / mensaje rojo / "Senal debil" gris / "PAUSADO" amarillo |
| MetricBadges | 6 metricas, mismos nombres, punto verde/rojo segun problema |
| Info sesion | "Sesion: NN min" y "Buenos: NN%" en gris secundario |
| Tema | Toggle dark/light con persistencia; ambos temas correctos |
| Cards | radius 12px, padding 16px, sombra sutil |
| Toast | Aparece abajo, color por severidad, auto-dismiss |
| Calibracion | Overlay con progreso 0→100% sobre el video |

---

## 14. Plan de implementacion

| Fase | Trabajo | Prioridad |
|------|---------|-----------|
| 1 | `tokens.css` + `base.css`: reset, tipografia, layout, **sidebar** identico | Critico |
| 2 | Reorg a `base.html` + `partials/sidebar.html` + `index.html` | Critico |
| 3 | `monitor.css` + **HealthRing SVG** + `monitor.js` (render del ring) | Critico |
| 4 | MetricBadges (6) + mapeo `problems[]` -> badges | Alto |
| 5 | Status label + info de sesion + caption de confianza | Alto |
| 6 | Toast (dispara con `alert_id`) + overlay de calibracion | Medio |
| 7 | `theme.js`: toggle dark/light + `localStorage` | Medio |
| 8 | Responsividad (breakpoints) + pulido de espaciado | Bajo |
| 9 | Vistas Dashboard / Ajustes / Historial (paridad con escritorio) | Futuro |

---

## 15. Notas de compatibilidad

- **Backend intacto:** este SDD solo agrega/reorganiza `templates/` y `static/`.
  `engine.py` y `server.py` no requieren cambios para alcanzar la paridad visual.
- **`core/` y `config/` compartidos:** ninguna modificacion. La web y el
  escritorio siguen usando exactamente el mismo motor.
- **Sin assets binarios:** iconos via glifos Unicode o SVG inline, para mantener
  el repo liviano y evitar dependencias de imagenes.
- **Extensible a modo remoto:** la capa visual definida aqui es independiente de
  como llegan los frames; si en el futuro se agrega captura desde el navegador
  (`getUserMedia`), la UI no cambia.
```
