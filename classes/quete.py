from enum import Enum

class ObjectiveStatus(Enum):
    INCOMPLETE = 0
    COMPLETE = 1

class Objective:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = ObjectiveStatus.INCOMPLETE

    def complete(self):
        self.status = ObjectiveStatus.COMPLETE

    def is_complete(self) -> bool:
        return self.status == ObjectiveStatus.COMPLETE

    def __str__(self):
        return f"[{'X' if self.is_complete() else ' '}] {self.name}: {self.description}"


class QuestStatus(Enum):
    IN_PROGRESS = 0
    COMPLETE = 1

class Quest:
    def __init__(self, title: str, description: str):
        self.title = title
        self.description = description
        self.objectives: list[Objective] = []
        self.status = QuestStatus.IN_PROGRESS

    def add_objective(self, objective: Objective):
        self.objectives.append(objective)

    def update_status(self):
        if all(obj.is_complete() for obj in self.objectives):
            self.status = QuestStatus.COMPLETE

    def is_complete(self) -> bool:
        return self.status == QuestStatus.COMPLETE

    def __str__(self):
        objs = "\n".join(f"   - {obj}" for obj in self.objectives)
        return f"Quête: {self.title}\nDescription: {self.description}\nObjectifs:\n{objs}\nStatut: {self.status.name}"
