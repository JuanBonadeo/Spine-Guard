import json
import os

from .defaults import DEFAULTS


SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "user_settings.json")


class Settings:

    def __init__(self, path: str = SETTINGS_PATH):
        self._path = path
        self._user: dict = {}
        self.load()

    def get(self, key: str):
        return self._user.get(key, DEFAULTS.get(key))

    def set(self, key: str, value):
        self._user[key] = value
        self.save()

    def reset(self, key: str = None):
        if key is None:
            self._user.clear()
        else:
            self._user.pop(key, None)
        self.save()

    def load(self):
        if os.path.isfile(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                self._user = json.load(f)

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._user, f, indent=2, ensure_ascii=False)

    def as_dict(self) -> dict:
        merged = dict(DEFAULTS)
        merged.update(self._user)
        return merged
