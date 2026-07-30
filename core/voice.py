"""Alertas por voz (Text-to-Speech) — modulo COMPARTIDO por escritorio y web.

Estrategia (Opcion A): las frases de alerta son fijas y pocas, asi que se
generan **una sola vez** con gTTS y se cachean como MP3 en `assets/audio/`.
En runtime solo se reproduce el archivo ya listo, por lo que:

  * internet solo hace falta la primera vez (para generar el cache);
  * la alerta es instantanea (sin round-trip a Google);
  * si gTTS falla o no hay internet, la app sigue andando (el escritorio cae
    al beep y la web simplemente no reproduce nada).

Escritorio: reproduce el MP3 con el reproductor MCI de Windows (winmm, via
ctypes) — sin dependencia extra, consistente con el uso de `winsound`.
Web: los MP3 se sirven como estaticos y los reproduce el navegador.
"""

import os
import threading

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")

# Frase por nivel de severidad (0/1/2) + recordatorio de descanso.
VOICE_PHRASES = {
    "0": "Corregi un poco la postura",
    "1": "Tu postura empeoro, sentate derecho",
    "2": "Postura muy mala, endereza la espalda",
    "break": "Hora de un descanso. Levantate y estira un poco",
}

_gen_lock = threading.Lock()
_play_lock = threading.Lock()


def audio_path(key) -> str:
    return os.path.join(AUDIO_DIR, f"voice_{key}.mp3")


def ensure_cached(lang: str = "es") -> tuple[list[str], list[str]]:
    """Genera con gTTS los MP3 que falten. Idempotente y thread-safe.

    Devuelve (generados, faltantes) donde `faltantes` son las claves que no se
    pudieron generar (sin gTTS instalado, sin internet, etc.).
    """
    with _gen_lock:
        os.makedirs(AUDIO_DIR, exist_ok=True)
        missing = [k for k in VOICE_PHRASES if not os.path.isfile(audio_path(k))]
        if not missing:
            return [], []

        try:
            from gtts import gTTS
        except ImportError:
            return [], missing

        generated: list[str] = []
        failed: list[str] = []
        for key in missing:
            try:
                gTTS(text=VOICE_PHRASES[key], lang=lang, slow=False).save(audio_path(key))
                generated.append(key)
            except Exception:
                failed.append(key)
        return generated, failed


def _play_blocking(path: str) -> None:
    """Reproduce un MP3 en Windows via MCI (winmm). Bloquea hasta terminar,
    por eso `VoicePlayer.speak` lo lanza en un hilo aparte."""
    import ctypes

    mci = ctypes.windll.winmm.mciSendStringW
    with _play_lock:
        alias = "sg_voice"
        mci(f"close {alias}", None, 0, 0)
        # 'type mpegvideo' abre el MP3 con el dispositivo MPEG de Windows.
        if mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, 0) != 0:
            return
        mci(f"play {alias} wait", None, 0, 0)
        mci(f"close {alias}", None, 0, 0)


class VoicePlayer:
    """Reproductor de alertas por voz para la app de ESCRITORIO.

    Al construirse dispara la generacion del cache en segundo plano, para no
    bloquear el arranque de la UI.
    """

    def __init__(self, lang: str = "es"):
        self._lang = lang
        threading.Thread(target=ensure_cached, args=(lang,), daemon=True).start()

    def speak(self, key) -> bool:
        """Reproduce (async) la frase de la clave dada. Devuelve False si el
        MP3 aun no existe, para que el llamador pueda caer al beep."""
        path = audio_path(str(key))
        if not os.path.isfile(path):
            return False
        threading.Thread(target=_play_blocking, args=(path,), daemon=True).start()
        return True

    def speak_break(self) -> bool:
        return self.speak("break")
