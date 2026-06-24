# ui/hud/

Éléments d'interface permanents affichés en HUD pendant le jeu.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `interact_ui.py` | `InteractUI` | Popups d'interaction (objets, PNJs) + sidebar quêtes |
| `quest_notif.py` | `QuestNotif` | Notifications de quête (fade in/hold/fade out) |
| `zombie_hud.py` | `ZombieHUD` | Rendu visuel du mode zombie : arme, arc mêlée, barre vie, kills, cartes armes, crosshair |

## ZombieHUD

Classe instanciée par `ZombieMode` (`self._hud = ZombieHUD(self)`). Contient tout le code de rendu extrait de `ZombieMode`.

```python
zombie_hud.draw_world()  # world-space : sprite arme à feu + animation arc mêlée
zombie_hud.draw_hud()    # screen-space : kills, barre vie, cartes armes, crosshair
```

Méthodes internes :
- `_draw_player_firearm()` — sprite arme à feu orienté vers le curseur, avec flip horizontal et rotation correcte
- `_draw_melee_arcs()` — animation de frappe arc mêlée (sprite ou fallback géométrique)
- `_draw_stats()` — compteur kills, barre vie, deux cartes armes
- `_draw_weapon_card(w, cx, cy, label)` — carte arme avec nom, dégâts et info type (couleur balle / rayon)
- `_draw_crosshair()` — viseur rouge (crosshair), appelé séparément pour éviter le double-rendu

## InteractUI

Gère la détection de proximité et l'affichage des popups contextuelles.

```python
# Appelé depuis on_draw() en world-space (camera_sprites.use())
interact_ui.interact_obj_prg()       # popup objet le plus proche
interact_ui.interact_pnj_strateg()   # popup PNJ stratégique
interact_ui.interact_pnj()           # popup PNJ normal

# Appelé depuis on_draw() en screen-space (camera_gui.use())
interact_ui.draw_side_bar()          # sidebar quête (toggle avec bouton Quêtes)
```

### Priorité des objets (interact_obj_prg)
1. `ObjetInteractif` — popup info uniquement
2. `MapActionObject` — si objectif actif (priorité sur UpStat)
3. `UpStat` / `UpStatCollection` — progression de stat

Met à jour `game_view.current_objet`, `current_collection`, `current_map_action`.

### create_obstacles()
Construit la `SpriteList` des obstacles physiques : PNJs + stratégiques + objets + Mur + Meuble_H.
Appelé depuis `setup()` des scènes pour initialiser le `PhysicsEngineSimple`.

## QuestNotif

Machine à états pour les notifications de quête animées.

États : `idle → fade_in → hold → fade_out → idle`  
Timings : 0.35s / 2.2s / 0.55s

```python
quest_notif.update(delta_time, quest_manager.pending_notifications)
quest_notif.draw()
```

Types de notification (`type` dans le dict) :
- `"new_arc"` / `"new_quest"` / `"quest"` → couleur or
- `"objective"` → couleur verte
