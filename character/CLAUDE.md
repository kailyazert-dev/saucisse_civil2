# character/

Ce dossier contient toutes les classes de personnages du jeu ainsi que leur équipement.

## Structure

```
character/
├── character_base.py       — classe mère commune + Humain
├── player/
│   ├── player.py           — classe Player (joueur)
│   └── player_manager.py   — CharacterManager + AnimationManager
├── pnj/
│   ├── pnj.py              — classe PNJ + PNJState
│   └── pnj_loader.py       — humain_from_data()
├── enemies/
│   ├── zombie.py            — classe Zombie (base)
│   ├── zombie_augmente.py   — classe ZombieAugmente (sous-classe)
│   └── zombie_manager.py    — ZombieManager
└── equipment/
    ├── weapon.py            — Weapon, FirearmWeapon, MeleeWeapon
    └── bullet.py            — Bullet (projectile)
```

## Hiérarchie d'héritage

```
arcade.Sprite
└── CharacterBase          (character_base.py)
    ├── Player             (player/player.py)
    ├── PNJ                (pnj/pnj.py)
    └── Zombie             (enemies/zombie.py)
        └── ZombieAugmente (enemies/zombie_augmente.py)
```

## character_base.py

Définit `Humain` et `CharacterBase`. Ré-exporte `Weapon` et `Bullet` depuis `equipment/` pour la compatibilité des imports.

- **`Humain`** — 9 stats (force, vitesse, endurance, mathematique, logique, rpg, music, langue, sociabilite) + position (x, y)
- **`CharacterBase`** — classe mère avec les propriétés communes à tous les personnages :
  - `nom`, `humain`, `direction`, `health`, `damage_cooldown`, `weapon`
  - `textures` (dict idle), `textures_walk` (dict listes frames)
  - `face(dx, dy)` — oriente le sprite
  - `load_walk_textures(prefix)` — charge les textures depuis `assets/images/<prefix>_<dir>.png` (le préfixe peut inclure un sous-dossier, ex. `enemies/zombies/z_1`)
  - `_animate(direction, dt)` — alterne les frames de marche

## equipment/

Objets équipables par n'importe quel personnage (Player, PNJ, Zombie).
Pour ajouter un nouveau type d'équipement, créer un fichier dans ce dossier.

### weapon.py

Trois classes dans ce fichier :

- **`Weapon`** — classe mère : `name`, `damage_min`, `damage_max`, `fire_interval`, `sprite_size`, `image_path`, `weapon_type = "base"`
  - `get_damage()` — retourne un dégât aléatoire dans `[damage_min, damage_max]`
  - `get_texture()` — chargement lazy du sprite de l'arme (retourne `None` si le PNG est absent)
  - `use(player, zombie_manager, world_x, world_y, ...)` — déclenche l'arme (à surcharger) ; retourne `(kills, arc_dict | None)`
  - `from_name(name)` (classmethod factory) — instancie l'arme correspondante depuis `character/equipment/weapons.json` (registre chargé en lazy dans `_registry`)

- **`FirearmWeapon(Weapon)`** — arme à feu (`weapon_type = "feu"`) : ajoute `bullet_color` ; `use()` accepte `spawn_x/spawn_y` optionnels et tire des `Bullet` via `zombie_manager.fire()`

- **`MeleeWeapon(Weapon)`** — arme blanche (`weapon_type = "blanc"`) : ajoute `attack_radius`, `half_span`, `arc_color`, `_ARC_DURATION = 0.20` ; `use()` retourne un dict arc pour l'animation de frappe

### bullet.py — Bullet

Projectile `arcade.SpriteSolidColor` avec `vel_x/y`, `damage`, `life`, `step()`.
Paramètres optionnels : `speed` (défaut `SPEED=10`) et `size` (taille du sprite).

## player/

### player.py — Player

Joueur contrôlé par le clavier (AZERTY : Z/Q/S/D).

Propriétés spécifiques : `reading`, `quest_manager`, `character_manager`, `textures_read`, timers d'animation, `gold = 0` (or ramassé en mode zombie), `max_health_bonus`, `weapon_feu: Weapon | None`, `weapon_blanc: Weapon | None`.

`Player.update()` délègue à `character_manager.update_player_stats()` et `character_manager.animation.update()`.

### player_manager.py — CharacterManager

Propriétaire du sprite joueur. Responsabilités :
- Chargement et sauvegarde JSON (`save/character_save.json`)
- Slots de sauvegarde nommés (`save/saves.json`) : `save_slot()`, `load_slot()` (retourne le nom de la map sous forme de `str`), `delete_slot()`
- Incrémentation de stats via `start_up(progresseur)` / `stop_up()`
- Auto-save toutes les 30 s pendant la progression active
- `reset()` — réinitialise les stats et repositionne le joueur
- `_pending_spawn` / `consume_pending_spawn()` — position de respawn différée après chargement de slot

**`_CHARACTER_DEFAULTS`** — valeurs par défaut utilisées à la création et à la validation de la sauvegarde :

| Clé | Valeur par défaut |
|---|---|
| `nom` | `"Joueur"` |
| `force` … `sociabilite` | stats initiales (0.1 à 0.14) |
| `x`, `y` | `0` |
| `weapon` | `None` (champ legacy, toujours `None` à la création) |
| `weapon_feu` | `None` |
| `weapon_blanc` | `None` |

`load_player()` et `load_slot()` gèrent la migration depuis l'ancien champ `weapon` vers `weapon_feu` (`wf = data.get("weapon_feu") or data.get("weapon")`).

