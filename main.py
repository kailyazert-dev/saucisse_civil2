import arcade
from map.map_manager import MapManager
from quests.quest_manager import QuestManager
from character.character_manager import CharacterManager

def main():
    # Création du gestionnaire de quêtes
    quest_manager = QuestManager()

    # Création du gestionnaire des character
    character_manager = CharacterManager(quest_manager)

    # Création du gestionnaire de maps
    MapManager(quest_manager, character_manager)

    # Lance la boucle de jeu arcade
    arcade.run()

if __name__ == "__main__":
    main()
