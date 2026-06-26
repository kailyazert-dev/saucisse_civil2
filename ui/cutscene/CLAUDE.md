# ui/cutscene/

Orchestration des cutscènes narratives liées aux quêtes.

## Fichiers

| Fichier | Contenu | Rôle |
|---|---|---|
| `cutscene_manager.py` | `CutsceneManager` | Détecte, déclenche et avance les cutscènes |
| `cutscene_data.py` | `KYLE_LINES`, `KYLE_END_LINES`, `SYLVAIN_LINES`, `JEAN_CHRISTOPHE_LINES`, `GUY_LINES` | Textes des dialogues scriptés |

## CutsceneManager

Point d'entrée unique pour toutes les cutscènes du jeu.

```python
# Depuis InputHandler (touche ENTER)
if gv.cutscene_manager.any_active:
    gv.cutscene_manager.handle_enter()

# Depuis InputHandler (approche d'un PNJ)
if gv.cutscene_manager.try_trigger(pnj):
    return True   # ENTER consommé par la cutscène

# Depuis on_draw() (après camera_gui.use())
gv.cutscene_manager.draw()
```

### Conditions de déclenchement

Chaque PNJ a sa cutscène déclenchée si :
1. L'arc et la quête correspondants sont actifs (`arc_id`, `quest_id`)
2. L'objectif `"talk"` ciblant ce PNJ n'est pas encore complété

| PNJ | `arc_id` | `quest_id` |
|---|---|---|
| Kyle (intro) | 3 | 1 |
| Sylvain | 2 | 1 |
| Jean christophe | 2 | 1 |
| Guy | 2 | 4 |
| Kyle (fin) | — | — (voir `_kyle_end_needed`) |

La cutscène de fin de Kyle (`_kyle_end`) est déclenchée séparément : `kyle_ai.walk_done` doit être `True`, `zombie_mode.is_active()` doit être `False`, et `kyle_ai.end_talked` doit être `False`.

### Callbacks `on_done`

Quand une cutscène se termine, le callback associé est appelé automatiquement :

| Cutscène | Callback | Actions |
|---|---|---|
| Kyle (intro) | `_on_kyle_done` | `complete_talk_objective("Kyle")` + attribue `Pistolet` et `Couteau` au joueur + `character_manager.save_player()` + `kyle_ai.start_walk()` |
| Kyle (fin) | `_on_kyle_end_done` | `kyle_ai.end_talked = True` + `complete_talk_objective("Kyle")` |
| Sylvain | `_on_sylvain_done` | `complete_talk_objective("Sylvain")` |
| Jean-Christophe | `_on_jc_done` | `complete_talk_objective("Jean christophe")` |
| Guy | `_on_guy_done` | `complete_talk_objective("Guy")` |

## cutscene_data.py

Contient uniquement les listes de strings des dialogues. Séparé du code pour faciliter la traduction ou l'édition de contenu sans toucher à la logique.

```python
from ui.cutscene.cutscene_data import (
    KYLE_LINES, KYLE_END_LINES, SYLVAIN_LINES, JEAN_CHRISTOPHE_LINES, GUY_LINES
)
```
