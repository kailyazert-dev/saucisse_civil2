import arcade

class Objet(arcade.Sprite):
    def __init__(self, image_path, scale):
        super().__init__(image_path, scale)

class Progresseur(Objet):
    def __init__(self, image_path, scale, nom, stat_cible, stat_min=0, stat_max=100):
        super().__init__(image_path, scale)
        self.nom = nom
        self.stat_cible = stat_cible
        self.stat_min = stat_min
        self.stat_max = stat_max

    def utiliser(self, player):
        player_level_stat = getattr(player.humain, self.stat_cible)
        if self.stat_min <= player_level_stat < self.stat_max:
            player.start_up(self.stat_cible, self)

    def get_nom(self):
        return(f"{self.nom}")   
          

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