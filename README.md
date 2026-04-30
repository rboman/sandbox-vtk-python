# sandbox-vtk-python

Sandbox multi-plateforme pour un workflow C++/Python autour de VTK 9.3.1.

## Public visé

Ce README s'adresse aux développeurs applicatifs des packages `codecpp` et `codepy`.
Il explique comment utiliser `pmanager` tel qu'il fonctionne actuellement.

La documentation orientée maintenance du système de build est dans [AGENTS.md](AGENTS.md).

## Ce que fournit le repository

- un build VTK local par cible (`external/build/...`)
- un SDK natif VTK par cible (`external/install/.../sdk`)
- un wheel Python local `vtk` par cible (`external/wheelhouse/...`)
- des environnements virtuels cibles (`.venvs/<target>/`)
- une orchestration Python-first via `pmanager`

## Cibles supportées

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## Démarrage rapide

### Windows (`cmd.exe`)

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
pmanager workflow windows-phase1
```

### Linux

```bash
python scripts/bootstrap-dev-env.py
source .venvs/pmanager-dev/bin/activate
pmanager workflow linux-phase1
```

## Commandes utiles pour les développeurs `codecpp` / `codepy`

```text
pmanager fetch vtk
pmanager build vtk --configure
pmanager build vtk --build
pmanager build vtk --install
pmanager build vtk --wheel
pmanager sync venv
pmanager validate provenance
pmanager validate import-order --require-extension
```

## Contrat runtime

Dans un venv cible:

- `vtk`, `pyvista` et `codecpp` partagent le meme runtime VTK
- les bibliotheques VTK chargees proviennent du venv cible
- le SDK natif reste une autorite de compilation, pas une autorite runtime Python

## Pour développer les packages

- `packages/codecpp`: extension C++/SWIG qui compile contre le SDK VTK de la cible
- `packages/codepy`: package Python qui utilise `pyvista` dans le meme venv cible

Utiliser les exemples de [examples/README.md](examples/README.md) pour verifier les imports croises.

## Documentation

- [docs/python-first-dev-env.md](docs/python-first-dev-env.md): usage quotidien de `pmanager`
- [docs/build-flow.md](docs/build-flow.md): flux build/sync/validate
- [docs/runtime-model.md](docs/runtime-model.md): regles runtime
- [docs/environment-hygiene.md](docs/environment-hygiene.md): hygiene d'environnement
- [docs/validation-matrix.md](docs/validation-matrix.md): verifications attendues
