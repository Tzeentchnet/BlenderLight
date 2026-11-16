[![BlenderLight CI](https://github.com/Tzeentchnet/BlenderLight/actions/workflows/ci.yml/badge.svg)](https://github.com/Tzeentchnet/BlenderLight/actions/workflows/ci.yml)

# BlenderLight

BlenderLight is an independently maintained Blender 5.2 extension for
importing LightWave object files. It supports classic LWOB objects, LWO2, and
the commonly used geometry and material portions of LWO3.

## Features

- LightWave 4/5 `LWOB` and layered `LWLO`
- LightWave 6+ `LWO2`
- LightWave 2018+ `LWO3`
- Multi-layer meshes and layer parenting
- Faces, loose points and edges, subpatches, Catmull-Clark subdivision, and
  native Blender n-gons
- Surface assignments and Principled BSDF material conversion
- LWO3 standard-node values and color image references
- Point and discontinuous UV maps
- RGB/RGBA color attributes
- Weight maps, relative and absolute morphs, edge creases, and custom normals
- Skelegon-to-armature conversion
- Blender file drag-and-drop for `.lwo`, `.lwo2`, and `.lwo3`
- NumPy-backed bulk mesh and attribute transfer

See the [LightWave handler research](docs/lightwave-handler-research.md) for
the implementations reviewed and future format-coverage priorities.

## Requirements

- Blender 5.2 LTS or newer
- No external Python packages at runtime

BlenderLight uses Blender's bundled NumPy.

## Install

Download a release archive, or build one from the repository:

```powershell
& "D:\Blender Foundation\Blender 5.2\blender.exe" `
  --command extension build `
  --source-dir io_scene_lwo `
  --output-dir dist
```

In Blender, open **Edit > Preferences > Get Extensions**, open the menu in the
top-right, choose **Install from Disk**, and select
`dist/blenderlight-2.0.0.zip`.

Import through **File > Import > LightWave Object (.lwo)** or drag a supported
file into the 3D View.

## Development

The fixture corpus contains 83 LWOB, LWO2, and LWO3 objects. The validator
imports every fixture and checks Blender 5.2 geometry, materials, UVs, color
attributes, and custom normals.

```powershell
python -m flake8 io_scene_lwo scripts\validate_blender52.py

& "D:\Blender Foundation\Blender 5.2\blender.exe" `
  --background `
  --factory-startup `
  --python scripts\validate_blender52.py
```

The same validation runs in GitHub Actions on Windows and Linux.

## Project layout

- `io_scene_lwo/` - installable Blender extension
- `scripts/validate_blender52.py` - dependency-free regression validator
- `tests/` - active LightWave fixtures and referenced images
- `docs/` - format-handler research and coverage roadmap

## Current limitations

- LightWave scene (`.lws`) files are not imported.
- Arbitrary LWO3 node graphs, envelopes, procedural textures, gradients, and
  every third-party node are not yet translated.
- Non-UV planar, cylindrical, cubic, and spherical image projections are
  parsed but are not yet converted to Blender mapping nodes.

## Credits and license

BlenderLight is maintained by Kenneth Peters. It began with the
[nangtani/blender-import-lwo](https://github.com/nangtani/blender-import-lwo)
codebase and preserves its authorship in [NOTICE.md](NOTICE.md).

BlenderLight is distributed under the
[GNU General Public License v3.0 or later](LICENSE). The upstream MIT notice is
preserved in [LICENSES/MIT.txt](LICENSES/MIT.txt).

Please report reproducible gaps with a small redistributable fixture in the
[issue tracker](https://github.com/Tzeentchnet/BlenderLight/issues).
