# ui/menus/

Menus plein écran du jeu : statistiques, pause et mort.

## Fichiers

| Fichier | Classe | Touche | Rôle |
|---|---|---|---|
| `stats_view.py` | `StatsView(arcade.View)` | P | Écran stats/quêtes/équipement |
| `menu.py` | `Menu` | ESCAPE | Menu pause (overlay) |
| `death_menu.py` | `DeathMenu` | — | Menu mort (overlay) |

## StatsView

Vue Arcade complète (remplace temporairement la scène).  
3 onglets navigables avec ← → :
- **Stats** : barres de progression pour les 9 stats en 3 colonnes (Physique / Intellect / Sociale)
- **Quêtes** : quête en cours, objectifs avec statut [x]/[ ]
- **Équipement** : carte arme avec image, dégâts min/max, barre et couleur projectile

Retour à la scène : P ou ESCAPE.

## Menu

Overlay modal (non-View), dessiné au-dessus de la scène via `menu.draw()`.  
Options : Reprendre, Sauvegarder, Charger, Retour à la maison, Réinitialiser, Quitter.

Sous-menus : liste des sauvegardes (scroll), saisie de nom, confirmation de suppression.

```python
gv.show_menu = True
gv.menu.draw()
gv.menu.handle_key(key)
gv.menu.on_text(char)   # pour la saisie du nom de sauvegarde
```

## DeathMenu

Overlay affiché quand `player.health <= 0` (après fondu rouge).  
Options : "Recommencer au début" ou "Apparaître à la maison".

```python
death_menu = DeathMenu()
death_menu.active = True
death_menu.draw()
choice = death_menu.handle_key(key)  # → str | None
```
