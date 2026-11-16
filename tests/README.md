# Test fixtures

`scripts/validate_blender52.py` imports every `.lwo`, `.lwo2`, and `.lwo3`
file below the following fixture roots:

- `basic/src`
- `assimp/src`
- `lwo_interceptor/src`

Referenced images and fixture provenance notes are retained beside the object
files. Historical Blender output snapshots, fixtures for unsupported formats,
and inactive submodule corpora are intentionally not part of this repository.

The `assimp` fixtures originate from Assimp's public test-model corpus. Files
with specific source or redistribution notes retain those notes next to the
fixture.
