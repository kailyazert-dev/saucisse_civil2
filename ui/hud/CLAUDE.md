# ui/hud/

Éléments d'interface permanents affichés en HUD pendant le jeu.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `interact_ui.py` | `InteractUI` | Popups d'interaction (objets, PNJs) + sidebar quêtes |
| `quest_notif.py` | `QuestNotif` | Notifications de quête (fade in/hold/fade out) |
| `zombie_hud.py` | `ZombieHUD` | Rendu visuel du mode zombie : arme, arc mêlée, barre vie, kills, armes, crosshair |

## ZombieHUD

Classe instanciée par `ZombieMode` (`self._hud = ZombieHUD(self)`). Contient tout le code de rendu extrait de `ZombieMode`.

```python
zombie_hud.draw_world()  # world-space : sprite arme à feu + animation arc mêlée
zombie_hud.draw_hud()    # screen-space : kills, barre vie, or, armes compactes, crosshair
```

**Layout en colonne verticale** (panneau droit) : kills (centre haut) → barre de vie → or avec icône pièce → arme feu → arme blanche.

Constantes de layout définies en haut du module :
- `_PANEL_RIGHT`, `_PANEL_W`, `_PANEL_LEFT` — bords du panneau droit
- `_BAR_X`, `_BAR_Y` — position de la barre de vie ; `_BAR_W, _BAR_H = 200, 16` — dimensions
- `_ICON_SIZE = 40` — taille d'icône arme par défaut (l'arme blanche est appelée avec `icon_size=26`)

Chargement dans `__init__` : `self._coin_tex` (texture `assets/images/conssomables/coins.png`, `None` si absent).

Méthodes internes :
- `_draw_player_firearm()` — sprite arme à feu orienté vers le curseur, avec flip horizontal et rotation correcte
- `_draw_melee_arcs()` — animation de frappe arc mêlée (sprite ou fallback géométrique)
- `_draw_stats()` — kills + barre vie + or + armes compactes
- `_draw_weapon_compact(w, cy, label, icon_size=40)` — ligne compacte : icône + nom + dégâts ; appelée avec `icon_size=26` pour l'arme blanche
- `_draw_crosshair()` — viseur rouge : deux lignes croisées + cercle (`draw_circle_outline` rayon 7), appelé séparément pour éviter le double-rendu

Note : `FirearmWeapon` et `MeleeWeapon` sont importés mais ne servent pas d'annotations de type dans le code actuel (importés pour usage futur ou annotation retirée).

## InteractUI

Gère la détection de proximité et l'affichage des popups contextuelles.

```python
# Appelé depuis on_draw() en world-space (camera_sprites.use())
interact_ui.interact_obj_prg()       # popup objet le plus proche
interact_ui.interact_pnj_strateg()   # popup PNJ stratégique
interact_ui.interact_pnj()           # popup PNJ normal

# Appelé depuis on_draw() en screen-space (camera_gui.use())
interact_ui.draw_side_bar()          # sidebar quête (toggle avec bouton Quêtes)
interact_ui.draw_box()               # stub vide (pass), sans effet
```

### Priorité des objets (interact_obj_prg)
1. `ObjetInteractif` — popup info uniquement
2. `MapActionObject` — si objectif actif (priorité sur UpStat)
3. `UpStat` / `UpStatCollection` — progression de stat

Met à jour `game_view.current_objet`, `current_collection`, `current_map_action`.

### UpStatCollection
Navigation dans une collection de stats : ouverture via `gv.open_collection`, déplacement ↑↓ avec `gv.current_index_upstat`. Le menu déroulant est affiché dans la popup principale.

### draw_side_bar()
Lit `quest_manager.arc.quests` et filtre les quêtes au statut `'ec'` (en cours). Affiche les objectifs en colorant selon leur statut : vert si `'t'` (terminé), gris sinon.

### Méthodes de rendu internes
- `get_r_corner_cord()` — calcule les coordonnées du coin supérieur droit de la zone popup
- `_draw_popup(left, top, w, h)` — fond semi-transparent de popup
- `_draw_box_rect(cx, cy, w, h)` — rectangle centré utilitaire
- `draw_interact_box()` — boîte d'interaction principale
- `draw_box()` — méthode publique vide (`pass`), sans effet

### create_obstacles()
Construit la `SpriteList` des obstacles physiques : PNJs + stratégiques + objets + couches `Mur` et `Meuble_H` de la scène.
Appelé depuis `setup()` des scènes pour initialiser le `PhysicsEngineSimple`. Les couches spécifiques à MercScene (`step_1_H`, `step_2`, `step_3_H`, `hero_1/2/3`) sont ajoutées directement dans `MercScene.setup()`, pas ici.

## QuestNotif

Machine à états pour les notifications de quête animées.

États : `idle → fade_in → hold → fade_out → idle`  
Timings : 0.35s / 2.2s / 0.55s

```python
quest_notif.update(delta_time, quest_manager.pending_notifications)
quest_notif.draw()
```

Propriétés :
- `is_idle` — `True` si l'état courant est `idle`
- `current_type` — type de la notification en cours d'affichage

Types de notification (`type` dans le dict) :
- `"new_arc"` / `"new_quest"` / `"quest"` → couleur or
- `"objective"` → couleur verte

Champs du dict de notification :
- `text` — texte principal (obligatoire)
- `type` — type de notification (obligatoire)
- `title` — titre optionnel affiché au-dessus de la boîte
- `objectives` — liste optionnelle d'objectifs ; pour `"new_quest"`, affichés en pile sous la boîte principale

Position d'affichage : centrée horizontalement, à `WINDOW_HEIGHT * 0.68` de hauteur ; les boîtes d'objectifs sont empilées verticalement sous la boîte principale.
