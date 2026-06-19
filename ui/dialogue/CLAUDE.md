# ui/dialogue/

Dialogue entre le joueur et les PNJs : saisie libre via IA et popups cutscène.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `dialogue_system.py` | `DialogueSystem` | Boîte de dialogue IA (Replicate API) |
| `cutscene_popup.py` | `CutscenePopup` | Popup générique ligne par ligne |

## DialogueSystem

Dialogue texte libre joueur → PNJ via l'API Replicate (gpt-4o-mini).

- Rate-limiting : 3 appels max par 30 secondes (token bucket)
- Threading : l'appel API tourne dans un `daemon=True` thread pour ne pas bloquer le jeu
- `on_text(text)` — accumule les caractères tapés dans `game_view.current_input`
- `request_response(message, pnj)` — lance le thread si non rate-limité
- `draw_dialogue_box()` — affiche la zone joueur (bas) et la réponse PNJ (haut)

Personnalités des PNJs chargées depuis `assets/param_humain.IbmI_personnage`.

## CutscenePopup

Popup modale réutilisable pour des dialogues scriptés (non IA).

```python
popup = CutscenePopup("Kyle", KYLE_LINES, speaker_color=(255, 120, 0))
popup.open()       # active la popup, step=0
popup.advance()    # passe à la ligne suivante ; retourne True si terminé
popup.draw()       # dessine si active
```

- Une seule popup active à la fois (gérée par `CutsceneManager`)
- Le bouton [Entrée] affiche "Suivant" ou "Terminer" selon la position dans les lignes
- Les données de dialogue (listes de strings) sont dans `ui/cutscene/cutscene_data.py`
