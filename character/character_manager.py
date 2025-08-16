import random
import os
import json
from itertools import combinations
from assets.param_map import PLAYER_SCALING, MAP_WIDTH, MAP_HEIGHT
from character.character_classes import Player, PNJ, Humain

class CharacterManager:
    def __init__(self, quest_manager, character_save_file: str = "character_save.json", x=0, y=0):
        # Répertoire du fichier actuel
        self.base_dire = os.path.dirname(os.path.abspath(__file__))

        # 📁 Dossiers
        self.character_file_dir = os.path.join(self.base_dire, "character_save_file")

        # 📄 Chemins des fichiers
        self.character_file = os.path.join(self.character_file_dir, character_save_file)

        # Player
        self.x = x
        self.y = y
        self.quest_manger = quest_manager
        self.player: Player | None = None
        # Pour les augmentations
        self.up = False
        self.stat_to_up = None
        self.time_since_last_up_increase = 0.0
        self.up_increase_interval = 2.0
        self.current_progresseur = None

        # Liste des PNJs
        self.PNJ: list[PNJ] = []

        # Chargement du player
        self.load_player(self.x, self.y, self.quest_manger)

        self.animation = AnimationManager(self)

    """ Pour charger le player. """
    def load_player(self, x, y, quest_manger, scale=PLAYER_SCALING):
        with open(self.character_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

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
            sociabilité=data["sociabilité"],
            x = data["x"],                                                         
            y = data["y"]
        )
        image_file = 'assets/images/player_d.png'
        player = Player(humain, data["nom"], image_file, quest_manger, self, scale)
        player.center_x = x
        player.center_y = y
        self.player = player       

    """ Pour sauvegarder les stats du player. """
    def save_player(self):
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
            "sociabilité": p.humain.sociabilité,
            "x": p.humain.x,
            "y": p.humain.y,
        }

        with open(self.character_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)  



    """Démarre l’augmentation progressive des stats."""
    def start_up(self, objet_progresseur=None):
        self.up = True
        self.stat_to_up = objet_progresseur.stat_cible
        self.time_since_last_up_increase = 0.0
        self.current_progresseur = objet_progresseur

    """Arrête l’augmentation des stats."""
    def stop_up(self):
        self.up = False       

    """Gère l'augmentation progressive des stats du joueur"""
    def update_player_stats(self, delta_time: float = 1/60):
        player = self.player
        if player and self.up:
            self.time_since_last_up_increase += delta_time
            if self.time_since_last_up_increase >= self.up_increase_interval:
                if self.stat_to_up:
                    current_value = getattr(player.humain, self.stat_to_up, None)
                    if current_value is not None:
                        new_value = round(current_value + 0.002, 3)
                        player.quest_manager.check_objective(self.stat_to_up, new_value)
                        if self.current_progresseur:
                            max_value = self.current_progresseur.stat_max
                            if new_value > max_value:
                                print(f"🚫 {self.stat_to_up} a atteint la limite ({max_value:.3f})")
                                self.stop_up()
                                return

                        setattr(player.humain, self.stat_to_up, new_value)
                        print(f"{player.nom} a gagné +0.002 en {self.stat_to_up} → {new_value:.3f}")
                        self.save_player()
                    else:
                        print(f"⚠️ La stat '{self.stat_to_up}' n'existe pas.")
                self.time_since_last_up_increase = 0.0        

