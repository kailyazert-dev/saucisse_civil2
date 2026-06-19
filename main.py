import arcade
from world.scene.scene_manager import SceneManager
from quests.quest_manager import QuestManager
from character.player.player_manager import CharacterManager

def main():
    # Création du gestionnaire de quêtes
    quest_manager = QuestManager()

    # Création du gestionnaire des character
    character_manager = CharacterManager(quest_manager)

    # Création du gestionnaire de maps
    SceneManager(quest_manager, character_manager)

    # Lance la boucle de jeu arcade
    arcade.run()

if __name__ == "__main__":
    main()
