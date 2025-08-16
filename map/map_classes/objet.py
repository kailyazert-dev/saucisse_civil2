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