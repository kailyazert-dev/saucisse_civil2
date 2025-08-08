import arcade

class Objet(arcade.Sprite):
    def __init__(self, image_path, scale):
        super().__init__(image_path, scale)

class Progresseur(Objet):
    def __init__(self, image_path, scale, nom, stat_cible):
        super().__init__(image_path, scale)
        self.nom = nom
        self.stat_cible = stat_cible

    def utiliser(self, joueur):
        joueur.start_up(self) 
          

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