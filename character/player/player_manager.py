from __future__ import annotations
import os
import json
import shutil
import datetime
from typing import Protocol
from assets.param_map import PLAYER_SCALING, MAP_WIDTH, MAP_HEIGHT
from character.player.player import Player
from character.pnj.pnj import PNJ
from character.character_base import Humain
from character.equipment.weapon import Weapon
import utils.paths as paths


_CHARACTER_DEFAULTS: dict[str, object] = {
    "nom": "Joueur",
    "force": 0.1,
    "vitesse": 0.1,
    "endurance": 0.1,
    "mathematique": 0.14,
    "logique": 0.14,
    "rpg": 0.1,
    "music": 0.1,
    "langue": 0.1,
    "sociabilite": 0.1,
    "x": 0,
    "y": 0,
    "weapon": None,
}

_AUTO_SAVE_INTERVAL: float = 30.0


class _HasStatCible(Protocol):
    stat_cible: str
    stat_min:   float
    stat_max:   float


class CharacterManager:
    def __init__(self, quest_manager, x: int = 0, y: int = 0) -> None:
        self.base_dir      = os.path.dirname(os.path.abspath(__file__))
        self.x             = x
        self.y             = y
        self.quest_manager = quest_manager
        self.player:       Player | None = None

        self.up:               bool             = False
        self.stat_to_up:       str | None       = None
        self.time_since_last_up_increase: float = 0.0
        self.up_increase_interval:        float = 2.0
        self.current_progresseur: _HasStatCible | None = None

        self._stats_dirty:    bool  = False
        self._auto_save_timer: float = 0.0

        self._pending_spawn: tuple[float, float] | None = None

        self.PNJ: list[PNJ] = []

        self.character_file = self._resolve_save_file()
        self.load_player(self.x, self.y, self.quest_manager)
        self.animation = AnimationManager(self)

    # ------------------------------------------------------------------ save

    def _resolve_save_file(self) -> str:
        save_path = os.path.join(paths.get_save_dir(), "character_save.json")
        if os.path.exists(save_path):
            return save_path

        old_path = os.path.join(self.base_dir, "character_save_file", "character_save.json")
        if os.path.exists(old_path):
            shutil.copy(old_path, save_path)
            print(f"[OK] Sauvegarde migrée vers {save_path}")
            return save_path

        self._write_json(save_path, _CHARACTER_DEFAULTS)
        print(f"[OK] Nouvelle sauvegarde créée : {save_path}")
        return save_path

    def _write_json(self, path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _validate_data(self, data: dict) -> dict:
        return {key: data.get(key, default) for key, default in _CHARACTER_DEFAULTS.items()}

    def _flush_save(self) -> None:
        if self._stats_dirty:
            self.save_player()
            self._stats_dirty = False
        self._auto_save_timer = 0.0

    # ------------------------------------------------------------------ player

    def load_player(self, x: int, y: int, quest_manager, scale: float = PLAYER_SCALING) -> None:
        try:
            with open(self.character_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Sauvegarde illisible ({e}), utilisation des valeurs par défaut.")
            raw = {}

        data   = self._validate_data(raw)
        humain = Humain(
            force=data["force"],
            vitesse=data["vitesse"],
            endurance=data["endurance"],
            mathematique=data["mathematique"],
            logique=data["logique"],
            rpg=data["rpg"],
            music=data["music"],
            langue=data["langue"],
            sociabilite=data["sociabilite"],
            x=data["x"],
            y=data["y"],
        )
        player           = Player(humain, data["nom"],
                                  paths.asset("assets/images/player_d.png"),
                                  quest_manager, self, scale)
        player.center_x  = x
        player.center_y  = y
        weapon_data = data.get("weapon")
        if weapon_data:
            player.weapon = Weapon(
                weapon_data["name"],
                weapon_data["damage_min"],
                weapon_data["damage_max"],
                tuple(weapon_data["bullet_color"]),
            )
        self.player = player

    def reset(self) -> None:
        if self.player is None:
            return
        h = self.player.humain
        for key in ("force", "vitesse", "endurance", "mathematique", "logique",
                    "rpg", "music", "langue", "sociabilite"):
            setattr(h, key, _CHARACTER_DEFAULTS[key])
        self.player.center_x = 745
        self.player.center_y = 970
        self._write_json(self.character_file, _CHARACTER_DEFAULTS)
        print("[RESET] Personnage réinitialisé.")

    def consume_pending_spawn(self) -> tuple[float, float] | None:
        spawn = self._pending_spawn
        self._pending_spawn = None
        return spawn

    def save_player(self) -> None:
        if self.player is None:
            return
        if os.path.exists(self.character_file):
            shutil.copy(self.character_file, self.character_file + ".bak")
        p = self.player
        w = p.weapon
        stats = {
            "nom":          p.nom,
            "force":        p.humain.force,
            "vitesse":      p.humain.vitesse,
            "endurance":    p.humain.endurance,
            "mathematique": p.humain.mathematique,
            "rpg":          p.humain.rpg,
            "logique":      p.humain.logique,
            "music":        p.humain.music,
            "langue":       p.humain.langue,
            "sociabilite":  p.humain.sociabilite,
            "x":            p.humain.x,
            "y":            p.humain.y,
            "weapon": {
                "name":         w.name,
                "damage_min":   w.damage_min,
                "damage_max":   w.damage_max,
                "bullet_color": list(w.bullet_color),
            } if w is not None else None,
        }
        self._write_json(self.character_file, stats)

    def get_all_saves(self) -> list:
        saves_file = os.path.join(paths.get_save_dir(), "saves.json")
        try:
            with open(saves_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_slot(self, name: str, map_name: str) -> None:
        self.save_player()
        self.quest_manager.save_progress()
        try:
            with open(self.character_file, "r", encoding="utf-8") as f:
                char_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            char_data = {}
        if self.player:
            char_data["x"] = self.player.center_x
            char_data["y"] = self.player.center_y
        try:
            with open(self.quest_manager.quest_save_file, "r", encoding="utf-8") as f:
                quests_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            quests_data = []
        saves = self.get_all_saves()
        saves = [s for s in saves if s["name"] != name]
        saves.append({
            "name":      name,
            "map":       map_name,
            "date":      datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "character": char_data,
            "quests":    quests_data,
        })
        saves_file = os.path.join(paths.get_save_dir(), "saves.json")
        os.makedirs(os.path.dirname(saves_file), exist_ok=True)
        with open(saves_file, "w", encoding="utf-8") as f:
            json.dump(saves, f, ensure_ascii=False, indent=4)

    def delete_slot(self, name: str) -> None:
        saves = self.get_all_saves()
        saves = [s for s in saves if s["name"] != name]
        saves_file = os.path.join(paths.get_save_dir(), "saves.json")
        os.makedirs(os.path.dirname(saves_file), exist_ok=True)
        with open(saves_file, "w", encoding="utf-8") as f:
            json.dump(saves, f, ensure_ascii=False, indent=4)

    def load_slot(self, slot: dict) -> str:
        char_data  = slot.get("character", {})
        quest_data = slot.get("quests", [])
        self._write_json(self.character_file, char_data)
        self.quest_manager.load_from_data(quest_data)
        if self.player:
            data = self._validate_data(char_data)
            h = self.player.humain
            for key in ("force", "vitesse", "endurance", "mathematique",
                        "logique", "rpg", "music", "langue", "sociabilite"):
                setattr(h, key, data[key])
            weapon_data = char_data.get("weapon")
            if weapon_data:
                self.player.weapon = Weapon(
                    weapon_data["name"],
                    weapon_data["damage_min"],
                    weapon_data["damage_max"],
                    tuple(weapon_data["bullet_color"]),
                )
            else:
                self.player.weapon = None
            self._pending_spawn = (char_data.get("x", 745.0), char_data.get("y", 970.0))
        return slot.get("map", "home")

    # ------------------------------------------------------------------ stat upgrade

    def start_up(self, objet_progresseur: _HasStatCible | None = None) -> None:
        self.up                          = True
        self.stat_to_up                  = objet_progresseur.stat_cible
        self.time_since_last_up_increase = 0.0
        self.current_progresseur         = objet_progresseur
        self._auto_save_timer            = 0.0

    def stop_up(self) -> None:
        self.up = False
        self._flush_save()

    def update_player_stats(self, delta_time: float = 1 / 60) -> None:
        player = self.player
        if not player or not self.up:
            return

        self._auto_save_timer += delta_time
        if self._auto_save_timer >= _AUTO_SAVE_INTERVAL:
            self._flush_save()

        self.time_since_last_up_increase += delta_time
        if self.time_since_last_up_increase < self.up_increase_interval:
            return
        self.time_since_last_up_increase = 0.0

        if not self.stat_to_up:
            return

        current = getattr(player.humain, self.stat_to_up, None)
        if current is None:
            print(f"[WARN] Stat inconnue : '{self.stat_to_up}'")
            return

        new_value = round(current + 0.002, 3)
        if self.current_progresseur and new_value > self.current_progresseur.stat_max:
            print(f"[STOP] {self.stat_to_up} a atteint la limite ({self.current_progresseur.stat_max:.3f})")
            self.stop_up()
            return

        setattr(player.humain, self.stat_to_up, new_value)
        self._stats_dirty = True
        print(f"{player.nom} +0.002 {self.stat_to_up} → {new_value:.3f}")
        if player.quest_manager:
            player.quest_manager.check_objective(self.stat_to_up, new_value)


# ---------------------------------------------------------------------------
class AnimationManager:
    def __init__(self, character_manager: CharacterManager) -> None:
        self.manager = character_manager

    def update(self, delta_time: float = 1 / 60) -> None:
        player = self.manager.player
        if player is None:
            return

        player.center_x += player.change_x
        player.center_y += player.change_y
        super(Player, player).update(delta_time)

        if player.left < 0:
            player.left = 0
        elif player.right > MAP_WIDTH - 1:
            player.right = MAP_WIDTH - 1
        if player.bottom < 0:
            player.bottom = 0
        elif player.top > MAP_HEIGHT - 1:
            player.top = MAP_HEIGHT - 1

        if player.reading:
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.reading_texture_switch_interval:
                self._toggle_read_texture(player)
                player.time_since_last_texture_change = 0.0
        elif player.change_x != 0 or player.change_y != 0:
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.walking_texture_switch_interval:
                self._toggle_walk_texture(player)
                player.time_since_last_texture_change = 0.0
        else:
            player.texture = player.textures[player.direction]

    def _toggle_walk_texture(self, player: Player) -> None:
        player._walk_frame = 1 - player._walk_frame
        textures = player.textures_walk.get(player.direction, player.textures_walk["down"])
        player.texture = textures[player._walk_frame]

    def _toggle_read_texture(self, player: Player) -> None:
        player.read_texture_index = (player.read_texture_index + 1) % len(player.textures_read)
        player.texture = player.textures_read[player.read_texture_index]
