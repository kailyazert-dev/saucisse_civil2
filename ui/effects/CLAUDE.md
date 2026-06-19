# ui/effects/

Effets visuels plein écran.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `screen_fade.py` | `ScreenFade` | Fondu en entrée/sortie sur l'écran entier |

## ScreenFade

Utilitaire de fondu réutilisable. Couvre toute la fenêtre avec un rectangle semi-transparent animé.

```python
fade = ScreenFade(color=(0, 0, 0))  # noir par défaut
fade.darken()                        # lance l'assombrissement
fade.lighten()                       # lance l'éclaircissement
fade.update()                        # appelé chaque frame dans on_update()
fade.draw()                          # appelé dans on_draw() après camera_gui.use()
fade.is_active                       # True si un fondu est en cours
fade.alpha                           # valeur alpha actuelle (0-255)
```

### Utilisation typique

```python
# Déclencher un fondu noir au changement de map
self._fade = ScreenFade()
self._fade.darken()

# Dans on_update
self._fade.update()
if not self._fade.is_active and self._should_switch:
    self.manager.switch_map("home")

# Dans on_draw (après camera_gui.use())
self._fade.draw()
```

Note : `HomeScene` et `PhlScene` implémentent leur propre fondu inline pour le moment (`_fade_alpha`, `_fade_dir`). `ScreenFade` est prévu pour les prochaines scènes.
