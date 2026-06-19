Commit toutes les modifications en cours et pousse sur le dépôt distant (branche `refont`).

Le message de commit est : $ARGUMENTS

## Instructions

1. Lance `git status` pour voir les fichiers modifiés et non suivis.
2. Lance `git diff` pour analyser le contenu des changements si aucun message n'est fourni.
3. Ajoute tous les fichiers avec `git add .`
4. Crée un commit :
   - **Avec message** (`$ARGUMENTS` non vide) : utilise le message tel quel.
   - **Sans message** : génère un message court et pertinent en français décrivant les modifications détectées. Format : verbe d'action + objet (ex. "ajout système de combat", "correction import InputHandler").
5. Pousse sur `origin refont` avec `git push origin refont`.
6. Confirme le succès en affichant le hash du commit et les fichiers inclus.

## Exemples d'appel

```
/commit-push ajout système de combat zombies
/commit-push correction imports nouvelle architecture
/commit-push                    ← message auto-généré
```
