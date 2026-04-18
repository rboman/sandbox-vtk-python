# Plan de mise en oeuvre du sandbox VTK / C++ / Python

## 1. Executive summary
- Oui, ton architecture de principe est la bonne.
- La correction essentielle est la suivante: pour chaque cible, **un seul build VTK cohérent** produit à la fois un **SDK natif** pour la compilation C++ et un **wheel `vtk`** pour le runtime Python, mais **pendant l’exécution Python la source d’autorité des bibliothèques VTK doit être le wheel installé dans le venv, jamais `external/install`**.
- Je recommande donc: `build VTK -> install SDK -> build wheel vtk -> installer le wheel dans le venv -> installer pyvista sous contraintes -> construire/installer codecpp contre le SDK mais le faire charger les bibliothèques VTK du venv au runtime`.

## 2. Recommended architecture
- **Source d’autorité compile-time**: `external/install/vtk-9.3.1/<target>/sdk/` avec headers, libs, CMake config, fichiers de version et manifeste.
- **Source d’autorité runtime Python**: le wheel `vtk==9.3.1` installé dans `.venvs/<target>/.../site-packages`, avec ses DLL/.so.
- **`codecpp`** compile contre le SDK via `find_package(VTK CONFIG REQUIRED)` mais ne vendore pas VTK en phase 1; il résout VTK au runtime vers le venv.
- **`codepy`** reste pur Python et dépend de `pyvista`, mais son installation doit toujours passer par un mécanisme contraint qui empêche `pip` de tirer un autre `vtk`.

## 3. Alternative architectures considered
- **Utiliser l’install tree VTK comme runtime Python** via `PYTHONPATH`/`PATH`/`LD_LIBRARY_PATH`: rejeté, car cela mélange compile-time et runtime, masque l’origine réelle des binaires et rend les erreurs d’import dépendantes de l’environnement.
- **Construire deux VTK distincts** par cible, un pour le SDK et un pour le wheel: rejeté en phase 1, car cela double le coût et augmente le risque de divergence ABI/options.
- **Bundler une seconde copie de VTK dans `codecpp`**: rejeté, car c’est précisément le scénario qui crée les conflits de DLL/.so dans un seul processus.
- **S’appuyer sur une distribution système/Conda**: rejeté, car ce n’est ni l’objectif du sandbox ni le meilleur moyen de prouver la cohérence binaire voulue.

## 4. Build-time model
- Nom de cible recommandé: `win-amd64-msvc2022-py310-release` et `linux-x86_64-gcc-py312-release` en phase 1.
- Un build VTK par tuple `(OS, arch, toolchain, python ABI, build type)` dans `external/build/vtk-9.3.1/<target>/`.
- Le même build VTK doit recevoir explicitement `VTK_WRAP_PYTHON=ON`, `VTK_WHEEL_BUILD=ON`, `Python3_EXECUTABLE=<python du venv cible>` et un profil large: Rendering, Views, StandAlone, OpenGL2, InteractionStyle, RenderingMatplotlib, Qt=`WANT`, QtQuick=`DONT_WANT`.
- `cmake --install` alimente `external/install/vtk-9.3.1/<target>/sdk/`; la génération du wheel alimente `external/wheelhouse/vtk-9.3.1/<target>/`.
- **Compile-time only**: `VTK_DIR`, `CMAKE_PREFIX_PATH`, headers, import libs, CMake targets. **À éviter**: `PYTHONPATH`, `PATH`, `LD_LIBRARY_PATH`, `INCLUDE`, `LIB` globaux pour faire “marcher” la compilation.

## 5. Run-time model
- Pendant `python -c "import codecpp, pyvista"`, les bibliothèques VTK doivent venir **du wheel `vtk` installé dans le venv**, pas du SDK.
- **Windows**: `packages/codecpp/src/codecpp/__init__.py` doit d’abord localiser `vtkmodules` dans le venv, dériver les répertoires candidats contenant les DLL VTK dans `site-packages`, appeler `os.add_dll_directory(...)` pour chacun, puis seulement importer `_codecpp.pyd`.
- **Linux**: ne pas compter sur `__init__.py` pour corriger le chargeur; `_codecpp.so` doit être construit avec un `RUNPATH` relatif de type `$ORIGIN:$ORIGIN/../vtkmodules:$ORIGIN/../vtk.libs` pour résoudre les bibliothèques VTK du wheel installé comme paquet voisin dans `site-packages`.
- En phase 1, **aucun shell Python normal** ne doit exporter `PATH`/`LD_LIBRARY_PATH` vers `external/install/.../sdk/bin` ou `sdk/lib`.
- Un shell de diagnostic séparé peut exister plus tard pour les binaires natifs hors Python, mais il doit être explicitement distinct du flux venv.

