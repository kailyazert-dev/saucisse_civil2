from __future__ import annotations
import arcade


class Objet(arcade.Sprite):
    def __init__(self, image_path, scale):
        super().__init__(image_path, scale)

class UpStat(Objet):
    def __init__(self, image_path, scale, name, stat_cible, stat_min=0, stat_max=100):
        super().__init__(image_path, scale)
        self.name = name
        self.stat_cible = stat_cible
        self.stat_min = stat_min
        self.stat_max = stat_max

    def utiliser(self, player, character_manager):
        player_level_stat = getattr(player.humain, self.stat_cible)
        if self.stat_min <= player_level_stat < self.stat_max:
            character_manager.start_up(self)

    def get_name(self):
        return(f"{self.name}")   
          
class UpStatCollection(arcade.Sprite):
    def __init__(self, image_path, scale, name):
        super().__init__(image_path, scale)
        self.name = name
        self.upStats = []

    def get_name(self):
        return(f"{self.name}")  
    
    def add_upStats(self, upstat):
        self.upStats.append(upstat)

    def remove_upStats(self, upstat):
        self.upStats.remove(upstat)

    def get_all_upStats(self):
        return self.upStats 










class MapActionObject(Objet):
    """Objet lié à un objectif de type map_action.
    Affiche son nom uniquement quand l'objectif est actif, et le complète à ENTER."""

    def __init__(self, image_path, scale, name: str, objective_name: str):
        super().__init__(image_path, scale)
        self.name = name
        self.objective_name = objective_name  # Doit correspondre à obj.name dans quests.json

    def get_name(self) -> str:
        return self.name

    def is_available(self, quest_manager) -> bool:
        """Retourne True si l'objectif lié est en cours et non terminé."""
        if quest_manager is None or quest_manager.arc is None:
            return False
        for quest in quest_manager.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type in ("map_action", "test") and obj.name == self.objective_name and obj.status != "t":
                    return True
        return False


class Item(Objet):
    def __init__(self, image_path, scale, stat_cible, valeur, slot):
        super().__init__(image_path, scale)
        self.stat_cible = stat_cible
        self.valeur = valeur
        self.slot = slot

    def equiper(self, joueur):
        joueur.equiper(self)

    def retirer(self, joueur):
        joueur.retirer(self)    