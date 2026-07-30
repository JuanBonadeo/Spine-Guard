// Vista Monitor: polling de /status + render (replica de monitor_view.py)

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

const RING_C = 2 * Math.PI * 70; // 439.82
const $ = (id) => document.getElementById(id);

let lastAlertId = 0;
let lastBreakId = 0;
let toastTimer = null;

// --- alertas por voz (gTTS servidas por /voice/<sev>) ---
let voiceEnabled = (localStorage.getItem("pc-voice") || "on") !== "off";
let audioUnlocked = false;

// Los navegadores bloquean el autoplay hasta que hay un gesto del usuario.
// Al primer click/tecla desbloqueamos el audio para la sesion.
function unlockAudio() {
  audioUnlocked = true;
  document.removeEventListener("click", unlockAudio);
  document.removeEventListener("keydown", unlockAudio);
}
document.addEventListener("click", unlockAudio);
document.addEventListener("keydown", unlockAudio);

function playVoice(severity) {
  if (!voiceEnabled || !audioUnlocked) return;
  try {
    new Audio("/voice/" + severity).play().catch(() => {});
  } catch (e) { /* sin audio: seguimos con el toast visual */ }
}

// --- construir las 6 badges ---
const badgeEls = {};
(function buildBadges() {
  const cont = $("badges");
  for (const [name, key] of METRICS) {
    const row = document.createElement("div");
    row.className = "badge";
    row.innerHTML =
      '<span class="badge-dot"></span>' +
      '<span class="badge-name"></span>' +
      '<span class="badge-value">--</span>';
    row.querySelector(".badge-name").textContent = name;
    cont.appendChild(row);
    badgeEls[key] = row;
  }
})();

function renderRing(health) {
  const prog = $("ring-progress");
  prog.style.strokeDashoffset = RING_C * (1 - health);
  const color = health > 0.6 ? "var(--success)"
              : health > 0.3 ? "var(--warning)" : "var(--danger)";
  prog.style.stroke = color;
  const pct = $("ring-pct");
  pct.textContent = Math.round(health * 100) + "%";
  pct.style.color = color;
  $("ring-status").textContent =
      health > 0.8 ? "Excelente"
    : health > 0.6 ? "Buena"
    : health > 0.3 ? "Regular" : "Mala";
}

function render(s) {
  // overlay de calibracion
  const ov = $("calib-overlay");
  if (s.calibrating) {
    ov.classList.remove("hidden");
    const p = Math.round(s.calib_progress * 100);
    $("calib-bar").style.width = p + "%";
    $("calib-pct").textContent = p + "%";
  } else {
    ov.classList.add("hidden");
  }

  renderRing(s.health);

  // estado (mismos colores/textos que monitor_view.update_status)
  const st = $("status-text");
  if (s.paused) {
    st.textContent = "PAUSADO"; st.style.color = "var(--warning)";
  } else if (s.calibrating) {
    st.textContent = "Calibrando…"; st.style.color = "var(--text-secondary)";
  } else if (!s.reliable) {
    st.textContent = "Senal debil"; st.style.color = "var(--text-secondary)";
  } else if (s.is_good) {
    st.textContent = "Postura correcta"; st.style.color = "var(--success)";
  } else {
    st.textContent = s.message || "Corregi la postura"; st.style.color = "var(--danger)";
  }

  // badges
  const probKeys = new Set();
  (s.problems || []).forEach((p) => { if (PROBLEM_MAP[p]) probKeys.add(PROBLEM_MAP[p]); });
  for (const [, key] of METRICS) {
    const row = badgeEls[key];
    row.classList.toggle("problem", probKeys.has(key));
    const m = s.metrics || {};
    row.querySelector(".badge-value").textContent =
      (key in m) ? Number(m[key]).toFixed(2) : "--";
  }

  // info de sesion
  $("session").textContent = "Sesion: " + Math.round(s.session_min) + " min";
  $("goodpct").textContent = "Buenos: " + Math.round(s.good_pct) + "%";
  $("confidence").textContent =
    (!s.reliable && !s.calibrating && !s.paused)
      ? "Confianza: " + Math.round(s.confidence * 100) + "%" : "";

  // toast + voz cuando se registra una nueva alerta
  if (s.alert_id > lastAlertId) {
    lastAlertId = s.alert_id;
    showToast("⚠ " + (s.message || "Postura incorrecta"), "danger");
    playVoice(s.severity || 0);
  }

  // recordatorio de descanso
  if (s.break_id > lastBreakId) {
    lastBreakId = s.break_id;
    showToast("☕ Hora de un descanso, levantate y estira", "info");
    playVoice("break");
  }
}

