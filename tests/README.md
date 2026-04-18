# tests

The automated tests focus on repository logic that should work even before a real VTK build exists locally:

- environment audit classification
- runtime bootstrap path discovery
- CLI surface and target conventions
- runtime provenance summarization logic

The first true end-to-end VTK validation will happen once the local SDK and wheel flows are exercised on the supported targets.
