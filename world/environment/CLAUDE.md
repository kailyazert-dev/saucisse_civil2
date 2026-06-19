# world/environment/

Données de contexte social d'un lieu de jeu.

## Fichiers

| Fichier | Classe | Rôle |
|---|---|---|
| `environnement.py` | `Environnement` | Paramètres sociaux d'une zone |

## Environnement

```python
env = Environnement(
    nom="PHL",
    tension_sociale=0.7,
    densite_sociale=0.5,
    regles_sociale="corporatif"
)
env.get_stat()  # → string formaté pour affichage debug
```

Attributs :
- `nom` — identifiant du lieu
- `tension_sociale` — niveau de stress ambiant (0.0 → 1.0)
- `densite_sociale` — densité de population (0.0 → 1.0)
- `regles_sociale` — régime social (string libre)

Passé en premier argument au constructeur de `BaseScene` mais non utilisé activement dans le rendu actuel. Prévu pour influencer le comportement des PNJs et les dialogues IA.
