from __future__ import annotations
import os
import sys

APP_NAME = "SaucisseCivilisation"
_PROJECT_ROOT: str | None = None


def get_project_root() -> str:
    """Racine des assets (lecture seule).
    Frozen : sys._MEIPASS (bundle extrait par PyInstaller).
    Dev    : racine du dépôt."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        if getattr(sys, "frozen", False):
            _PROJECT_ROOT = sys._MEIPASS
        else:
            # utils/ est un niveau sous la racine
            _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return _PROJECT_ROOT


def get_save_dir() -> str:
    """Dossier de sauvegarde (lecture-écriture).
    Frozen : dossier contenant l'exe.
    Dev    : save/ dans la racine du projet."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = get_project_root()
    path = os.path.join(base, "save")
    os.makedirs(path, exist_ok=True)
    return path


def asset(relative_path: str) -> str:
    """Convertit un chemin relatif d'asset en chemin absolu portable."""
    parts = relative_path.replace("\\", "/").split("/")
    return os.path.join(get_project_root(), *parts)
