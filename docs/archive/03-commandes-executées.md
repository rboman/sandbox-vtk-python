Le mieux pour avancer maintenant, c’est que **tu exécutes le premier thin slice réel sur ton PC Windows**, et que **je poursuive ensuite à partir de ton retour**. C’est la partie la plus utile, parce que le dépôt est prêt, mais les inconnues critiques sont maintenant machine-réelles: source VTK, build Visual Studio, wheel généré, et surtout interaction avec ton environnement historique.

En clair: **oui, j’ai besoin de toi pour la prochaine étape**, surtout pour le build VTK. Dès que tu me donnes le résultat, je reprends la main pour corriger, ajuster les scripts et verrouiller le flux.

**Ce que tu dois faire sur Windows**
1. À la racine du repo, crée le venv cible:
```powershell
C:\Python310\python.exe -m venv .venvs\win-amd64-msvc2022-py310-release
```

2. Place les sources VTK 9.3.1 ici:
```text
external\src\vtk-9.3.1\
```
Il faut que ce dossier contienne le vrai source tree VTK, pas juste l’archive.

3. Ouvre le shell propre du repo:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\enter-clean-dev-shell.ps1 -Target win-amd64-msvc2022-py310-release
```

4. Dans ce shell propre, lance d’abord l’audit:
```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\audit-environment.py --mode strict --target-venv .\.venvs\win-amd64-msvc2022-py310-release
```

5. Si l’audit passe, lance le build VTK:
```powershell
& .\scripts\windows\build-vtk.ps1 -Target win-amd64-msvc2022-py310-release -PythonExe .\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe
```

6. Si le build VTK va au bout, synchronise le venv:
```powershell
& .\scripts\windows\sync-venv.ps1 -Target win-amd64-msvc2022-py310-release
```

7. Puis lance les validations runtime:
```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\runtime-provenance.py --target-venv .\.venvs\win-amd64-msvc2022-py310-release --target-sdk-root .\external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk
```

```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\import-order.py --require-extension
```

**Très important**
- Utilise bien **le Python du venv explicitement**, pas `python` tout court.
- Si une étape échoue, **arrête-toi là** et envoie-moi:
  - la commande lancée
  - le message d’erreur complet
  - et si possible les 30 à 80 dernières lignes de sortie

**Ce que je te recommande**
Commence par les étapes `1` à `5`. C’est le point le plus utile. Si ça casse au configure ou au build VTK, j’aurai déjà assez de matière pour t’aider précisément. Si ça passe, on enchaîne avec `6` et `7`.

Quand tu veux, envoie-moi le retour de la première étape qui échoue, ou dis-moi simplement: `l'audit a échoué`, `le configure VTK a échoué`, `le build VTK est terminé`, etc.