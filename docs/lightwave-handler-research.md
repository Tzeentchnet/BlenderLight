# LightWave handler research

Research date: 2026-11-16.

This survey is used to prioritize BlenderLight format coverage. External
implementations are treated as behavioral references only. No source code from
K3D, Assimp, Three.js, or the other projects listed below is vendored into the
add-on.

## Primary format references

| Reference | Coverage and useful details | License/status |
|---|---|---|
| [LightWave SDK file formats](https://docs.lightwave3d.com/2025/sdk-file-formats.html) and [object format overview](https://docs.lightwave3d.com/2026/lightwave-object-format.html) | Authoritative EA-IFF basis, LWO2 specification, and LWO3's 32-bit nested `FORM` structure | Official documentation |
| [Three.js LWOLoader](https://github.com/mrdoob/three.js/tree/dev/examples/jsm/loaders/lwo) | Separate LWO2/LWO3 parsers; nested forms, layers, UVs, morphs, clips, LWO3 node entries, and material conversion | MIT; loader deprecated since Three.js r185 but parser remains a valuable reference |
| [Assimp LWO importer](https://github.com/assimp/assimp/tree/master/code/AssetLib/LWO) | Mature LWOB/LWO2 loader with LWO3 surface, clip, envelope, and nodal entry points; extensive public LWO fixture corpus | BSD 3-Clause-style Assimp license |
| [K3D LightWave Object Viewer](https://www.kevs3d.co.uk/k3d2.html) | LightWave 4/5 and 6/7/8 multi-layer objects, core surface parameters, smoothing, and subpatch tessellation | LGPL-2.1; C# source released in 2005, predates LWO3 |
| [LightWaveObjectViewer](https://github.com/laubryan/LightWaveObjectViewer) | Direct3D viewer with preliminary LWO3 support and a compact modern C++ parser | MIT |

## Additional parsers and writers

| Project | Relevance | License |
|---|---|---|
| [LogicalError/LWO-library](https://github.com/LogicalError/LWO-library) | Small C# LWO loader useful for cross-checking basic chunk boundaries | MIT |
| [ipr/Lightwave-object-loader](https://github.com/ipr/Lightwave-object-loader) | C++ LWO2 parser with older LWOB handling | MIT-style |
| [D-Lwo2Writer](https://github.com/shulc/D-Lwo2Writer) | Current clean-room LWO2 writer covering points, polygons, subpatches, surfaces, and surface tags; useful for round-trip fixtures | MIT |
| [nangtani/lwo_strut](https://github.com/nangtani/lwo_strut) | Standalone Python extraction of the historical Blender parser | GPL-3.0 |

## Findings applied in BlenderLight 2.0

1. LWO3 retains LWO2-compatible top-level geometry chunks (`LAYR`, `PNTS`,
   `POLS`, `TAGS`, `PTAG`, `VMAP`, and `VMAD`).
2. LWO3 moves clips and surfaces into 32-bit nested `FORM CLIP` and
   `FORM SURF` blocks.
3. Standard LWO3 material values are stored as named `FORM ENTR` values inside
   the surface node data. BlenderLight maps core color, diffuse, luminosity,
   specular, glossiness/roughness, reflection, transparency, refraction,
   translucency, metallic, and bump values.
4. LWO3 image-map entries still expose clip IDs and UV-map names, so the
   importer can connect resolved images to Blender's Principled BSDF.
5. Blender 5.2's attribute API and bundled NumPy allow topology and corner data
   to be transferred in bulk without legacy `MeshEdge.crease` or per-element
   assignment.

## Coverage priorities

1. Translate arbitrary LWO3 node connections, starting with Standard Surface,
   Image, Bump, Normal, Mix, and Math nodes.
2. Convert planar, cylindrical, spherical, and cubic projections into Blender
   mapping nodes.
3. Add LWO3 envelopes, gradients, and procedural-texture fallbacks.
4. Extend polygon-tag handling for parts and selection sets.
5. Evaluate LightWave scene (`.lws`) import separately from object import.
6. Add an LWO2 writer and round-trip fixtures, using only compatible,
   independently implemented behavior.
