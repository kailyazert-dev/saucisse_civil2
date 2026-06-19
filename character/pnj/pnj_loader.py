from __future__ import annotations
from assets.param_humain import IbmI_personnage
from character.character_base import Humain


def humain_from_data(nom: str) -> Humain:
    """Construit un Humain à partir des données de param_humain.py."""
    d     = IbmI_personnage.personnages.get(nom, {})
    phys  = d.get("competences", {}).get("physique", {})
    intel = d.get("competences", {}).get("intelecte", {})
    return Humain(
        force=phys.get("force", 0.1),
        vitesse=phys.get("vitesse", 0.1),
        endurance=phys.get("endurance", 0.1),
        mathematique=intel.get("mathematique", 0.1),
        logique=intel.get("logique", 0.1),
        rpg=0.1,
        music=intel.get("musique", 0.1),
        langue=intel.get("langage", 0.1),
        sociabilite=intel.get("sociale", 0.1),
    )
