# ui/cutscene/

Orchestration des cutscènes narratives liées aux quêtes.

## Fichiers

| Fichier | Contenu | Rôle |
|---|---|---|
| `cutscene_manager.py` | `CutsceneManager` | Détecte, déclenche et avance les cutscènes |
| `cutscene_data.py` | `KYLE_LINES`, `SYLVAIN_LINES`, etc. | Textes des dialogues scriptés |

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

### Callbacks `on_done`

Quand une cutscène se termine, le callback associé est appelé automatiquement :
- Kyle → donne une arme au joueur + lance la marche de Kyle via `KyleAI.start_walk()`
- Kyle (fin) → marque `kyle_ai.end_talked = True`
- Sylvain / Jean-Christophe / Guy → `quest_manager.complete_talk_objective(nom)`

## cutscene_data.py

Contient uniquement les listes de strings des dialogues. Séparé du code pour faciliter la traduction ou l'édition de contenu sans toucher à la logique.

```python
from ui.cutscene.cutscene_data import KYLE_LINES, GUY_LINES
```
