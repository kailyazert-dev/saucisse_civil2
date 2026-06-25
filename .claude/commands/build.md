Compile le jeu en exécutable Windows standalone via PyInstaller.

## Instructions

1. Vérifie que PyInstaller est installé : `pip show pyinstaller`. Si absent, l'installe avec `pip install pyinstaller`.
2. Lance le build : `pyinstaller saucisse.spec`
3. Attend la fin du build (peut prendre 30–60 secondes).
4. Vérifie que `dist/SaucisseCivilisation.exe` existe.
5. Confirme le succès en affichant le chemin de l'exe et sa taille.

En cas d'erreur, affiche les dernières lignes du log PyInstaller pour aider au diagnostic.

## Exemple d'appel

```
/build
```
