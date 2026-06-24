# Commandes du projet — Saucisse Civilisation 2

## Lancer le jeu

```bash
# Installation des dépendances (première fois ou après update)
pip install -r requirements.txt

# Lancer le jeu en mode développement
python main.py
```

> Nécessite un fichier `.env` à la racine avec `REPLICATE_API_TOKEN=votre_clé`.
> Voir `.env.example` pour le modèle.

---

## Git

```bash
# Voir l'état du dépôt
git status

# Ajouter les fichiers modifiés et committer
git add .
git commit -m "message"

# Pousser sur la branche refont
git push origin refont

# Créer une nouvelle branche et basculer dessus
git checkout -b nom-de-branche
```

### Slash commands Claude Code

`/commit-push [message]` — ajoute tous les fichiers, commit et pousse sur `origin refont` en une seule commande.

- Avec message : `/commit-push ajout du système de combat`
- Sans message : Claude génère automatiquement un message en français basé sur les modifications détectées.

> Défini dans `.claude/commands/commit-push.md`.

---

## Build — Créer l'exécutable (PyInstaller)

Le fichier de config est `saucisse.spec`. Le build produit un `.exe` standalone dans `dist/`.

```bash
# Installer PyInstaller si absent
pip install pyinstaller

# Build depuis le .spec (recommandé)
pyinstaller saucisse.spec

# Résultat : dist/SaucisseCivilisation.exe
```

Le `.spec` inclut les dossiers de données — **à mettre à jour** pour inclure la nouvelle structure :
- `assets/`
- `world/tilemaps/`      ← tilemaps
- `map/map_configs/`     ← configs JSON (inchangé)
- `quests/quests_file/`
- `world/`, `ui/`, `input/`, `character/`  ← nouveaux packages Python

> Les sauvegardes (`save/`) se créent à côté de l'exe au premier lancement (géré par `utils/paths.py`).

```bash
# Nettoyer les artefacts de build
rmdir /s /q build dist
del /q *.spec.bak
```

---

## Dépendances

```bash
# Installer toutes les dépendances
pip install -r requirements.txt

# Mettre à jour une dépendance et régénérer le fichier
pip install --upgrade arcade
pip freeze | findstr -i "arcade replicate python-dotenv" > requirements.txt

# Vérifier les versions installées
pip show arcade replicate python-dotenv
```

---

## Sauvegardes (debug)

Les sauvegardes sont dans `save/` en mode dev, à côté de l'exe en mode frozen.

```bash
# Remettre les sauvegardes à zéro (dev)
del save\character_save.json
del save\quests_save.json
del save\saves.json

# Copier le template de quêtes pour repartir de zéro
copy quests\quests_save_file\quests_default_save.json save\quests_save.json
```

---

## Vérifications rapides

```bash
# Vérifier la syntaxe de tous les fichiers Python
python -m compileall . -q

# Vérifier que les imports principaux fonctionnent
python -c "import main; print('OK')"

# Tester les modules de la nouvelle architecture
python -c "
from world.scene.scene_manager import SceneManager
from world.scene.base_scene import BaseScene
from world.maps.home_scene import HomeScene
from world.maps.phl_scene import PhlScene
from world.maps.tma_scene import TmaScene
from ui.hud.interact_ui import InteractUI
from ui.cutscene.cutscene_manager import CutsceneManager
from input.input_handler import InputHandler
from character.ai.kyle_ai import KyleAI
print('Tous les modules OK')
"

# Vérifier qu'un module spécifique importe correctement
python -c "from world.objects.interactables.up_stat import UpStat; print('OK')"
```

---

## Structure des modules (nouvelle architecture)

```
world/          espace de jeu (world-space)
  scene/        BaseScene, SceneManager, LoadingView
  maps/         HomeScene, PhlScene, TmaScene
  loader/       MapLoader (lit map/map_configs/*.json)
  objects/      UpStat, UpStatCollection, MapActionObject, ObjetInteractif
  environment/  Environnement

ui/             interface (screen-space)
  dialogue/     DialogueSystem, CutscenePopup
  cutscene/     CutsceneManager, cutscene_data
  menus/        StatsView, Menu, DeathMenu
  hud/          InteractUI, QuestNotif
  effects/      ScreenFade

input/          InputHandler, MOVE_KEYS (AZERTY)
character/ai/   KyleAI
```

> Les anciens fichiers `map/` sont conservés mais inactifs — le jeu importe exclusivement depuis `world/`, `ui/`, `input/`.
