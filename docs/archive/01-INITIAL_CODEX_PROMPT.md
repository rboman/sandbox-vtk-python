You are helping me design a cross-platform sandbox repository for a mixed C++ / Python project.

I do NOT want code implementation first.
I want a planning pass first.

Your task in this conversation is to produce a rigorous implementation plan for the repository, file layout, build flow, packaging flow, runtime model, and validation strategy.

## Project context

I work on both Windows and Ubuntu.
Windows and Ubuntu are both important targets from the beginning.

I often build C++ libraries using VTK with CMake.
On Windows, I use Visual Studio 2022.
I want to freeze VTK to version 9.3.1 because I also use that version on Ubuntu.

I have a native C++ library called `codecpp`.
It is exposed to Python via SWIG:
- `codecpp.i` is the SWIG interface file
- `codecpp.py` contains shadow classes
- `_codecpp.pyd` / `_codecpp.so` is the compiled extension module depending on platform

In the same Python environment, I also want a pure Python package called `codepy` that uses `pyvista`.

The core problem is that `pyvista` depends on Python `vtk`, and I must avoid having a second incompatible VTK runtime in the same Python process.
Even if `codecpp` and `pyvista` never exchange VTK objects, importing both in one process can still break due to VTK DLL / shared-library conflicts.

## What is already known from my existing Ubuntu workflow

I already have Ubuntu shell scripts that do the following successfully:

- download VTK 9.3.1 sources
- configure CMake with:
  - `VTK_WRAP_PYTHON=ON`
  - `VTK_WHEEL_BUILD=ON`
  - `Python3_EXECUTABLE=$(which python)`
  - several rendering/view/Qt-related VTK options enabled
- build VTK
- create a local Python wheel using `python3 setup.py bdist_wheel`

I also have an install script that installs VTK under `/opt/vtk-9.3.1` and sets environment variables for:
- PATH
- LD_LIBRARY_PATH
- PYTHONPATH
- INCLUDE
- LIB
- CMAKE_PREFIX_PATH

This means I already validated the general idea of:
- native VTK build
- Python VTK wrappers
- local VTK wheel generation

## Main engineering goal

Design a sandbox proving that:
- a custom-built VTK 9.3.1 can be used for native C++ compilation
- a matching Python VTK wheel can be used inside a virtual environment
- `codecpp` and `pyvista` can be imported in the same process without runtime conflicts
- the effective VTK binary origins are observable and testable
- the repository layout is ready to grow later toward more third-party libraries

## Constraints

- Platforms: Windows + Ubuntu
- Initial Python target: Python 3.10 must be supported first
- Other Python versions should remain possible later
- Build system: CMake
- Python environment management for phase 1: `venv + pip`
- Python packaging: modern `pyproject.toml`
- SWIG is the first binding technology to keep
- Future docs may mention pybind11 / nanobind as possible later variants
- This is a sandbox: functionality is trivial, architecture is the main concern
- No public PyPI workflow is required
- A local wheelhouse is perfectly acceptable
- No GitHub Actions required in phase 1
- `pmanager` only needs a CLI skeleton in v1
- Long-term goal: the orchestration model should later support several external libraries, not only VTK

## Important design question

I currently believe the best design is:

1. build VTK from source
2. produce a native install tree / SDK view for C++ compilation
3. produce a local Python wheel for `vtk==9.3.1`
4. install that wheel into the venv
5. install `pyvista` in a way that does not pull an unwanted different `vtk`
6. ensure `codecpp` also uses that same VTK runtime during Python execution

Please evaluate whether this is indeed the best architecture.
If you think another architecture is better, explain exactly why.

## VTK completeness requirement

Do NOT propose a tiny minimal VTK build.
The VTK build should be as complete as reasonably needed for realistic PyVista usage.
My Ubuntu scripts already enable a fairly broad VTK feature set, including rendering, views, OpenGL2, interaction style, matplotlib rendering, and Qt-related options.

Please take that into account when planning.

## Repository I want to end up with

I expect something conceptually like:

- a root repository
- `packages/codecpp`
- `packages/codepy`
- `packages/pmanager`
- `external/src`
- `external/build`
- `external/install`
- `external/wheelhouse`
- `docs`
- `examples`
- `tests`

I want the repository to be explicit about compile-time vs runtime concerns.

## Your deliverable in this conversation

Do NOT start implementing files yet.
Instead, provide a planning document with these sections:

1. Executive summary
2. Recommended architecture
3. Alternative architectures considered
4. Build-time model
5. Run-time model
6. Packaging model
7. Cross-platform strategy
8. Proposed repository tree
9. Role of each important file
10. Development workflow on Windows
11. Development workflow on Ubuntu
12. Validation matrix
13. Risk register
14. Open questions / assumptions
15. Suggested implementation phases
16. Suggested first thin slice
17. Suggested acceptance criteria for phase 1

## Additional requirements

- Be explicit about what belongs to compile-time only vs run-time only.
- Be explicit about where VTK DLLs / shared libraries should come from during Python execution.
- Be explicit about how to avoid accidental mixing of SDK binaries and venv runtime binaries.
- Be explicit about whether editable installs are acceptable for each package.
- Be explicit about how `codecpp/__init__.py` should bootstrap native library loading on Windows.
- Be explicit about how Linux runtime library discovery should be handled.
- Be explicit about how `pyvista` should be installed so that it does not silently pull an unwanted different `vtk`.
- Be explicit about what should be validated by scripts.
- Be explicit about what should be postponed to later phases.
- Call out any hardcoded-path anti-patterns that should be avoided.
- Propose naming conventions for build/install directories that include platform and Python version.

## Guidance for your answer style

- Think like a senior build/release engineer for scientific software.
- Optimize for reproducibility, observability, and debuggability.
- Prefer simple, robust choices over clever ones.
- Call out hidden traps.
- If something is uncertain, label it clearly as an assumption or a point to validate experimentally.
- Keep the plan concrete enough that a later implementation chat can execute it file by file.

At the end, give:
- the 5 most important design decisions
- the 5 biggest risks
- the exact order in which you would implement the repository

> **IMPORTANT**: Bien que ce message et les fichiers soient rédigés en anglais, je veux que tu dialogues avec moi en FRANCAIS. Merci d'avance!
 
---

remarque ajoutée:

J'aimerais que tu prennes en compte tout le long du développement que je travaille sur un PC Windows et un PC Ubuntu dont l'environnement de base a été configuré de manière un peu "brutale" via des variables d'environnement. Ceci parce que je developpe beaucoup de programmes et que j'avais l'habitude de tout compiler moi même et de tout exposer de manière globale (jusqu'à l'utilisation de pip dont je suis en train de me former aujourd'hui). J'ai donc peut que des variables globales telles que PYTHONPATH, PATH ou autre perturbent le procédé. Il faudra donc a tout moment que tu gardes ça en tête et/ou que tu me dises comment faire pour nettoyer mon environnement et éviter les conflits avec, par exemple, un VTK installé dans mon installation python de mes machine. Je veux etre sur que tu as bien ca en tête et que tu inclues ces précautions dans ton plan de développement.
