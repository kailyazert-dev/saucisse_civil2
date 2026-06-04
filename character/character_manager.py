from __future__ import annotations
import os
import json
import shutil
from itertools import combinations
from assets.param_map import PLAYER_SCALING, MAP_WIDTH, MAP_HEIGHT
from character.character_classes import Player, PNJ, Humain
import utils.paths as paths


_CHARACTER_DEFAULTS: dict = {
    "nom": "Joueur",
    "charisme": 0.1,
    "rigidite": 0.1,
    "intensite_boof": 0.1,
    "receptif_boof": 0.1,
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
}


class CharacterManager:
    def __init__(self, quest_manager, x: int = 0, y: int = 0):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.x = x
        self.y = y
        self.quest_manager = quest_manager
        self.player: Player | None = None

        self.up = False
        self.stat_to_up: str | None = None
        self.time_since_last_up_increase = 0.0
        self.up_increase_interval = 2.0
        self.current_progresseur = None

        self.PNJ: list[PNJ] = []

        self.character_file = self._resolve_save_file()
        self.load_player(self.x, self.y, self.quest_manager)
        self.animation = AnimationManager(self)

    # ------------------------------------------------------------------ save

    def _resolve_save_file(self) -> str:
        """Retourne le chemin AppData du fichier de sauvegarde.
        Migre automatiquement depuis l'ancien emplacement si nécessaire."""
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
        """Complète les champs manquants avec les valeurs par défaut."""
        return {key: data.get(key, default) for key, default in _CHARACTER_DEFAULTS.items()}

    # ------------------------------------------------------------------ player

    def load_player(self, x: int, y: int, quest_manager, scale: float = PLAYER_SCALING) -> None:
        try:
            with open(self.character_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Sauvegarde illisible ({e}), utilisation des valeurs par défaut.")
            raw = {}

        data = self._validate_data(raw)
        humain = Humain(
            charisme=data["charisme"],
            rigidite=data["rigidite"],
            beauf=data["intensite_boof"],
            receptif_beauf=data["receptif_boof"],
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
        player = Player(humain, data["nom"], paths.asset("assets/images/player_d.png"), quest_manager, self, scale)
        player.center_x = x
        player.center_y = y
        self.player = player

    def reset(self) -> None:
        if self.player is None:
            return
        h = self.player.humain
        for key in ("charisme", "rigidite", "intensite_boof", "receptif_boof",
                    "force", "vitesse", "endurance", "mathematique", "logique",
                    "rpg", "music", "langue", "sociabilite"):
            setattr(h, key, _CHARACTER_DEFAULTS[key])
        self.player.center_x = 745
        self.player.center_y = 970
        self._write_json(self.character_file, _CHARACTER_DEFAULTS)
        print("[RESET] Personnage réinitialisé.")

    def save_player(self) -> None:
        if self.player is None:
            return
        # Backup avant écrasement
        if os.path.exists(self.character_file):
            shutil.copy(self.character_file, self.character_file + ".bak")
        p = self.player
        stats = {
            "nom": p.nom,
            "charisme": p.humain.charisme,
            "rigidite": p.humain.rigidite,
            "intensite_boof": p.humain.intensite_boof,
            "receptif_boof": p.humain.receptif_boof,
            "force": p.humain.force,
            "vitesse": p.humain.vitesse,
            "endurance": p.humain.endurance,
            "mathematique": p.humain.mathematique,
            "rpg": p.humain.rpg,
            "logique": p.humain.logique,
            "music": p.humain.music,
            "langue": p.humain.langue,
            "sociabilite": p.humain.sociabilite,
            "x": p.humain.x,
            "y": p.humain.y,
        }
        self._write_json(self.character_file, stats)

    # ------------------------------------------------------------------ stat upgrade

    def start_up(self, objet_progresseur=None) -> None:
        self.up = True
        self.stat_to_up = objet_progresseur.stat_cible
        self.time_since_last_up_increase = 0.0
        self.current_progresseur = objet_progresseur

    def stop_up(self) -> None:
        self.up = False

    def update_player_stats(self, delta_time: float = 1 / 60) -> None:
        player = self.player
        if not player or not self.up:
            return
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
        print(f"{player.nom} +0.002 {self.stat_to_up} → {new_value:.3f}")
        if player.quest_manager:
            player.quest_manager.check_objective(self.stat_to_up, new_value)
        self.save_player()


class AnimationManager:
    def __init__(self, character_manager: CharacterManager):
        self.manager = character_manager

    def update(self, delta_time: float = 1 / 60) -> None:
        player = self.manager.player
        if player is None:
            return

        player.center_x += player.change_x
        player.center_y += player.change_y
        super(Player, player).update(delta_time)

        # Limites de la carte
        if player.left < 0:
            player.left = 0
        elif player.right > MAP_WIDTH - 1:
            player.right = MAP_WIDTH - 1
        if player.bottom < 0:
            player.bottom = 0
        elif player.top > MAP_HEIGHT - 1:
            player.top = MAP_HEIGHT - 1

        # Animation
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
        player.walk_texture_index = 1 - player.walk_texture_index
        direction_map = {
            "up": player.textures_up,
            "down": player.textures_down,
            "left": player.textures_left,
            "right": player.textures_right,
        }
        textures = direction_map.get(player.direction, player.textures_down)
        player.texture = textures[player.walk_texture_index]

    def _toggle_read_texture(self, player: Player) -> None:
        player.read_texture_index = (player.read_texture_index + 1) % len(player.textures_read)
        player.texture = player.textures_read[player.read_texture_index]


class Interaction:
    """Simule la transmission de 'boofitude' entre personnages selon l'environnement."""

    def __init__(self, participants, environnement):
        self.participants = participants
        self.environnement = environnement

    def coeff_regle_sociale(self) -> float:
        coeffs = {
            "informelles": 1.25, "formelles": 0.25,
            "sociale": 1.50, "liberales": 1.10,
            "restrictives": 0.75, "neutres": 1.0,
        }
        return coeffs.get(self.environnement.regles_sociale.lower(), 1.0)

    def coeff_influence_env(self) -> float:
        return (1 - self.environnement.tension_sociale) * self.environnement.densite_sociale * self.coeff_regle_sociale()

    def simuler(self) -> None:
        influence_env = self.coeff_influence_env()
        for a, b in combinations(self.participants, 2):
            if a.charisme == b.charisme:
                continue
            source, cible = (a, b) if a.charisme > b.charisme else (b, a)
            if source.intensite_boof > cible.intensite_boof:
                self._transmettre(source, cible, influence_env)
            else:
                self._guerir(source, cible, influence_env)

    def _transmettre(self, source, cible, influence_env: float) -> None:
        if source.intensite_boof <= cible.intensite_boof:
            return
        coef = source.intensite_boof * (0.5 + 0.5 * cible.receptif_boof) * influence_env
        gain = coef * (1 - cible.rigidite) * 0.1
        cible.intensite_boof = round(min(cible.intensite_boof + gain, 1.0), 2)

    def _guerir(self, source, cible, influence_env: float) -> None:
        if source.intensite_boof >= cible.intensite_boof:
            return
        coef = (1 - source.intensite_boof) * (0.5 + 0.5 * cible.receptif_boof) * influence_env
        gain = coef * (1 - cible.rigidite) * 0.1
        cible.intensite_boof = round(max(cible.intensite_boof - gain, 0.0), 2)
