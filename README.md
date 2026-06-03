# Spine Guard

Aplicacion de escritorio que monitorea tu postura en tiempo real usando la webcam. Detecta problemas posturales como inclinacion hacia adelante, hombros caidos, cabeza ladeada y mas, alertandote con notificaciones sonoras y visuales para que corrijas tu posicion.

## Que hace

- **Deteccion de postura en tiempo real** a traves de la webcam usando MediaPipe Pose para rastrear puntos corporales clave (hombros, cabeza, torso).
- **Calibracion automatica**: al iniciar, el sistema aprende tu postura ideal en unos segundos.
- **Deteccion de multiples problemas**: inclinacion frontal, slouching, hombros levantados, cabeza ladeada e inclinacion lateral.
- **Barra de salud**: indicador visual que baja cuando mantenes mala postura y se recupera al corregirla, similar a un videojuego.
- **Alertas escalables**: notificaciones con sonido que se intensifican segun la gravedad y duracion del problema.
- **Recordatorios de descanso**: aviso configurable para levantarte y estirar cada cierto tiempo.
- **Dashboard con estadisticas**: porcentaje de buena postura, tiempo de sesion, alertas emitidas, historial de salud y problemas mas frecuentes.
- **Historial de sesiones**: exporta datos a CSV para revisar tu progreso a lo largo del tiempo.
- **System tray**: la app se minimiza a la bandeja del sistema con icono de estado (verde/rojo).

## Stack tecnico

| Componente | Tecnologia |
|---|---|
| Lenguaje | Python 3.12+ |
| UI | CustomTkinter (interfaz moderna estilo macOS) |
| Vision | OpenCV + MediaPipe Pose Landmarker |
| Filtrado | 1-Euro Filter (suavizado de landmarks) |
| Notificaciones | plyer + winsound |
| Graficos | Matplotlib (embebido en dashboard) |
| System tray | pystray + Pillow |

## Instalacion

```bash
# Clonar el repo
git clone https://github.com/juancruzbonadeo/spine-guard.git
cd spine-guard

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
python main_v3.py
```

1. La app abre la webcam y te pide que te sientes derecho para calibrar.
2. Una vez calibrada, comienza el monitoreo en tiempo real.
3. Navega entre las vistas usando la barra lateral: **Monitor**, **Dashboard**, **Ajustes** e **Historial**.

### Atajos de teclado

| Atajo | Accion |
|---|---|
| `Ctrl+1/2/3/4` | Cambiar entre vistas |
| `Ctrl+P` | Pausar / reanudar |
| `Ctrl+C` | Recalibrar postura |
| `Ctrl+B` | Registrar break manual |
| `Ctrl+T` | Alternar tema claro/oscuro |
| `Ctrl+Q` | Salir |

## Estructura del proyecto

```
spine-guard/
├── main_v3.py          # Punto de entrada (v3 - CustomTkinter UI)
├── main.py             # Punto de entrada (v2 - OpenCV UI)
├── app.py              # Clase principal de la aplicacion
├── core/
│   ├── analyzer.py     # Analisis de postura con MediaPipe
│   ├── capture.py      # Captura de webcam
│   ├── filters.py      # 1-Euro Filter para suavizado
│   ├── health_bar.py   # Sistema de barra de salud
│   ├── notifier.py     # Notificaciones y alertas sonoras
│   └── session_stats.py # Estadisticas de sesion
├── config/
│   ├── defaults.py     # Valores por defecto
│   └── settings.py     # Persistencia de configuracion
├── ui/
│   ├── theme.py        # Tema claro/oscuro
│   ├── sidebar.py      # Barra lateral de navegacion
│   ├── components/     # Componentes reutilizables
│   │   ├── video_panel.py
│   │   ├── metric_badge.py
│   │   ├── stat_card.py
│   │   ├── health_ring.py
│   │   ├── toast.py
│   │   └── calibration_modal.py
│   └── views/          # Vistas principales
│       ├── monitor_view.py
│       ├── dashboard_view.py
│       ├── settings_view.py
│       └── history_view.py
├── tray.py             # Icono en bandeja del sistema
├── requirements.txt
└── docs/               # Documentacion de diseno (SDD)
```

## Contexto academico

Proyecto desarrollado para la materia **Soporte a la Gestion de Datos con Programacion Visual** de la [UTN (Universidad Tecnologica Nacional)](https://www.utn.edu.ar/).
