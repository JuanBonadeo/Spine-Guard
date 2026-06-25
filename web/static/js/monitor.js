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
let toastTimer = null;

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

  // toast cuando se registra una nueva alerta
  if (s.alert_id > lastAlertId) {
    lastAlertId = s.alert_id;
    showToast("⚠ " + (s.message || "Postura incorrecta"), "danger");
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

// vistas aun no implementadas (Dashboard / Ajustes / Historial)
document.querySelectorAll('.nav-item[data-view]').forEach((b) => {
  b.addEventListener("click", () => {
    if (b.getAttribute("data-view") !== "monitor") {
      showToast("Vista en desarrollo", "info");
    }
  });
});

setInterval(poll, 500);
poll();
