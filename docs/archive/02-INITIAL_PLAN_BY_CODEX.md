# Plan de mise en oeuvre du sandbox VTK / C++ / Python avec hygiène d’environnement stricte

## 1. Executive summary
- L’architecture recommandée reste la même: **un build VTK cohérent par cible**, produisant à la fois un **SDK natif** pour le C++ et un **wheel `vtk`** pour le runtime Python.
- La contrainte supplémentaire, désormais explicite, est la suivante: **le dépôt doit fonctionner de manière prédictible même sur des machines dont l’environnement global est pollué** par `PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, `CMAKE_PREFIX_PATH`, `VTK_DIR`, anciens Python, anciens VTK, ou anciens paquets `vtk`/`pyvista`.
- En pratique, cela impose une discipline forte: **tous les builds, installations et validations passent par des scripts d’enveloppe qui nettoient l’environnement avant exécution**, et les scripts doivent **échouer volontairement** s’ils détectent une pollution susceptible de fausser le résultat.

## 2. Recommended architecture
- **Source d’autorité compile-time**: `external/install/vtk-9.3.1/<target>/sdk/`
  - Contient headers, libs/import libs, CMake config, métadonnées de build, et manifeste.
  - Sert uniquement à `find_package(VTK CONFIG REQUIRED)` et à la compilation native.
- **Source d’autorité runtime Python**: le wheel `vtk==9.3.1` installé dans `.venvs/<target>/.../site-packages`
  - Contient les wrappers Python et les bibliothèques VTK effectivement chargées par le processus Python.
  - Pendant l’exécution Python, **c’est cette copie qui doit être résolue**, pas celle du SDK.
- **`codecpp`** compile contre le SDK, mais au runtime Python il doit charger le VTK du venv.
- **`codepy`** reste pur Python, dépend de `pyvista`, et ne doit jamais déclencher l’installation d’un `vtk` non désiré.
- **Contrainte d’environnement transverse**: les scripts du repo ne doivent jamais dépendre d’un état global implicite de la machine.

## 3. Alternative architectures considered
- **Utiliser l’install tree VTK comme runtime Python** via `PYTHONPATH` et `PATH`/`LD_LIBRARY_PATH`: rejeté.
  - Trop sensible aux variables globales existantes.
  - Rend les imports dépendants de l’ordre des chemins et masque les vraies origines binaires.
- **Faire confiance au shell courant de l’utilisateur**: rejeté.
  - Sur tes machines, c’est précisément le risque principal.
  - Un plan robuste doit partir du principe que le shell courant peut être contaminé.
- **Tout exposer globalement via variables système**: rejeté.
  - Bon pour du bricolage historique, mauvais pour un sandbox reproductible.
- **Deux VTK distincts par cible**: rejeté en phase 1.
  - Complexité inutile tant que l’objectif principal est de prouver la cohérence compile-time/runtime.

## 4. Build-time model
- Un build VTK par tuple `(OS, arch, toolchain, python ABI, build type)` dans `external/build/vtk-9.3.1/<target>/`.
- Noms de cibles recommandés:
  - `win-amd64-msvc2022-py310-release`
  - `linux-x86_64-gcc-py312-release`
- Le build VTK reçoit explicitement:
  - `VTK_WRAP_PYTHON=ON`
  - `VTK_WHEEL_BUILD=ON`
  - `Python3_EXECUTABLE=<python du venv cible>`
  - Profil large pour PyVista: Rendering, Views, StandAlone, OpenGL2, InteractionStyle, RenderingMatplotlib, Qt=`WANT`, QtQuick=`DONT_WANT`.
- Le même build produit:
  - `external/install/vtk-9.3.1/<target>/sdk/`
  - `external/wheelhouse/vtk-9.3.1/<target>/vtk-...whl`
- **Compile-time only**:
  - `CMAKE_PREFIX_PATH` pointant vers le SDK, mais injecté **par script local au process**, jamais imposé globalement.
  - `VTK_DIR` éventuel, mais local au process uniquement.
- **Interdits build-time**:
  - Dépendre d’un `VTK_DIR` global déjà présent.
  - Dépendre d’un `Python3_EXECUTABLE` implicite.
  - Dépendre du `python` ou du `cmake` “trouvé par hasard” dans le shell courant.

## 5. Run-time model
- Pendant `python -c "import codecpp, pyvista"`, toutes les bibliothèques VTK doivent venir du venv.
- **Windows**:
  - `codecpp/__init__.py` doit localiser `vtkmodules` dans le venv actif.
  - Il doit calculer les répertoires contenant les DLL VTK du wheel.
  - Il doit appeler `os.add_dll_directory(...)` avant l’import de `_codecpp.pyd`.
  - Il doit aussi pouvoir émettre un diagnostic clair si aucun runtime VTK cohérent n’est trouvé dans le venv.
- **Linux**:
  - `_codecpp.so` doit être construit avec un `RUNPATH` conçu pour retrouver les bibliothèques VTK du wheel installé dans le même environnement Python.
  - On évite de “réparer” cela avec `LD_LIBRARY_PATH` global.
  - `LD_LIBRARY_PATH` peut être utilisé comme outil de diagnostic manuel, mais pas comme mécanisme supporté du flux normal.
- **Règle absolue**:
  - En phase 1, les tests Python du repo ne doivent pas s’exécuter dans un shell où `PATH`, `PYTHONPATH` ou `LD_LIBRARY_PATH` réinjectent `external/install/.../sdk`.

## 6. Packaging model
- Le `pyproject.toml` racine reste un fichier d’outillage de repo, pas un package applicatif.
- `packages/codecpp`:
  - packaging natif moderne via `scikit-build-core` recommandé.
  - build via CMake + SWIG.
  - installation **non editable** en phase 1.
  - raison: le layout final du package natif et la logique de chargement doivent être figés pour être testables.
- `packages/codepy`:
  - package pur Python.
  - installation editable acceptable en phase 1.
- `packages/pmanager`:
  - squelette Typer.
  - installation editable acceptable.
- `pyvista`:
  - ne doit jamais être installé sans contrainte.
  - le flux supporté est: installation du wheel local `vtk`, puis installation de `pyvista` sous fichier de contraintes.
  - si `pyvista` exige une autre version de `vtk`, l’installation doit échouer explicitement.

## 7. Stratégie d’hygiène d’environnement
- Cette section devient une partie centrale du design, pas une note annexe.

### 7.1 Principe général
- Tous les scripts importants du repo doivent s’exécuter dans un **environnement nettoyé**.
- Le shell utilisateur est considéré comme **non fiable**.
- Les scripts du repo doivent construire eux-mêmes leur environnement minimal.

### 7.2 Variables à neutraliser ou surveiller
- Variables Python à neutraliser:
  - `PYTHONPATH`
  - `PYTHONHOME`
  - `PYTHONSTARTUP`
  - `VIRTUAL_ENV` si elle ne correspond pas au venv cible
  - `PIP_REQUIRE_VIRTUALENV` si cela gêne un flux prévu
  - `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL`, `PIP_FIND_LINKS`, `PIP_CONSTRAINT` si hérités globalement
- Variables CMake / native à neutraliser ou tracer:
  - `CMAKE_PREFIX_PATH`
  - `VTK_DIR`
  - `CMAKE_TOOLCHAIN_FILE` si non voulu
  - `INCLUDE`
  - `LIB`
  - `LIBRARY_PATH`
  - `CPATH`
- Variables de résolution runtime à neutraliser ou tracer:
  - `PATH`
  - `LD_LIBRARY_PATH`
  - `DYLD_LIBRARY_PATH` si un jour macOS entre en jeu
- Variables d’écosystèmes concurrents à neutraliser ou tracer:
  - `CONDA_PREFIX`
  - `CONDA_DEFAULT_ENV`
  - `PYTHONNOUSERSITE` doit être forcé à `1` dans les scripts de validation
  - `PIP_USER` / user-site Python doivent être rendus inoffensifs

### 7.3 Politique repo
- Les scripts du repo doivent:
  - **whitelister** les variables autorisées plutôt que blacklister partiellement.
  - journaliser l’environnement effectif utile au diagnostic.
  - échouer si un chemin suspect contenant `vtk`, `site-packages`, un ancien Python, ou une arborescence globale inattendue est détecté avant le venv ou le SDK attendu.
- Les scripts doivent fournir deux modes:
  - `audit`: observe et rapporte la pollution.
  - `strict`: refuse d’exécuter si l’environnement n’est pas conforme.

### 7.4 Nettoyage pratique recommandé pour toi
- **Windows**:
  - lancer les commandes du repo depuis un script PowerShell de “clean dev shell” qui retire du process courant les variables critiques et reconstruit un `PATH` minimal.
  - éviter d’utiliser un terminal déjà initialisé par un script maison historique.
- **Ubuntu**:
  - lancer les scripts du repo depuis un shell “nettoyé”, idéalement via `env -i` avec un whitelist minimal (`HOME`, `USER`, `SHELL`, `TERM`, `LANG`, `PATH` minimal).
  - ne pas sourcer les anciens scripts globaux VTK avant d’utiliser le repo.
- Dans les deux cas:
  - vérifier avant chaque session:
    - `python -c "import sys; print(sys.executable); print(sys.path)"`
    - `python -m pip show vtk pyvista`
    - origine de `vtk.__file__` si `vtk` est importable
  - le repo devra automatiser ces vérifications.

## 8. Cross-platform strategy
- **Windows phase 1 obligatoire**: Windows 11, VS 2022, Python 3.10.
- **Ubuntu phase 1 obligatoire**: Ubuntu 24.04, Python 3.12 natif.
- Le modèle logique est commun, mais la stratégie d’isolation diffère:
  - Windows: bootstrap explicite des DLL avant import.
  - Linux: `RUNPATH` correct + shell propre.
- Dans les deux cas, l’outillage doit supposer qu’un ancien VTK peut déjà être présent ailleurs sur la machine.

## 9. Proposed repository tree
```text
.
├─ CMakePresets.json
├─ pyproject.toml
├─ README.md
├─ constraints/
│  ├─ py310.txt
│  └─ py312.txt
├─ docs/
│  ├─ architecture.md
│  ├─ build-flow.md
│  ├─ runtime-model.md
│  ├─ environment-hygiene.md
│  ├─ validation-matrix.md
│  └─ decisions/
├─ external/
│  ├─ src/vtk-9.3.1/
│  ├─ build/
│  │  ├─ vtk-9.3.1/<target>/
│  │  └─ codecpp/<target>/
│  ├─ install/vtk-9.3.1/<target>/sdk/
│  └─ wheelhouse/
│     ├─ vtk-9.3.1/<target>/
│     └─ codecpp/<target>/
├─ packages/
│  ├─ codecpp/
│  ├─ codepy/
│  └─ pmanager/
├─ scripts/
│  ├─ windows/
│  │  ├─ enter-clean-dev-shell.ps1
│  │  ├─ build-vtk.ps1
│  │  └─ sync-venv.ps1
│  ├─ ubuntu/
│  │  ├─ enter-clean-dev-shell.sh
│  │  ├─ build-vtk.sh
│  │  └─ sync-venv.sh
│  └─ validate/
│     ├─ audit-environment.py
│     ├─ runtime-provenance.py
│     └─ import-order.py
├─ examples/
├─ tests/
└─ .venvs/<target>/
```

## 10. Role of each important file
- `docs/environment-hygiene.md`:
  - documente les variables interdites, tolérées, nettoyées, et la politique d’échec.
- `scripts/windows/enter-clean-dev-shell.ps1`:
  - crée une session PowerShell nettoyée pour tout le workflow du repo.
- `scripts/ubuntu/enter-clean-dev-shell.sh`:
  - crée un shell Linux nettoyé avec environnement whitelisté.
- `scripts/validate/audit-environment.py`:
  - inspecte `sys.path`, `site`, `pip`, variables critiques, et signale les éléments suspects.
- `scripts/validate/runtime-provenance.py`:
  - vérifie d’où viennent réellement les bibliothèques VTK chargées.
- `scripts/validate/import-order.py`:
  - valide les deux ordres d’import.
- `packages/codecpp/src/codecpp/_runtime.py`:
  - centralise la logique de découverte runtime et les diagnostics.
- `constraints/*.txt`:
  - fige les dépendances Python autorisées par cible.

## 11. Development workflow on Windows
- Ouvrir d’abord le shell propre du repo, pas un shell historique.
- Créer/activer `.venvs/win-amd64-msvc2022-py310-release`.
- Lancer l’audit d’environnement.
- Configurer/build/install VTK depuis le shell propre uniquement.
- Installer le wheel `vtk` local dans le venv.
- Installer `pyvista` sous contraintes.
- Installer `codecpp`.
- Exécuter validations:
  - audit environnement
  - provenance runtime
  - import order
  - smoke tests
- Si un ancien VTK global est détecté dans `PATH` ou via import Python, la validation doit échouer et l’indiquer explicitement.

## 12. Development workflow on Ubuntu
- Ouvrir d’abord le shell propre du repo.
- Créer/activer `.venvs/linux-x86_64-gcc-py312-release`.
- Lancer l’audit d’environnement.
- Configurer/build/install VTK depuis le shell propre uniquement.
- Installer le wheel `vtk` local dans le venv.
- Installer `pyvista` sous contraintes.
- Installer `codecpp`.
- Vérifier le `RUNPATH`, puis exécuter:
  - audit environnement
  - provenance runtime
  - import order
  - smoke tests
- Si `LD_LIBRARY_PATH` ou `PYTHONPATH` pointe vers un ancien VTK, le script doit le détecter avant de lancer les validations.

## 13. Validation matrix
- **Audit machine**
  - variables critiques présentes/absentes
  - `sys.path`
  - user-site Python actif ou non
  - `pip show vtk pyvista`
  - `vtk.__file__` si importable
- **Build VTK**
  - options CMake attendues
  - Python cible attendu
  - manifeste complet
- **SDK**
  - `find_package(VTK CONFIG REQUIRED)` résout bien le SDK du repo
- **Wheel runtime**
  - le wheel `vtk` installé dans le venv est bien celui du wheelhouse local
- **PyVista**
  - import réussi sans réinstallation sauvage de `vtk`
- **codecpp**
  - import réussi
  - smoke function SWIG réussie
- **Coexistence**
  - `import codecpp; import pyvista`
  - `import pyvista; import codecpp`
- **Provenance**
  - les libs VTK chargées viennent du venv
  - aucune lib VTK du SDK ou d’un ancien emplacement global n’est chargée
- **Negative tests**
  - le script doit détecter un `PYTHONPATH` pollué
  - le script doit détecter un `PATH`/`LD_LIBRARY_PATH` pollué
  - le script doit détecter un ancien `vtk` déjà installé ailleurs

## 14. Risk register
- L’environnement global des machines peut faire “marcher” des tests qui devraient échouer; il faut donc des vérifications négatives explicites.
- Un `vtk` déjà installé dans une autre installation Python peut être importé à la place de celui du venv.
- Un `PATH` ou `LD_LIBRARY_PATH` pollué peut faire charger les mauvaises bibliothèques VTK même si `vtk.__file__` semble correct.
- Sur Windows, des DLL système ou toolkit ajoutées historiquement peuvent précéder le venv.
- Sur Linux, les habitudes de scripts `source /opt/...` peuvent contaminer la session sans qu’on s’en rende compte.
- Le profil VTK large augmente le nombre de dépendances natives donc les occasions de collision.

## 15. Open questions / assumptions
- Hypothèse phase 1 conservée: Windows `py310` et Ubuntu `py312` sont les deux cibles obligatoires.
- Hypothèse à valider: version exacte de `pyvista` compatible avec `vtk==9.3.1` pour les cibles retenues.
- Hypothèse à valider: layout précis des bibliothèques à l’intérieur du wheel VTK selon Windows et Linux.
- Décision déjà prise: l’environnement utilisateur n’est pas une base fiable; le repo doit se protéger lui-même.
- Point reporté: nettoyage permanent des variables globales système au niveau de la machine.
  - En phase 1, on vise d’abord l’isolation et le diagnostic par repo.
  - Un guide de “désintoxication” machine pourra venir ensuite.

## 16. Suggested implementation phases
- **Phase A**: architecture, runtime model, environment hygiene, conventions de nommage.
- **Phase B**: shells propres et audit environnement.
- **Phase C**: pipeline VTK repo-local avec SDK + wheelhouse.
- **Phase D**: sync venv contrôlé avec `vtk` local + `pyvista` sous contraintes.
- **Phase E**: `codecpp` natif + SWIG + bootstrap runtime.
- **Phase F**: validations automatiques et exemples.
- **Phase G**: squelette `pmanager`.

## 17. Suggested first thin slice
- Premier thin slice recommandé: **audit environnement + shell propre + Windows py310 end-to-end**.
- Pourquoi:
  - c’est la plateforme la plus vulnérable aux collisions de DLL,
  - et ton contexte “variables globales brutales” y est particulièrement dangereux.
- Ce thin slice doit prouver:
  - que le repo détecte la pollution,
  - qu’il peut s’en isoler,
  - et qu’il fait coexister `codecpp` et `pyvista` via un runtime VTK unique.

## 18. Suggested acceptance criteria for phase 1
- Le repo dispose d’un document d’hygiène d’environnement clair.
- Le repo fournit un shell propre Windows et un shell propre Ubuntu.
- Les scripts d’audit détectent les variables et chemins pollués critiques.
- Le flux supporté n’utilise pas `PYTHONPATH`, `PATH` ou `LD_LIBRARY_PATH` globaux pour “faire marcher” Python.
- Le runtime Python charge uniquement les bibliothèques VTK du venv.
- Les imports croisés `codecpp` / `pyvista` fonctionnent sur les deux plateformes cibles.
- La provenance binaire est observable et automatisée.

## 19. Les 5 décisions de design les plus importantes
- Le shell utilisateur est considéré comme non fiable; le repo fournit son propre environnement propre.
- Le runtime VTK Python autoritaire est le wheel installé dans le venv.
- Le SDK VTK est strictement compile-time.
- `codecpp` est non-editable en phase 1 pour figer le layout runtime.
- Les scripts doivent échouer s’ils détectent une pollution d’environnement dangereuse.

## 20. Les 5 plus gros risques
- Pollution silencieuse de `PATH`, `PYTHONPATH` ou `LD_LIBRARY_PATH`.
- Présence d’un ancien `vtk` importable ailleurs sur la machine.
- Résolution Windows des DLL avant bootstrap correct de `codecpp`.
- `RUNPATH` Linux incomplet ou non conforme au layout réel du wheel.
- Compatibilité exacte `pyvista` / `vtk==9.3.1` à figer proprement.

## 21. Ordre exact d’implémentation recommandé
1. Écrire `docs/architecture.md`, `docs/runtime-model.md` et `docs/environment-hygiene.md`.
2. Définir `CMakePresets.json` et la convention `<target>`.
3. Implémenter l’audit environnement et les shells propres Windows/Ubuntu.
4. Mettre en place `constraints/py310.txt` et `constraints/py312.txt`.
5. Implémenter le pipeline VTK repo-local: fetch, configure, build, install SDK, build wheel, manifeste.
6. Implémenter la synchronisation du venv avec installation du wheel `vtk` local puis `pyvista` sous contraintes.
7. Implémenter `codecpp` avec CMake + SWIG + packaging natif.
8. Ajouter le bootstrap Windows dans `codecpp/__init__.py` et les diagnostics runtime.
9. Ajouter la stratégie Linux `RUNPATH` et la vérification de dépendances natives.
10. Ajouter les tests de provenance, d’ordre d’import et les smoke tests.
11. Ajouter `codepy`.
12. Ajouter le squelette `pmanager`.
13. Seulement ensuite, envisager extension de matrice, Qt plus ambitieux, ou guide de nettoyage système permanent.

## 22. Consigne de développement à garder en tête en permanence
- À chaque étape future du développement, le repo devra être pensé comme s’il s’exécutait sur une machine potentiellement contaminée par des habitudes anciennes de build global.
- Si une solution “marche” seulement parce qu’une variable globale aide en douce, elle devra être considérée comme invalide.
- Toute hypothèse cachée sur l’environnement devra être soit:
  - supprimée par isolation,
  - soit détectée par audit,
  - soit documentée comme précondition explicite.

Références utiles pour calibrer `pyvista`: [PyVista sur PyPI](https://pypi.org/project/pyvista/) ; [discussion PyVista sur le remplacement de `vtk` par un autre wheel VTK](https://github.com/pyvista/pyvista/discussions/5597).
