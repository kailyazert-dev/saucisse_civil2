from __future__ import annotations
from typing import List

class Objective:
    def __init__(self, name: str, description: str, status = str, type = str, stat_key = str, validator = int):
        self.name = name
        self.description = description
        self.status = status
        self.type = type
        self.stat_key = stat_key
        self.validator = validator

    # Marque l'objectif en cour
    def start(self) -> None:
        self.status = "ec"

    # Marque l'objectif terminé
    def complete(self) -> None:
        self.status = "t"

    # Marque l'object comme terminé
    def is_completed(self) -> bool:
        return self.status == "t"

    def __repr__(self) -> str:
        return f"<Objective {self.name} - {self.status}>"


class Quest:
    def __init__(self, id: int, title: str, description: str, status = str):
        self.id = id
        self.title = title
        self.description = description
        self.objectives: List[Objective] = []
        self.status = status

    # Ajoute un objectif à la quête.
    def add_objective(self, objective: Objective) -> None:
        self.objectives.append(objective)

    # Met la quête en cour
    def start(self) -> None:
        if self.objectives:
            self.status = "ec"

    # Marque la quête comme terminer si tous les objectifs sont terminer
    def complete(self) -> None:
        if all(obj.is_completed() for obj in self.objectives):
            self.status = "t"
        # self.status = "t"

    # Retourne le nombre d'objectifs terminés / total. 
    def progress(self) -> str:
        completed = sum(obj.is_completed() for obj in self.objectives)
        return f"{completed}/{len(self.objectives)} Objectifs terminés"

    def __repr__(self) -> str:
        return f"<Quest {self.title} - {self.status} - {self.progress()}>"
    

class Arc:
    def __init__(self, arc_id: int, name: str, description: str, status: str = "nc"):
        self.arc_id = arc_id
        self.name = name
        self.description = description
        self.status = status
        self.quests: List[Quest] = []

    # Ajoute une quête à l'arc
    def add_quest(self, quest: Quest) -> None:
        self.quests.append(quest)

    # Démarre l'arc si au moins une quête est en cours
    def start(self) -> None:
        if self.quests:
            self.status = "ec"

    # Vérifie si toutes les quêtes sont terminées
    def complete(self) -> None:
        if all(quest.status == "t" for quest in self.quests):
            self.status = "t"

    # Retourne le nombre de quêtes terminées sur le total
    def progress(self) -> str:
        completed = sum(quest.status == "t" for quest in self.quests)
        return f"{completed}/{len(self.quests)} Quêtes terminées"

    def __repr__(self) -> str:
        return f"<Arc {self.name} - {self.status} - {self.progress()}>"    