## 6. Packaging model
- Le `pyproject.toml` racine reste **outil de repo**, pas package monolithique.
- `packages/codecpp` doit être un package Python natif moderne, idéalement via `scikit-build-core`, avec CMake + SWIG comme vérité de build.
- `packages/codecpp` doit être installé **non editable** en phase 1 pour figer le layout et la logique de chargement; l’editable est à repousser après validation du modèle.
- `packages/codepy` et `packages/pmanager` peuvent être installés en editable, car ils sont purs Python.
- `pyvista` ne doit jamais être installé “nu”. Le flux supporté est: wheel VTK local visible via `--find-links`, puis installation sous **fichier de contraintes** qui épingle `vtk==9.3.1` et une version exacte de `pyvista`; si cette combinaison n’est pas compatible, l’installation doit échouer bruyamment, pas remplacer `vtk`.

## 7. Cross-platform strategy
- Windows et Ubuntu partagent le même modèle logique, mais pas les mêmes mécanismes de chargement natif.
- **Windows phase 1 obligatoire**: VS 2022, Python 3.10, build `Release`.
- **Ubuntu phase 1 obligatoire**: Ubuntu 24.04, Python 3.12 natif, build `Release`; le support Ubuntu `py310` reste préparé par le design mais reporté.
- Le profil VTK “broad for PyVista” est obligatoire; le volet Qt est documenté et activable quand les prérequis sont présents, mais les démos Qt ne sont pas un critère d’acceptation de phase 1.