function showToast(msg, type) {
  const t = $("toast");
  t.className = "toast " + (type || "danger") + " hidden";
  t.textContent = msg;
  void t.offsetWidth;            // reflow para animar la entrada
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 4000);
}

async function poll() {
  try {
    const res = await fetch("/status");
    render(await res.json());
  } catch (e) { /* reintenta en el proximo tick */ }
}

// --- acciones del sidebar ---
$("btn-pause").addEventListener("click", async () => {
  try {
    const res = await fetch("/pause", { method: "POST" });
    const data = await res.json();
    $("btn-pause").textContent = data.paused ? "Reanudar" : "Pausar";
  } catch (e) {}
});

$("btn-calibrate").addEventListener("click", () => {
  fetch("/recalibrate", { method: "POST" });
});

// --- toggle de voz ---
const voiceBtn = $("voice-toggle");
function renderVoiceBtn() {
  voiceBtn.textContent = voiceEnabled ? "🔊 Voz" : "🔇 Voz";
  voiceBtn.classList.toggle("active", voiceEnabled);
}
voiceBtn.addEventListener("click", () => {
  voiceEnabled = !voiceEnabled;
  localStorage.setItem("pc-voice", voiceEnabled ? "on" : "off");
  renderVoiceBtn();
  showToast(voiceEnabled ? "Voz activada" : "Voz desactivada", "info");
});
renderVoiceBtn();

// navegacion: Ajustes abre el modal de tiempos; el resto sigue en desarrollo
document.querySelectorAll('.nav-item[data-view]').forEach((b) => {
  b.addEventListener("click", () => {
    const view = b.getAttribute("data-view");
    if (view === "settings") {
      openSettings();
    } else if (view !== "monitor") {
      showToast("Vista en desarrollo", "info");
    }
  });
});

// --- modal de Ajustes: tiempos de aviso (via /config) ---
const CFG_FIELDS = [
  ["check_interval_sec", "cfg-check", (v) => Math.round(v) + " s"],
  ["bad_posture_sec",    "cfg-bad",   (v) => Number(v).toFixed(1) + " s"],
  ["break_interval_min", "cfg-break", (v) => Math.round(v) + " min"],
];

function renderCfgLabel(id, fmt) {
  $(id + "-val").textContent = fmt($(id).value);
}

async function openSettings() {
  try {
    const cfg = await (await fetch("/config")).json();
    for (const [key, id, fmt] of CFG_FIELDS) {
      $(id).value = cfg[key];
      renderCfgLabel(id, fmt);
    }
  } catch (e) { /* si falla, se muestran los ultimos valores conocidos */ }
  $("settings-overlay").classList.remove("hidden");
}

async function saveConfig() {
  const body = {};
  for (const [key, id] of CFG_FIELDS) body[key] = Number($(id).value);
  try {
    await fetch("/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) { showToast("No se pudo guardar", "warn"); }
}

for (const [, id, fmt] of CFG_FIELDS) {
  const el = $(id);
  el.addEventListener("input", () => renderCfgLabel(id, fmt)); // etiqueta en vivo
  el.addEventListener("change", saveConfig);                    // guarda al soltar
}
$("cfg-close").addEventListener("click", () => {
  $("settings-overlay").classList.add("hidden");
});
$("settings-overlay").addEventListener("click", (e) => {
  if (e.target === $("settings-overlay")) $("settings-overlay").classList.add("hidden");
});

setInterval(poll, 500);
poll();
