class Environnement:
    def __init__(self, nom, tension_sociale, densite_sociale, regles_sociale):
        self.nom = nom
        self.tension_sociale = tension_sociale
        self.densite_sociale = densite_sociale
        self.regles_sociale = regles_sociale

    def get_stat(self):
        return(
            f"Lieux : {self.nom}\n"
            f"Sociabilisation : {self.tension_sociale}\n"
            f"Densité: {self.densite_sociale}\n"
            f"régime : {self.regles_sociale}"
        )    