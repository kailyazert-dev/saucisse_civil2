# input/

Gestion des entrées clavier et souris. Découplé de la scène pour faciliter les tests et la réutilisation.

## Fichiers

| Fichier | Contenu | Rôle |
|---|---|---|
| `input_handler.py` | `InputHandler` | Routage clavier/souris → actions jeu |
| `key_map.py` | `MOVE_KEYS` | Mapping AZERTY → direction |

## InputHandler

Reçoit les événements Arcade et les route vers le bon sous-système.

```python
# Créé dans BaseScene.__init__
self.input_handler = InputHandler(self)

# Appelé depuis on_key_press / on_key_release / on_mouse_press des scènes
input_handler.handle_key_press(key, modifiers)
input_handler.reset_movement_on_release(key, modifiers)
input_handler.on_mouse_press(x, y, button, modifiers)
```

### Arbre de décision de handle_key_press

```
auto_walk_active → ignorer tout
cutscene active  → ENTER uniquement (advance cutscène)
ESCAPE           → fermer dialogue / basculer menu
menu ouvert      → déléguer à menu.handle_key()
sinon :
  _to_reinit()       → reset sélections si touche mouvement
  _handle_movement_keys() → déplacer le joueur
  _to_show_stat()    → P → StatsView
  _to_dialogue()     → ENTER près d'un PNJ → ouvrir dialogue
  _up_stat()         → ENTER sur objet → utiliser / compléter objectif
```

## key_map.py

```python
MOVE_KEYS = {
    arcade.key.D: ("x",  1, "right"),
    arcade.key.Q: ("x", -1, "left"),
    arcade.key.Z: ("y",  1, "up"),
    arcade.key.S: ("y", -1, "down"),
}
```

Layout AZERTY. Modifier ici pour changer les touches de déplacement.  
`InputHandler` utilise sa propre copie locale `_MOVE_KEYS` (compatible, peut être migré vers `key_map.MOVE_KEYS`).
