import json
import os
from .quest_classes import Arc, Quest, Objective

class QuestManager:
    def __init__(self, quest_file: str = "quests.json", quests_save_file: str = "quests_save.json", quests_default_file: str = "quests_default_save.json"):
        import os

        # Répertoire du fichier actuel
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # 📁 Dossiers
        self.quests_file_dir = os.path.join(self.base_dir, "quests_file")
        self.quests_save_dir = os.path.join(self.base_dir, "quests_save_file")

        # 📄 Chemins des fichiers
        self.quest_file = os.path.join(self.quests_file_dir, quest_file)  # Liste de toutes les quêtes
        self.quest_save_file = os.path.join(self.quests_save_dir, quests_save_file)  # Sauvegarde en cours
        self.quest_default_save_file = os.path.join(self.quests_save_dir, quests_default_file)  # Sauvegarde par défaut

        # Arc et quête en cours
        self.arc: Arc | None = None                      # L'arc en cours

        # Quêtes secondaires
        self.quest_trs: list[Quest] = []                 # Liste des quêtes secondaires

        # Charger la progression
        saved_data = self.get_save_progress()
        if saved_data:
            self.load_progress(saved_data)

    """Pour récupérer les quêtes en cour depuis la sauvegarde"""
    def get_save_progress(self) -> list[dict] | None:

        try:
            # 📌 Si la sauvegarde est absente ou vide → on la crée à partir du fichier par défaut
            if not os.path.exists(self.quest_save_file) or os.path.getsize(self.quest_save_file) == 0:
                with open(self.quest_default_save_file, "r", encoding="utf-8") as f:
                    default_save = json.load(f)
                with open(self.quest_save_file, "w", encoding="utf-8") as f:
                    json.dump(default_save, f, indent=4, ensure_ascii=False)
                return default_save    

            # 📌 Lecture de la sauvegarde
            with open(self.quest_save_file, "r", encoding="utf-8") as f:
                return json.load(f)

            # self.load_progress()
        except (FileNotFoundError, json.JSONDecodeError):
            print("Nouvelle partie lancée. Un fichier de sauvegarde a été créé.")
            return None

    """Pour charger les quêtes qui provient de la sauvegarde"""
    def load_progress(self, saved_data: list[dict]) -> None:

        # Nettoie    
        self.arc = None

        # Trouver l'arc en cours
        arc_data = saved_data[0] if saved_data and saved_data[0].get("status") == "ec" else None
        if arc_data is None:
            print("Aucun arc ec trouvé dans le fichier de sauvegarde.")
            return

        self.arc = self._create_arc_from_dict(arc_data)

    """Pour sauvegarder la progression des quêtes"""
    def save_progress(self) -> None:
        # Pour creer un objectif 
        def objective_to_dict(obj):
            return {
                "name": obj.name,
                "description": obj.description,
                "status": obj.status,
                "type": obj.type,
                "stat_key": obj.stat_key,
                "validator": obj.validator
            }
        # Pour creer une quête
        def quest_to_dict(quest):
            return {
                "id": quest.id,
                "title": quest.title,
                "description": quest.description,
                "status": quest.status,
                "objectives": [objective_to_dict(o) for o in quest.objectives]
            }
        # Pour creer un arc
        def arc_to_dict(arc):
            return {
                "arc": arc.arc_id,
                "name": arc.name,
                "description": arc.description,
                "status": arc.status,
                "quests": [quest_to_dict(q) for q in arc.quests]
            }
    
        try:
            with open(self.quest_save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []

        # en cherche l'arc dans data qui a le meme id que self.arc
        arc_saved = next((arc for arc in data if arc["arc"] == self.arc.arc_id), None) 

        if arc_saved:
            # Mettre à jour le statut de l'arc
            arc_saved["status"] = self.arc.status

            for quest in self.arc.quests:
                # Chercher la quête correspondante à celle de self.arc
                quest_found = next((q for q in arc_saved["quests"] if q["id"] == quest.id), None)
                if quest_found:
                    # Met à jour le status de la quête
                    quest_found["status"] = quest.status

                    for obj in quest.objectives:
                        # Chercher les objectifs correspondans à celle de self.arc
                        obj_found = next((o for o in quest_found["objectives"] if o["name"] == obj.name), None)
                        # si l'objectif est trouvé en met à jours son statut
                        if obj_found:
                            obj_found["status"] = obj.status
                        # si non trouvé en creer l'objectif    
                        else:
                            quest_found["objectives"].append(objective_to_dict(obj))
                # si la quête n'est pas trouvé (donc c'est une nouvelle) en la creer            
                else:
                    arc_saved["quests"].append(quest_to_dict(quest))
        # Si arc inexistant on l'ajoute en entier            
        else:
            data.append(arc_to_dict(self.arc))

        # Sauvegarder dans le fichier
        with open(self.quest_save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)






    """Pour verifier si un objectif est atteint"""
    def check_objective(self, stat, value) -> None:
        for quest in self.arc.quests:
            for obj in quest.objectives:
                # si c'est un objectif de type stat :
                if obj.type == "stat" :
                    if obj.stat_key == stat and obj.status != "t":
                        if obj.validator <= value:
                            self.complete_objective(quest, obj)
                        

    """Pour changer l'etat d'un objectif"""
    def complete_objective(self, quest, objective) -> None:
        if objective.is_completed():    # Si deja terminer
            return
        objective.complete()            # Fonction déclarer dans la classe qui change l'etat de l'objectif
        print(f"✅ Objectif '{objective.name}' terminé dans la quête '{quest.title}'")
        self.save_progress()
        self.complete_objectives_quete(quest)

    """Pour verfier que tous les objectifs d'une quête soit teminées"""
    def complete_objectives_quete(self, quest) -> None:
        all_done = all(obj.status == "t" for obj in quest.objectives)
        if all_done and quest.status != "t":
            quest.complete()            # Fonction déclarer dans la classe qui change l'etat de la quête
            print(f"🎯 Quête '{quest.title}' complétée !")
            self.save_progress()
            self.start_next_quest(quest.id)

    """Pour lancer la quête suivante"""
    def start_next_quest(self, completed_quest_id: int) -> None:
        with open(self.quest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # On récupère l'arc dans le fichier des quêtes
        arc_actu_in_data = next((arc for arc in data if arc["arc"] == self.arc.arc_id), None)  
        # On récupère la quête suivante
        next_quest_data = next((quest for quest in arc_actu_in_data["quests"] if quest["id"] == completed_quest_id + 1), None)

        # Si aucune autre quête
        if not next_quest_data:
            print("Aucune quête trouvée, passage à l'arc suivante")   
            self.complete_quete_arc()
        # Si une quête est trouvé      
        else:
            next_quest = self._create_quest_from_dict(next_quest_data)
            next_quest.status = "ec"

            # Ajouter la quête à l'arc courant
            self.arc.add_quest(next_quest)

            print(f"🎯 La quête suivante '{next_quest.title}' a commencé !")

            # Sauvegarder la progression
            self.save_progress()    

    """Pour verfier que tous les quetes d'un arc soit teminées"""
    def complete_quete_arc(self) -> None:
        all_done = all(quest.status == "t" for quest in self.arc.quests)
        if all_done and self.arc.status != "t":
            self.arc.complete()
            print(f"🎯 Arc '{self.arc.name}' complétée !")
            self.save_progress()
            self.start_next_arc()           

    """Pour passer à l'arc suivant"""
    def start_next_arc(self):
        with open(self.quest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        next_arc_in_data = next((arc for arc in data if arc["id"] == self.arc.arc_id + 1), None)

        new_arc = self._create_arc_from_dict(next_arc_in_data)
        self.arc = new_arc            
                 
    """Crée et initialise un objectif à partir d'un dictionnaire JSON."""
    def _create_objective_from_dict(self, o_data: dict) -> Objective:
        return Objective(
            name=o_data.get("name", ""),
            description=o_data.get("description", ""),
            status=o_data.get("status", "na"),
            type=o_data.get("type", ""),
            stat_key=o_data.get("stat_key", ""),
            validator=o_data.get("validator", 0)
        )
    """Crée et initialise une quête à partir d'un dictionnaire JSON."""
    def _create_quest_from_dict(self, q_data : dict) -> Quest:
        quest = Quest(
            id=q_data.get("id", 0),
            title=q_data.get("title", "Quête sans titre"),
            description=q_data.get("description", ""),
            status=q_data.get("status", "nc")
        )
        for o_data in q_data.get("objectives", []):
            quest.add_objective(self._create_objective_from_dict(o_data))
        return quest
    """Crée et initialise un arc à partir d'un dictionnaire JSON."""
    def _create_arc_from_dict(self, a_data: dict) -> Arc:
        arc = Arc(
            arc_id=a_data.get("arc", 0),
            name=a_data.get("name", "Arc sans nom"),
            description=a_data.get("description", ""),
            status=a_data.get("status", "nc")
        )
        for q_data in a_data.get("quests", []):
            arc.add_quest(self._create_quest_from_dict(q_data))
        return arc

    

              