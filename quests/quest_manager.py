from __future__ import annotations
import json
import os
import shutil
from quests.quest_classes import Arc, Quest, Objective
import utils.paths as paths


class QuestManager:
    def __init__(
        self,
        quest_file: str = "quests.json",
        quests_save_file: str = "quests_save.json",
        quests_default_file: str = "quests_default_save.json",
    ):
        self.pending_notifications: list[dict] = []
        self._needs_stat_check: bool = False
        self._on_progress_save = None  # callback optionnel → character_manager.save_player
        self.quests_file_dir = os.path.join(paths.get_project_root(), "quests", "quests_file")
        self.quests_save_dir = os.path.join(paths.get_project_root(), "quests", "quests_save_file")

        self.quest_file = os.path.join(self.quests_file_dir, quest_file)
        self.quest_default_save_file = os.path.join(self.quests_save_dir, quests_default_file)

        # Fichier de sauvegarde dans AppData (avec migration depuis l'ancien emplacement)
        self.quest_save_file = self._resolve_save_file(quests_save_file)

        self.arc: Arc | None = None
        self.quest_trs: list[Quest] = []

        saved_data = self._get_save_progress()
        if saved_data:
            self._load_progress(saved_data)
        if self._is_new_game():
            self._queue_arc_start_notifs(header="Nouvelle Histoire !")

    # ------------------------------------------------------------------ save

    def _resolve_save_file(self, filename: str) -> str:
        save_path = os.path.join(paths.get_save_dir(), filename)
        if os.path.exists(save_path):
            return save_path

        old_path = os.path.join(self.quests_save_dir, filename)
        if os.path.exists(old_path):
            shutil.copy(old_path, save_path)
            print(f"[OK] Sauvegarde quêtes migrée vers {save_path}")
            return save_path

        if os.path.exists(self.quest_default_save_file):
            shutil.copy(self.quest_default_save_file, save_path)
            print(f"[OK] Sauvegarde quêtes initialisée depuis les défauts.")
        return save_path

    def _get_save_progress(self) -> list[dict] | None:
        try:
            if not os.path.exists(self.quest_save_file) or os.path.getsize(self.quest_save_file) == 0:
                if os.path.exists(self.quest_default_save_file):
                    with open(self.quest_default_save_file, "r", encoding="utf-8") as f:
                        default = json.load(f)
                    with open(self.quest_save_file, "w", encoding="utf-8") as f:
                        json.dump(default, f, indent=4, ensure_ascii=False)
                    return default
                return None

            with open(self.quest_save_file, "r", encoding="utf-8") as f:
                return json.load(f)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Sauvegarde quêtes illisible ({e}), nouvelle partie.")
            return None

    def _load_progress(self, saved_data: list[dict]) -> None:
        self.arc = None
        arc_data = next((a for a in saved_data if a.get("status") == "ec"), None)
        if arc_data:
            self.arc = self._create_arc_from_dict(arc_data)
            return
        # Tous les arcs sauvegardés sont terminés — démarrer le suivant
        completed_ids = sorted(
            [a.get("arc", 0) for a in saved_data if a.get("status") == "t"]
        )
        if completed_ids:
            self._launch_arc(completed_ids[-1] + 1)
        else:
            print("[WARN] Aucun arc trouvé dans la sauvegarde.")

    def _is_new_game(self) -> bool:
        if self.arc is None or self.arc.arc_id != 1:
            return False
        quest = next((q for q in self.arc.quests if q.id == 1), None)
        if quest is None:
            return False
        return not any(o.status == "t" for o in quest.objectives)

    def _queue_arc_start_notifs(self, header: str = "Nouvel arc !") -> None:
        if self.arc is None:
            return
        self.pending_notifications.append({"type": "new_arc", "text": header, "title": self.arc.name})
        quest = next((q for q in self.arc.quests if q.status == "ec"), None)
        if quest:
            self.pending_notifications.append({"type": "new_quest", "text": "Nouvelle quête !", "title": quest.title, "objectives": [o.name for o in quest.objectives]})

    def load_from_data(self, data: list) -> None:
        """Écrase le fichier de sauvegarde quêtes et recharge depuis ces données."""
        with open(self.quest_save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self.arc = None
        saved = self._get_save_progress()
        if saved:
            self._load_progress(saved)

    def reset(self) -> None:
        if os.path.exists(self.quest_default_save_file):
            shutil.copy(self.quest_default_save_file, self.quest_save_file)
        self.arc = None
        saved_data = self._get_save_progress()
        if saved_data:
            self._load_progress(saved_data)
        if self._is_new_game():
            self._queue_arc_start_notifs(header="Nouvelle Histoire !")
        print("[RESET] Quêtes réinitialisées.")

    def save_progress(self) -> None:
        if self.arc is None:
            return

        def obj_to_dict(o: Objective) -> dict:
            return {
                "name": o.name, "description": o.description,
                "status": o.status, "type": o.type,
                "stat_key": o.stat_key, "validator": o.validator,
                "counter": o.counter,
            }

        def quest_to_dict(q: Quest) -> dict:
            return {
                "id": q.id, "title": q.title, "description": q.description,
                "status": q.status,
                "objectives": [obj_to_dict(o) for o in q.objectives],
            }

        def arc_to_dict(a: Arc) -> dict:
            return {
                "arc": a.arc_id, "name": a.name, "description": a.description,
                "status": a.status,
                "quests": [quest_to_dict(q) for q in a.quests],
            }

        try:
            with open(self.quest_save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        arc_saved = next((a for a in data if a["arc"] == self.arc.arc_id), None)
        if arc_saved:
            arc_saved["status"] = self.arc.status
            for quest in self.arc.quests:
                quest_found = next((q for q in arc_saved["quests"] if q["id"] == quest.id), None)
                if quest_found:
                    quest_found["status"] = quest.status
                    for obj in quest.objectives:
                        obj_found = next((o for o in quest_found["objectives"] if o["name"] == obj.name), None)
                        if obj_found:
                            obj_found["status"] = obj.status
                        else:
                            quest_found["objectives"].append(obj_to_dict(obj))
                else:
                    arc_saved["quests"].append(quest_to_dict(quest))
        else:
            data.append(arc_to_dict(self.arc))

        with open(self.quest_save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        if self._on_progress_save is not None:
            self._on_progress_save()

    # ------------------------------------------------------------------ progression

    def complete_talk_objective(self, pnj_name: str) -> None:
        """Complète un objectif de type 'talk' quand le joueur parle à un PNJ."""
        if self.arc is None:
            return
        for quest in self.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type == "talk" and obj.stat_key == pnj_name and obj.status != "t":
                    self._complete_objective(quest, obj)
                    return

    def complete_map_action_objective(self, objective_name: str) -> None:
        """Complète un objectif de type map_action ou test identifié par son nom."""
        if self.arc is None:
            return
        for quest in self.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type in ("map_action", "test") and obj.name == objective_name and obj.status != "t":
                    self._complete_objective(quest, obj)
                    return

    def get_kill_objective(self):
        if self.arc is None:
            return None
        for quest in self.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type == "compteur" and obj.stat_key == "kill" and obj.status != "t":
                    return obj
        return None

    def register_kill(self) -> None:
        if self.arc is None:
            return
        for quest in self.arc.quests:
            if quest.status != "ec":
                continue
            for obj in quest.objectives:
                if obj.type == "compteur" and obj.stat_key == "kill" and obj.status != "t":
                    obj.counter += 1
                    if obj.counter >= int(obj.validator):
                        self._complete_objective(quest, obj)
                    else:
                        self.save_progress()
                    return

    def check_objective(self, stat: str, value: float) -> None:
        if self.arc is None:
            return
        for quest in self.arc.quests:
            for obj in quest.objectives:
                if obj.type == "stat" and obj.stat_key == stat and obj.status != "t":
                    if obj.validator <= value:
                        self._complete_objective(quest, obj)

    def check_current_quest_stat_objectives(self, player) -> None:
        self._needs_stat_check = False
        if self.arc is None:
            return
        quest = next((q for q in self.arc.quests if q.status == "ec"), None)
        if quest is None:
            return
        for obj in quest.objectives:
            if obj.type == "stat" and not obj.is_completed():
                current = getattr(player.humain, obj.stat_key, None)
                if current is not None and float(current) >= obj.validator:
                    self._complete_objective(quest, obj)

    def _complete_objective(self, quest: Quest, objective: Objective) -> None:
        if objective.is_completed():
            return
        objective.complete()
        print(f"[OK] Objectif '{objective.name}' terminé dans '{quest.title}'")
        self.pending_notifications.append({"type": "objective", "text": "Objectif atteint !", "title": objective.name})
        self.save_progress()
        self._check_quest_complete(quest)

    def _check_quest_complete(self, quest: Quest) -> None:
        if all(o.status == "t" for o in quest.objectives) and quest.status != "t":
            quest.complete()
            print(f"[QUETE] Quête '{quest.title}' complétée !")
            self.pending_notifications.append({"type": "quest", "text": "Quête terminée !", "title": quest.title})
            self.save_progress()
            self._start_next_quest(quest.id)

    def _start_next_quest(self, completed_id: int) -> None:
        try:
            with open(self.quest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Impossible de lire quests.json : {e}")
            return

        arc_data = next((a for a in data if a["arc"] == self.arc.arc_id), None)
        if arc_data is None:
            return
        next_data = next((q for q in arc_data["quests"] if q["id"] == completed_id + 1), None)
        if next_data is None:
            print("Toutes les quêtes de l'arc terminées, passage à l'arc suivant.")
            self._complete_arc()
            return
        next_quest = self._create_quest_from_dict(next_data)
        next_quest.status = "ec"
        existing = next((q for q in self.arc.quests if q.id == next_quest.id), None)
        if existing:
            existing.status = "ec"
        else:
            self.arc.add_quest(next_quest)
        print(f"[QUETE] Nouvelle quête : '{next_quest.title}'")
        self.pending_notifications.append({"type": "new_quest", "text": "Nouvelle quête !", "title": next_quest.title, "objectives": [o.name for o in next_quest.objectives]})
        self._needs_stat_check = True
        self.save_progress()

    def _complete_arc(self) -> None:
        if self.arc is None:
            return
        if all(q.status == "t" for q in self.arc.quests) and self.arc.status != "t":
            self.arc.complete()
            print(f"[ARC] Arc '{self.arc.name}' terminé !")
            self.save_progress()
            self._start_next_arc()

    def _start_next_arc(self) -> None:
        self._launch_arc(self.arc.arc_id + 1)

    def _launch_arc(self, arc_id: int) -> None:
        """Charge et démarre l'arc avec l'id donné depuis quests.json."""
        try:
            with open(self.quest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Impossible de lire quests.json : {e}")
            return
        arc_data = next((a for a in data if a["arc"] == arc_id), None)
        if arc_data is None:
            print("[FIN] Fin du jeu — plus d'arcs disponibles.")
            return
        new_arc = Arc(
            arc_id=arc_data.get("arc", 0),
            name=arc_data.get("name", ""),
            description=arc_data.get("description", ""),
            status="ec",
        )
        self.pending_notifications.append({"type": "new_arc", "text": "Nouvel arc !", "title": new_arc.name})
        first_quest_data = next(
            (q for q in arc_data.get("quests", []) if q.get("id") == 1), None
        )
        if first_quest_data:
            first_quest = self._create_quest_from_dict(first_quest_data)
            first_quest.status = "ec"
            new_arc.add_quest(first_quest)
            self.pending_notifications.append({"type": "new_quest", "text": "Nouvelle quête !", "title": first_quest.title, "objectives": [o.name for o in first_quest.objectives]})
            self._needs_stat_check = True
        self.arc = new_arc
        self.save_progress()
        print(f"[QUETE] Nouvel arc : '{self.arc.name}'")

    # ------------------------------------------------------------------ factory

    def _create_objective_from_dict(self, o: dict) -> Objective:
        return Objective(
            name=o.get("name", ""),
            description=o.get("description", ""),
            status=o.get("status", "na"),
            type=o.get("type", ""),
            stat_key=o.get("stat_key", ""),
            validator=o.get("validator", 0),
            counter=o.get("counter", 0),
        )

    def _create_quest_from_dict(self, q: dict) -> Quest:
        quest = Quest(
            id=q.get("id", 0),
            title=q.get("title", "Quête sans titre"),
            description=q.get("description", ""),
            status=q.get("status", "nc"),
        )
        for o in q.get("objectives", []):
            quest.add_objective(self._create_objective_from_dict(o))
        return quest

    def _create_arc_from_dict(self, a: dict) -> Arc:
        arc = Arc(
            arc_id=a.get("arc", 0),
            name=a.get("name", "Arc sans nom"),
            description=a.get("description", ""),
            status=a.get("status", "nc"),
        )
        for q in a.get("quests", []):
            arc.add_quest(self._create_quest_from_dict(q))
        return arc
