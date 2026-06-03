from __future__ import annotations
import os
import sys

APP_NAME = "SaucisseCivilisation"
_PROJECT_ROOT: str | None = None


def get_save_dir() -> str:
    """Retourne le répertoire AppData de l'utilisateur pour les sauvegardes (cross-platform)."""
    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_project_root() -> str:
    """Retourne la racine du projet. Compatible avec les bundles PyInstaller."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        if getattr(sys, "frozen", False):
            _PROJECT_ROOT = os.path.dirname(sys.executable)
        else:
            # utils/ est un niveau sous la racine
            _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return _PROJECT_ROOT


def asset(relative_path: str) -> str:
    """Convertit un chemin relatif d'asset en chemin absolu portable."""
    parts = relative_path.replace("\\", "/").split("/")
    return os.path.join(get_project_root(), *parts)
