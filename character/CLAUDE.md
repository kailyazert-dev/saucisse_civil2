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
    ├── weapon.py            — Weapon (arme équipable)
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

- **`weapon.py` — `Weapon`** : arme avec `damage_min`, `damage_max`, `bullet_color`, `get_damage()`
- **`bullet.py` — `Bullet`** : projectile `arcade.SpriteSolidColor` avec `vel_x/y`, `damage`, `life`, `step()`

## player/

### player.py — Player

Joueur contrôlé par le clavier (AZERTY : Z/Q/S/D).

Propriétés spécifiques : `reading`, `quest_manager`, `character_manager`, `textures_read`, timers d'animation, `gold = 0` (or ramassé en mode zombie).

`Player.update()` délègue à `character_manager.update_player_stats()` et `character_manager.animation.update()`.

### player_manager.py — CharacterManager

Propriétaire du sprite joueur. Responsabilités :
- Chargement et sauvegarde JSON (`save/character_save.json`)
- Slots de sauvegarde nommés (`save/saves.json`)
- Incrémentation de stats via `start_up(progresseur)` / `stop_up()`
- Auto-save toutes les 30 s pendant la progression active

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

Sous-classe de `Zombie` avec des stats renforcées et un sprite distinct.

| Attribut | Valeur |
|---|---|
| `_SPRITE_PREFIX` | `"enemies/zombies/z_aug"` |
| `MAX_HEALTH` | `6` |
| `DAMAGE` | `4` |
| `VITESSE_CHASSE` | `160.0` |
| `RAYON_DETECTION` | `280` |

Sprites attendus dans `assets/images/enemies/zombies/z_aug_*.png`.

### zombie_manager.py — ZombieManager

Gère le spawn, le mouvement, les balles joueur→zombie et les dégâts zombie→joueur.
Normalement actif uniquement quand `quest_manager.get_kill_objective()` retourne un objectif — sauf si `is_active` est monkeypatché à `lambda: True` (cas MercScene via `ZombieMode(always_active=True)`).

Attributs et paramètres notables :
- `zombie_class` — sous-classe de `Zombie` à instancier (défaut : `Zombie`)
- `spawn_enabled` — flag booléen pour activer/désactiver le spawn sans toucher à `is_active`
- `morts_ce_frame: list[tuple[float, float]]` — positions des zombies morts dans la frame courante, lu par `ZombieMode` pour spawner les drops
