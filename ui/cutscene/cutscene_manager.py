"""Gestionnaire centralisé des cutscènes narratives.

Avant : logique de détection et de déclenchement dispersée dans input_handler.py
        (4 méthodes quasi-identiques) et map_base.py (5 attributs CutscenePopup).
Après : une seule classe, données déclaratives, callbacks explicites.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING
import arcade
from character.equipment.weapon import Weapon
from ui.dialogue.cutscene_popup import CutscenePopup
from ui.cutscene.cutscene_data import (KYLE_LINES, KYLE_END_LINES, SYLVAIN_LINES, JEAN_CHRISTOPHE_LINES, GUY_LINES)

if TYPE_CHECKING:
    from world.scene.base_scene import BaseScene


@dataclass
class _Entry:
    popup: CutscenePopup
    on_done: Callable


class CutsceneManager:
    """Gère toutes les cutscènes du jeu depuis un point unique."""

    def __init__(self, game_view: BaseScene):
        self._gv = game_view

        self._kyle     = CutscenePopup("Kyle", KYLE_LINES)
        self._kyle_end = CutscenePopup("Kyle", KYLE_END_LINES)
        self._sylvain  = CutscenePopup("Sylvain", SYLVAIN_LINES, (100, 200, 255))
        self._jc       = CutscenePopup("Jean-Christophe", JEAN_CHRISTOPHE_LINES, (150, 220, 120))
        self._guy      = CutscenePopup("Guy", GUY_LINES, (220, 80, 80))

        self._all: list[_Entry] = [
            _Entry(self._kyle,     self._on_kyle_done),
            _Entry(self._kyle_end, self._on_kyle_end_done),
            _Entry(self._sylvain,  self._on_sylvain_done),
            _Entry(self._jc,       self._on_jc_done),
            _Entry(self._guy,      self._on_guy_done),
        ]

    @property
    def any_active(self) -> bool:
        return any(e.popup.active for e in self._all)

    def handle_enter(self) -> bool:
        """Consomme ENTER si une cutscène est active. Retourne True si consommé."""
        for entry in self._all:
            if entry.popup.active:
                done = entry.popup.advance()
                if done:
                    entry.on_done()
                return True
        return False

    def try_trigger(self, pnj) -> bool:
        """Déclenche la cutscène du PNJ si les conditions sont remplies."""
        nom = pnj.nom
        if nom == "Kyle":
            if self._cutscene_needed(3, 1, "Kyle"):
                self._kyle.open()
                return True
            if self._kyle_end_needed():
                self._kyle_end.open()
                return True
        elif nom == "Sylvain" and self._cutscene_needed(2, 1, "Sylvain"):
            self._sylvain.open()
            return True
        elif nom == "Jean christophe" and self._cutscene_needed(2, 1, "Jean christophe"):
            self._jc.open()
            return True
        elif nom == "Guy" and self._cutscene_needed(2, 4, "Guy"):
            self._guy.open()
            return True
        return False

    def draw(self) -> None:
        for entry in self._all:
            entry.popup.draw()

    # ---------------------------------------------------------------- checks

    def _cutscene_needed(self, arc_id: int, quest_id: int, pnj_name: str) -> bool:
        qm = self._gv.quest_manager
        if qm.arc is None or qm.arc.arc_id != arc_id:
            return False
        quest = next((q for q in qm.arc.quests if q.status == "ec" and q.id == quest_id), None)
        if quest is None:
            return False
        return any(
            o.type == "talk" and o.stat_key == pnj_name and o.status != "t"
            for o in quest.objectives
        )

    def _kyle_end_needed(self) -> bool:
        gv = self._gv
        if not hasattr(gv, "kyle_ai") or not gv.kyle_ai.walk_done:
            return False
        if not hasattr(gv, "zombie_mode") or gv.zombie_mode.is_active():
            return False
        return not gv.kyle_ai.end_talked

    # ---------------------------------------------------------------- callbacks

    def _on_kyle_done(self) -> None:
        gv = self._gv
        gv.quest_manager.complete_talk_objective("Kyle")
        if gv.player_sprite is not None:
            gv.player_sprite.weapon_feu   = Weapon.from_name("Pistolet")
            gv.player_sprite.weapon_blanc = Weapon.from_name("Couteau")
            gv.character_manager.save_player()
        if hasattr(gv, "kyle_ai"):
            gv.kyle_ai.start_walk()

    def _on_kyle_end_done(self) -> None:
        gv = self._gv
        if hasattr(gv, "kyle_ai"):
            gv.kyle_ai.end_talked = True
        gv.quest_manager.complete_talk_objective("Kyle")

    def _on_sylvain_done(self) -> None:
        self._gv.quest_manager.complete_talk_objective("Sylvain")

    def _on_jc_done(self) -> None:
        self._gv.quest_manager.complete_talk_objective("Jean christophe")

    def _on_guy_done(self) -> None:
        self._gv.quest_manager.complete_talk_objective("Guy")
