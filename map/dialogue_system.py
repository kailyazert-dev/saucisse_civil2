from __future__ import annotations
import os
import threading
import time
from typing import TYPE_CHECKING
from dotenv import load_dotenv
import arcade
from assets.param_map import WINDOW_WIDTH, KENNY
from assets.param_humain import IbmI_personnage

if TYPE_CHECKING:
    from map.map_base import BaseGameView

try:
    import replicate as _replicate
    _REPLICATE_AVAILABLE = True
except ImportError:
    _replicate = None
    _REPLICATE_AVAILABLE = False

load_dotenv()
_API_KEY: str = os.getenv("REPLICATE_API_TOKEN", "")

_DIALOGUE_MAX_CHARS = 200


class DialogueSystem:
    _MAX_CALLS = 3
    _PERIOD    = 30.0  # 3 messages max par 30 secondes

    def __init__(self, game_view: BaseGameView):
        self.game_view = game_view
        self._rate_calls: list[float] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ public

    def on_text(self, text: str) -> None:
        gv = self.game_view
        if gv.is_typing and not gv.waiting_response:
            if len(gv.current_input) < _DIALOGUE_MAX_CHARS:
                gv.current_input += text

    def request_response(self, message: str, pnj) -> None:
        """Lance l'appel API dans un thread séparé pour ne pas bloquer le jeu."""
        gv = self.game_view
        if gv.waiting_response:
            return
        if self._is_rate_limited():
            gv.last_response = "Je parle trop souvent. Attends un moment..."
            return
        clean = message.strip()
        if not clean:
            return
        gv.waiting_response = True
        thread = threading.Thread(target=self._fetch_response, args=(clean, pnj), daemon=True)
        thread.start()

    def draw_dialogue_box(self) -> None:
        gv = self.game_view
        if not (gv.is_typing or gv.last_response):
            return

        PAD      = 16
        BOX_H    = 180
        SEP_H    = 36
        RESP_H   = BOX_H - SEP_H
        BG       = (15, 15, 40, 230)
        HINT_COL = (150, 180, 230)
        text_w   = WINDOW_WIDTH - 2 * PAD - 2 * PAD

        box_l = PAD
        box_r = WINDOW_WIDTH - PAD
        box_b = PAD
        box_t = PAD + BOX_H
        sep_y = box_b + SEP_H

        # Fond principal
        arcade.draw_lrbt_rectangle_filled(box_l, box_r, box_b, box_t, BG)
        arcade.draw_lrbt_rectangle_outline(box_l, box_r, box_b, box_t, arcade.color.WHITE, 1)
        arcade.draw_line(box_l + 4, sep_y, box_r - 4, sep_y, arcade.color.WHITE, 1)

        # Zone joueur (bas)
        player_nom = gv.player_sprite.nom
        cursor     = "_" if not gv.waiting_response else ""
        input_text = f"{player_nom} : {gv.current_input}{cursor}"
        arcade.draw_text(input_text, box_l + PAD, sep_y - SEP_H / 2,
                         arcade.color.WHITE, 13,
                         anchor_y="center", font_name=KENNY,
                         width=int(text_w), multiline=False)
        arcade.draw_text("[Entrée] Envoyer", box_r - PAD, box_b + 10,
                         HINT_COL, 10, anchor_x="right", font_name=KENNY)

        # Zone PNJ (haut)
        pnj = gv.current_pnj
        if pnj:
            arcade.draw_text(pnj.nom, box_l + PAD, box_t - 14,
                             arcade.color.ORANGE, 13, bold=True,
                             anchor_y="center", font_name=KENNY)
        if gv.waiting_response:
            arcade.draw_text("...", box_l + PAD, sep_y + RESP_H / 2,
                             HINT_COL, 14, anchor_y="center", font_name=KENNY)
        elif gv.last_response and pnj:
            resp_t = arcade.Text(gv.last_response,
                                 box_l + PAD, box_t - 28,
                                 arcade.color.WHITE, 13,
                                 font_name=KENNY,
                                 width=int(text_w),
                                 multiline=True,
                                 anchor_y="top")
            resp_t.draw()

    # ------------------------------------------------------------------ private

    def _is_rate_limited(self) -> bool:
        now = time.monotonic()
        with self._lock:
            self._rate_calls = [t for t in self._rate_calls if now - t < self._PERIOD]
            if len(self._rate_calls) >= self._MAX_CALLS:
                return True
            self._rate_calls.append(now)
            return False

    def _fetch_response(self, message: str, pnj) -> None:
        try:
            response = self._call_api(message, pnj)
        except Exception as e:
            print(f"[DialogueSystem] Erreur API : {e}")
            response = "Désolé, je suis occupé en ce moment..."
        self.game_view.last_response = response
        self.game_view.waiting_response = False

    def _call_api(self, message: str, pnj) -> str:
        if not _REPLICATE_AVAILABLE:
            return "[module replicate non installé]"
        if not _API_KEY:
            return "[clé API REPLICATE_API_TOKEN manquante dans .env]"

        os.environ["REPLICATE_API_TOKEN"] = _API_KEY
        nom = pnj.nom
        if nom in IbmI_personnage.personnages:
            d = IbmI_personnage.personnages[nom]
            system_prompt = (
                f"Tu es {d['nom']}, un personnage {d.get('type', 'mystérieux')}.\n"
                f"Ton métier est {d.get('metier', 'inconnu')}.\n"
                f"Tu as une personnalité {d.get('personnalite', 'mystérieuse')}.\n"
                f"Tes hobbies sont {d.get('hobbie', 'inconnus')}.\n"
                f"Réponds en 1-2 phrases, sans émoji."
            )
        else:
            system_prompt = "Tu es un personnage mystérieux. Reste vague et bref."

        full_prompt = f"{system_prompt}\nJoueur: {message}\n{nom}:"
        output = _replicate.run(
            "openai/gpt-4o-mini",
            input={"prompt": full_prompt, "max_new_tokens": 250, "temperature": 0.7},
        )
        return "".join(output)
