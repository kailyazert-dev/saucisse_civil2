import random
from itertools import combinations

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