## 8. Proposed repository tree
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
│  ├─ ubuntu/
│  └─ validate/
├─ examples/
├─ tests/
└─ .venvs/<target>/
```

## 9. Role of each important file
- `CMakePresets.json`: définit les presets canoniques par cible et évite les commandes CMake implicites ou divergentes.
- `constraints/py310.txt` et `constraints/py312.txt`: épinglent `vtk`, `pyvista` et les dépendances Python validées.
- `docs/architecture.md`: contrat principal compile-time vs runtime.
- `docs/runtime-model.md`: règles Windows/Linux de découverte des DLL/.so, anti-patterns inclus.
- `packages/codecpp/pyproject.toml`: packaging du module SWIG natif.
- `packages/codecpp/CMakeLists.txt`: build du cœur C++, SWIG, liens VTK, `RUNPATH` Linux.
- `packages/codecpp/src/codecpp/__init__.py`: bootstrap runtime Windows avant import de `_codecpp`.
- `packages/codecpp/src/codecpp/_runtime.py`: logique de découverte de runtime, diagnostics et reporting de provenance.
- `scripts/validate/runtime_provenance.py`: vérifie l’origine effective des bibliothèques VTK chargées.
- `packages/pmanager/src/pmanager/cli.py`: squelette CLI, sans orchestration complète en phase 1.

## 10. Development workflow on Windows
- Créer `.venvs/win-amd64-msvc2022-py310-release` avec Python 3.10.
- Configurer et builder VTK 9.3.1 depuis `external/src` vers `external/build/vtk-9.3.1/win-amd64-msvc2022-py310-release`.
- Installer le SDK dans `external/install/.../sdk` et produire le wheel dans `external/wheelhouse/...`.
- Installer le wheel `vtk` local puis `pyvista` sous contraintes dans le venv; ne jamais injecter `external/install/.../sdk/bin` dans `PATH` du venv.
- Builder et installer `codecpp` contre le SDK, puis lancer les tests d’import et de provenance.

## 11. Development workflow on Ubuntu
- Créer `.venvs/linux-x86_64-gcc-py312-release` avec Python 3.12 pour la phase 1.
- Réutiliser la logique déjà validée sous Ubuntu, mais en chemins repo-locaux au lieu de `/opt/vtk-*`.
- Produire SDK et wheel VTK depuis le même build tree.
- Installer `vtk` local puis `pyvista` sous contraintes dans le venv; ne pas utiliser `PYTHONPATH` ni `LD_LIBRARY_PATH` vers le SDK pour les tests Python.
- Builder et installer `codecpp`, puis vérifier `RUNPATH`, imports croisés et provenance réelle des `.so`.

## 12. Validation matrix
- **Build provenance**: le manifeste VTK doit enregistrer version VTK, source tarball, générateur CMake, Python cible, options majeures et chemin du SDK.
- **Python runtime provenance**: après import, toutes les bibliothèques VTK chargées doivent pointer vers le venv.
- **Import order**: `import codecpp; import pyvista` puis `import pyvista; import codecpp` doivent réussir sur les deux plateformes cibles.
- **Smoke VTK/PyVista**: `vtk.vtkVersion.GetVTKVersion()` et une opération PyVista offscreen triviale doivent réussir.
- **Smoke codecpp**: une fonction triviale du wrapper SWIG doit réussir sans échange d’objets VTK.
- **Negative guard**: le script de validation doit échouer s’il détecte `external/install/.../sdk` dans les origines runtime VTK.
- **Static dependency guard**: Windows `dumpbin` ou équivalent, Linux `readelf/ldd`, doivent montrer que `_codecpp` dépend bien de VTK et que la stratégie de résolution prévue est cohérente.

## 13. Risk register
- Le layout réel du wheel VTK peut varier selon plateforme; la logique de découverte doit être validée expérimentalement avant de figer les chemins relatifs.
- Un `pyvista` futur peut durcir ses contraintes et rendre `vtk==9.3.1` incompatible; le rôle du fichier de contraintes est de transformer cela en échec visible.
- Sur Windows, un `PATH` pollué peut masquer une erreur de bootstrap et charger des DLL VTK étrangères.
- Sur Linux, un `RUNPATH` incomplet peut fonctionner sur une machine et casser sur une autre.
- Le profil VTK “large + Qt WANT” peut augmenter les prérequis et la durée de build, surtout sous Windows.

## 14. Open questions / assumptions
- Hypothèse verrouillée pour phase 1: `Windows py310` et `Ubuntu py312` sont les deux cibles obligatoires; `Ubuntu py310` est reporté.
- Hypothèse à valider: le wheel VTK 9.3.1 expose ses bibliothèques sous `vtkmodules` et/ou un répertoire frère de type `vtk.libs`.
- Hypothèse à valider expérimentalement: la version exacte de `pyvista` compatible avec `vtk==9.3.1` sera épinglée dans `constraints/`; l’architecture n’en dépend pas, mais la validation oui.
- Point volontairement reporté: packaging “release-grade” de `codecpp` pour redistribution externe, CI et matrice multi-Python complète.

## 15. Suggested implementation phases
- **Phase A**: documentation d’architecture, conventions de nommage, `CMakePresets`, contraintes Python, ADR de séparation SDK/runtime.
- **Phase B**: pipeline VTK repo-local par cible, avec manifeste de build et wheelhouse.
- **Phase C**: packaging/install contrôlé du venv avec `vtk` local et `pyvista` sous contraintes.
- **Phase D**: `codecpp` natif + SWIG + bootstrap Windows + `RUNPATH` Linux.
- **Phase E**: validation automatisée, exemples d’import croisé, squelette `pmanager`.

## 16. Suggested first thin slice
- Premier thin slice recommandé: **Windows py310 end-to-end**, car c’est la zone la moins validée et celle où le problème de DLL est le plus piégeux.
- Ce thin slice doit prouver: build VTK broad, wheel local, venv propre, install `pyvista` sous contraintes, install `codecpp`, import des deux modules dans les deux ordres, rapport de provenance lisible.
- Les démos Qt, la matrice multi-Python et l’orchestration complète `pmanager` restent hors thin slice.

## 17. Suggested acceptance criteria for phase 1
- L’arborescence cible et les conventions de nommage sont figées et documentées.
- La séparation **compile-time only** vs **runtime only** est écrite noir sur blanc, avec interdictions explicites.
- La stratégie Windows `os.add_dll_directory` et la stratégie Linux `RUNPATH` sont définies.
- La stratégie d’installation de `pyvista` sans remplacement silencieux de `vtk` est définie.
- La matrice de validation, les risques et l’ordre d’implémentation sont suffisamment précis pour passer à une conversation d’implémentation fichier par fichier.

## 18. Les 5 décisions de design les plus importantes
- Le runtime Python VTK autoritaire est le wheel `vtk` du venv, jamais le SDK natif.
- Le même build VTK par cible produit à la fois SDK et wheel.
- `codecpp` ne doit pas embarquer une seconde copie de VTK en phase 1.
- `codecpp` est non-editable en phase 1; `codepy` et `pmanager` peuvent être editables.
- `pyvista` s’installe uniquement sous contraintes qui épinglent `vtk==9.3.1`.

## 19. Les 5 plus gros risques
- Découverte erronée des DLL/.so du wheel VTK.
- Remplacement silencieux de `vtk` par `pip` si le flux d’installation n’est pas verrouillé.
- Pollution de `PATH`/`LD_LIBRARY_PATH` qui masque les vraies origines runtime.
- Divergence future entre build VTK large et prérequis Qt/OpenGL par plateforme.
- Complexité d’intégration SWIG + CMake + packaging natif si le layout n’est pas figé tôt.

## 20. Ordre exact d’implémentation recommandé
1. Écrire `docs/architecture.md`, `docs/runtime-model.md` et l’ADR “VTK runtime authority”.
2. Introduire `CMakePresets.json` et la convention de noms `<target>`.
3. Mettre en place `constraints/py310.txt` et `constraints/py312.txt`.
4. Implémenter le pipeline repo-local VTK: fetch, configure, build, install SDK, build wheel, manifeste.
5. Implémenter la création/synchronisation du venv avec installation du wheel `vtk` et de `pyvista` sous contraintes.
6. Créer le package `codecpp` avec CMake + SWIG + packaging natif.
7. Ajouter `codecpp/__init__.py` et `_runtime.py` pour le bootstrap Windows et les diagnostics.
8. Ajouter la stratégie `RUNPATH` Linux et la validation statique des dépendances.
9. Ajouter les scripts/tests de provenance et les tests d’ordre d’import.
10. Ajouter `codepy`, puis le squelette `pmanager`, puis seulement après étendre la matrice et les variantes.

Références externes utiles pour calibrer la partie `pyvista`: [PyVista sur PyPI](https://pypi.org/project/pyvista/) ; [discussion PyVista sur le remplacement de `vtk` par un autre wheel VTK](https://github.com/pyvista/pyvista/discussions/5597).
