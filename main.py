import arcade
from map.map_manager import MapManager
from classes import environnement
from assets.param_map import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from quests.quest_manager import QuestManager
from character.character_manager import CharacterManager

def main():

    # Création d'une instance d'Environnement
    travaille = environnement.Environnement("Bureau", tension_sociale=0.7, densite_sociale=0.5, regles_sociale="formelles")
    bar = environnement.Environnement("Bar", tension_sociale=0.2, densite_sociale=0.8, regles_sociale="informelles")

    # Création du gestionnaire de quêtes
    quest_manager = QuestManager()

    # Gestionnaire des character
    character_manager = CharacterManager(quest_manager)

    # Crée la fenêtre arcade
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=False)

    manager = MapManager(window, travaille, quest_manager, character_manager)
    manager.load_initial_map()

    # Lance la boucle de jeu arcade
    arcade.run()

if __name__ == "__main__":
    main()
