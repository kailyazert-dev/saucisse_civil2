from __future__ import annotations


class Objective:
    def __init__(self, name: str, description: str, status: str = "na",
                 type: str = "", stat_key: str = "",
                 validator: float = 0.0, counter: int = 0) -> None:
        self.name        = name
        self.description = description
        self.status      = status
        self.type        = type
        self.stat_key    = stat_key
        self.validator   = validator
        self.counter     = counter

    def start(self) -> None:
        self.status = "ec"

    def complete(self) -> None:
        self.status = "t"

    def is_completed(self) -> bool:
        return self.status == "t"

    def progress_ratio(self) -> float:
        """Retourne une progression normalisée 0.0 → 1.0 (pour les objectifs compteur)."""
        if self.type == "compteur" and self.validator > 0:
            return min(1.0, self.counter / self.validator)
        return 1.0 if self.is_completed() else 0.0

    def __repr__(self) -> str:
        return f"<Objective {self.name!r} [{self.status}]>"


class Quest:
    def __init__(self, id: int, title: str, description: str, status: str = "nc") -> None:
        self.id          = id
        self.title       = title
        self.description = description
        self.status      = status
        self.objectives: list[Objective] = []

    def add_objective(self, objective: Objective) -> None:
        self.objectives.append(objective)

    def start(self) -> None:
        if self.objectives:
            self.status = "ec"

    def complete(self) -> None:
        if all(obj.is_completed() for obj in self.objectives):
            self.status = "t"

    def current_objective(self) -> Objective | None:
        """Retourne le premier objectif non terminé, ou None si tout est fait."""
        return next((obj for obj in self.objectives if not obj.is_completed()), None)

    def progress(self) -> str:
        completed = sum(obj.is_completed() for obj in self.objectives)
        return f"{completed}/{len(self.objectives)} Objectifs terminés"

    def __repr__(self) -> str:
        return f"<Quest {self.title!r} [{self.status}] {self.progress()}>"


class Arc:
    def __init__(self, arc_id: int, name: str, description: str, status: str = "nc") -> None:
        self.arc_id      = arc_id
        self.name        = name
        self.description = description
        self.status      = status
        self.quests:     list[Quest] = []

    def add_quest(self, quest: Quest) -> None:
        self.quests.append(quest)

    def start(self) -> None:
        if self.quests:
            self.status = "ec"

    def complete(self) -> None:
        if all(quest.status == "t" for quest in self.quests):
            self.status = "t"

    def progress(self) -> str:
        completed = sum(quest.status == "t" for quest in self.quests)
        return f"{completed}/{len(self.quests)} Quêtes terminées"

    def __repr__(self) -> str:
        return f"<Arc {self.name!r} [{self.status}] {self.progress()}>"
