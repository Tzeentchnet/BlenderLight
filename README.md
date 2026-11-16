[![Blender 5.2 tests](https://github.com/Tzeentchnet/BlenderLight/actions/workflows/test_io_scene_lwo.yml/badge.svg)](https://github.com/Tzeentchnet/BlenderLight/actions/workflows/test_io_scene_lwo.yml)

# BlenderLight

BlenderLight is a Blender 5.2 extension for importing LightWave object files.
It is a fork of
[nangtani/blender-import-lwo](https://github.com/nangtani/blender-import-lwo)
and retains the original importer authorship and history.

## Requirements

- Blender 5.2 LTS or newer
- No external Python packages: Blender's bundled NumPy is used for bulk mesh,
  UV, color, normal, shape-key, and crease data transfer

## Supported formats and data

- LightWave 4/5 `LWOB` and layered `LWLO`
- LightWave 6+ `LWO2`
- LightWave 2018+ `LWO3`
- Multi-layer meshes and layer parenting
- Faces, subpatches, Catmull-Clark subdivision, and native Blender n-gons
- Surface assignments and core surface parameters
- LWO3 standard-node values and color image references
- Point and discontinuous UV maps
- RGB/RGBA color attributes
- Weight maps, relative/absolute morphs, edge creases, and custom normals
- Skelegon-to-armature conversion
- Blender 5.2 extension packaging and file drag-and-drop

See [LightWave handler research](docs/lightwave-handler-research.md) for the
reference implementations reviewed and the next coverage targets.

## Install

Build the extension package with Blender 5.2:

```powershell
& "D:\Blender Foundation\Blender 5.2\blender.exe" `
  --command extension build `
  --source-dir io_scene_lwo `
  --output-dir dist
```

In Blender, open **Edit > Preferences > Get Extensions**, use the menu in the
top-right, choose **Install from Disk**, and select the generated
`blenderlight-2.0.0.zip`.

After installation, use **File > Import > LightWave Object (.lwo)** or drag an
`.lwo`, `.lwo2`, or `.lwo3` file into the 3D View.

## Development and tests

The checked-in fixture corpus covers LWOB, LWO2, and LWO3 objects. Run the
dependency-free Blender validation suite with Blender 5.2:

```powershell
& "D:\Blender Foundation\Blender 5.2\blender.exe" `
  --background `
  --factory-startup `
  --python scripts\validate_blender52.py
```

The suite imports every fixture and checks LWO3 materials and UV textures,
Blender 5.2 color attributes, and custom normals. CI runs it on Blender 5.2
for Windows and Linux.

## Current limitations

- LightWave scene (`.lws`) files are not imported.
- LWO3 geometry, core standard materials, UVs, and color textures are
  supported; arbitrary node graphs, envelopes, procedural textures, gradients,
  and every third-party node are not yet translated.
- Non-UV planar, cylindrical, cubic, and spherical image projections are
  parsed but are not yet converted to Blender mapping nodes.

Please report reproducible gaps with a small redistributable fixture in the
[issue tracker](https://github.com/Tzeentchnet/BlenderLight/issues).
