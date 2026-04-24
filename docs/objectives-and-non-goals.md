# Objectives and non-goals

## Context

This repository supports numerical simulation development in a university
laboratory.

The expected users are a small group: primarily the project owner, possibly a
student or close collaborator. The workflow should be easy to understand, easy
to run step by step, and easy to debug on a research workstation.

This is not intended to become a large institutional build platform. Prefer the
simple solution when it is good enough for daily laboratory work.

## Objectives

- design a robust repository structure
- support Windows and Ubuntu
- support Python 3.10 first
- support local wheel-based VTK installation
- prepare a Python-first `pmanager` orchestration tool
- keep the project ready for later support of multiple external libraries
- make the workflow understandable enough for a student to use and adapt

## Simplicity rules

- Assume network access is available for installing basic Python tooling.
- Avoid large fallback systems unless a real lab workflow needs them.
- Ask before adding compatibility machinery that makes the project harder to
  understand.
- Keep VTK as the concrete first recipe; generalize only after a second library
  makes the shared pattern clear.
- Keep shell scripts as thin as possible once Python replacements are validated.

## Non-goals for phase 1

- no public PyPI strategy
- no CI requirement
- no real application logic
- no advanced GUI
- no production installer yet
- no migration away from SWIG yet
- no plugin architecture for external libraries yet
- no offline package-management strategy yet