class AnimationManager:
    def __init__(self, character_manager, delta_time: float = 1/60):
        self.manager = character_manager
        self.delta_time = delta_time

    def update(self, delta_time: float = 1/60):
        player = self.manager.player

        # --- Déplacement ---
        player.center_x += player.change_x
        player.center_y += player.change_y

        super(Player, player).update(self.delta_time)

        # Limites de la carte
        if player.left < 0:
            player.left = 0
        elif player.right > MAP_WIDTH - 1:
            player.right = MAP_WIDTH - 1

        if player.bottom < 0:
            player.bottom = 0
        elif player.top > MAP_HEIGHT - 1:
            player.top = MAP_HEIGHT - 1

        # --- Animation ---
        if player.reading:
            # Animation de lecture
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.reading_texture_switch_interval:
                self.toggle_read_texture(player)
                player.time_since_last_texture_change = 0.0
        elif player.change_x != 0 or player.change_y != 0:
            # Animation de marche
            player.time_since_last_texture_change += delta_time
            if player.time_since_last_texture_change >= player.walking_texture_switch_interval:
                self.toggle_walk_texture(player)
                player.time_since_last_texture_change = 0.0
        else:
            # Joueur immobile (ni marche ni lecture)
            player.texture = player.textures[player.direction]

    # --- Animation marche ---
    def toggle_walk_texture(self, player):
        player.walk_texture_index = 1 - player.walk_texture_index
        if player.direction == "up":
            player.texture = player.textures_up[player.walk_texture_index]
        elif player.direction == "down":
            player.texture = player.textures_down[player.walk_texture_index]
        elif player.direction == "left":
            player.texture = player.textures_left[player.walk_texture_index]
        elif player.direction == "right":
            player.texture = player.textures_right[player.walk_texture_index]

    # --- Animation lecture ---
    def toggle_read_texture(self, player):
        player.read_texture_index = (player.read_texture_index + 1) % len(player.textures_read)
        player.texture = player.textures_read[player.read_texture_index]       


class Interaction:
    def __init__(self, participants, environnement):
        self.participants = participants
        self.environnement = environnement
    
    # Retourne un coeficient par rapport à au régime sociale
    def coeff_regle_sociale(self):
        regle = self.environnement.regles_sociale.lower()
        coeffs = {
            "informelles": 1.25,
            "formelles": 0.25,
            "sociale": 1.50,
            "liberales": 1.10,
            "restrictives": 0.75,
            "neutres": 1.0
        }
        return coeffs.get(regle, 1.0)
    
    # Calcule un facteur basé sur tension, densité, et régime sociale
    def coeff_influence_env(self):
        coeff_regle = self.coeff_regle_sociale()
        return (1 - self.environnement.tension_sociale) * self.environnement.densite_sociale * coeff_regle

    # Simule l'interaction
    def simuler(self):
        influence_env = self.coeff_influence_env()

        for a, b in combinations(self.participants, 2):
            if a.charisme == b.charisme:
                continue  # Si charisme égal, pas d'interaction

            # Déterminer source et cible selon le charisme
            source, cible = (a, b) if a.charisme > b.charisme else (b, a)

            if source.intensite_boof > cible.intensite_boof:
                self.transmettre_boofitude(source, cible, influence_env)
            else:
                self.guerir_boofitude(source, cible, influence_env)

    # Modifie la boofitude
    def transmettre_boofitude(self, source, cible, influence_env):
        if source.intensite_boof <= cible.intensite_boof:
            return  # Pas de différence → pas d'influence

        # Coefficient de transmission :
        # - source très boof = fort
        # - cible très réceptive = +++
        # base_influence = source.charisme * cible.receptif_boof * source.intensite_boof * influence_env
        coef_transmission = source.intensite_boof * (0.5 + 0.5 * cible.receptif_boof)
        
        # Application de l'environnement
        coef_transmission *= influence_env

        # Calcul du gain selon la rigidité de la cible
        # Plus la rigidité est basse, plus le gain est grand
        gain = coef_transmission * (1 - cible.rigidite) * 0.1
        # gain = 0.1 * base_influence

        cible.intensite_boof = round(min(cible.intensite_boof + gain, 1.0),2)    
        
    # Modifie la boofitude
    def guerir_boofitude(self, source, cible, influence_env):
        if source.intensite_boof >= cible.intensite_boof:
            return  # Pas de différence → pas d'influence

        # Coefficient de guérison :
        # - source peu boof = fort
        # - cible peu réceptive = --
        coef_guerison = (1 - source.intensite_boof) * (0.5 + 0.5 * cible.receptif_boof)
        coef_guerison *= influence_env

        # Gain selon rigidité (inversement proportionnel)
        gain = coef_guerison * (1 - cible.rigidite) * 0.1

        cible.intensite_boof = round(max(cible.intensite_boof - gain, 0.0), 2)     