`save_player()` sérialise `weapon_feu` et `weapon_blanc` (chacun comme `{"name": ...}` ou `None`) — le champ legacy `weapon` n'est plus écrit.

**AnimationManager** — gère l'animation du joueur (marche, lecture) et les limites de la map.

## pnj/

### pnj.py — PNJ + PNJState

PNJ avec machine à états (FSM) :

| État | Comportement |
|------|-------------|
| `ASSIS` | Statique |
| `ERRANCE` | Déplacement aléatoire animé |
| `CHASSE` | Poursuite + tir sur les zombies proches |
| `DIALOGUE` | Immobile, face au joueur |
| `STAND` | Debout immobile |

`update_ai(dt, walls, zombies)` retourne le nombre de zombies tués.

### pnj_loader.py — humain_from_data

`humain_from_data(nom)` construit un `Humain` depuis `assets/param_humain.py`.
Utilisé par `world/loader/map_loader.py`.

## enemies/

### zombie.py — Zombie

Ennemi avec deux comportements :
- **Errance** : déplacement en angle aléatoire (coordonnées polaires)
- **Chasse** : poursuite du joueur avec accélération, wall-slide

Transition errance → chasse à 220 px, retour à 450 px (hysteresis).
`_WALK_SWITCH = 0.2` (plus lent que les autres personnages).

**Attributs de classe surchargeables dans les sous-classes** :

| Attribut | Valeur défaut | Rôle |
|---|---|---|
| `_SPRITE_PREFIX` | `"enemies/zombies/z_1"` | Chemin relatif à `assets/images/` pour les sprites |
| `VITESSE_ERRANCE` | `90.0` | Vitesse en errance |
| `VITESSE_CHASSE` | `125.0` | Vitesse max en chasse |
| `ACCEL_CHASSE` | `30.0` | Accélération en chasse |
| `RAYON_DETECTION` | `220` | Distance déclenchant la chasse |
| `RAYON_FUITE` | `450` | Distance déclenchant le retour à l'errance |
| `CHANGEMENT_DIR` | `(2.5, 4.5)` | Intervalle aléatoire de changement de direction |

Les sprites sont dans `assets/images/enemies/zombies/`. Nommage attendu : `<prefix>_d.png`, `<prefix>_l.png`, `<prefix>_r.png`, `<prefix>_u.png` (idle) + `_d1/d2`, `_l1/l2`, `_r1/r2`, `_u1/u2` (marche).

**Système de drops** :
- `_DROPS: list | None = None` — attribut de classe, `None` = lazy-load par défaut, `[]` = aucun drop
- `_get_drops_config()` (classmethod) — initialise `_DROPS` au premier appel avec `[(GoldDrop, 0.65), (HealthDrop, 0.20)]` (lazy import)
- `loot(x, y)` (classmethod) — génère la liste de drops selon les probabilités de la classe ; utilisé par `ZombieMode` après chaque mort

### zombie_augmente.py — ZombieAugmente

Sous-classe de `Zombie` avec des stats renforcées, un sprite distinct et une attaque à distance (jet de pierre).

| Attribut | Valeur |
|---|---|
| `_SPRITE_PREFIX` | `"enemies/zombies/z_aug"` |
| `MAX_HEALTH` | `30` |
| `DAMAGE` | `7` |
| `VITESSE_ERRANCE` | `100.0` |
| `VITESSE_CHASSE` | `160.0` |
| `ACCEL_CHASSE` | `80.0` |
| `RAYON_DETECTION` | `480` |
| `RAYON_FUITE` | `550` |

**Système de projectile (jet de pierre)** — attributs surchargeables :

| Attribut | Valeur défaut | Rôle |
|---|---|---|
| `PROJECTILE_DEGATS` | `2` | Dégâts par projectile |
| `PROJECTILE_VITESSE` | `6.0` | Vitesse du projectile |
| `PROJECTILE_INTERVALLE` | `2.5` | Intervalle entre tirs (s) |
| `PROJECTILE_RAYON_TIR` | `400` | Distance maximale de tir |
| `PROJECTILE_COULEUR` | `(150, 100, 60)` | Couleur du projectile |

`pending_projectiles: list[tuple[float, float, float, float]]` — liste des projectiles à spawner (remplie dans `move()`, consommée par `ZombieMode`). Tir uniquement en mode chasse si le joueur est dans `PROJECTILE_RAYON_TIR`.

Sprites attendus dans `assets/images/enemies/zombies/z_aug_*.png`.

### zombie_manager.py — ZombieManager

Gère le spawn, le mouvement, les balles joueur→zombie et les dégâts zombie→joueur.
Normalement actif uniquement quand `quest_manager.get_kill_objective()` retourne un objectif — sauf si `is_active` est monkeypatché à `lambda: True` (cas MercScene via `ZombieMode(always_active=True)`).

Attributs et paramètres notables :
- `zombie_class` — sous-classe de `Zombie` à instancier (défaut : `Zombie`)
- `spawn_enabled` — flag booléen pour activer/désactiver le spawn sans toucher à `is_active`
- `morts_ce_frame: list[tuple[float, float]]` — positions des zombies morts dans la frame courante, lu par `ZombieMode` pour spawner les drops

Méthodes notables :
- `fire(fx, fy, tx, ty, weapon)` — crée un `Bullet` orienté vers la cible
- `melee_attack(player, radius, get_damage, attack_angle, half_span)` — inflige des dégâts aux zombies dans le secteur (rayon + angle) ; retourne le nombre de kills
- `check_player_damage(player, delta_time)` — gère dégâts + knockback zombie→joueur ; retourne `True` si dégâts appliqués
- `draw()` — dessine zombies, balles et barres de vie
