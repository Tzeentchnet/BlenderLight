from pathlib import Path
import sys

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import io_scene_lwo  # noqa: E402


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for collection in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
    ):
        for data_block in list(collection):
            if data_block.users == 0:
                collection.remove(data_block)


def fixture_files():
    roots = (
        ROOT / "tests" / "basic" / "src",
        ROOT / "tests" / "assimp" / "src",
        ROOT / "tests" / "lwo_interceptor" / "src",
    )
    return sorted(
        path
        for root in roots
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".lwo", ".lwo2", ".lwo3"}
    )


def import_fixture(relative_path):
    clear_scene()
    bpy.types.Scene.ch.search_paths = []
    bpy.types.Scene.ch.cancel_search = True
    bpy.types.Scene.ch.recursive = True

    path = ROOT / relative_path
    result = bpy.ops.import_scene.lwo(filepath=str(path))
    if result != {"FINISHED"}:
        raise RuntimeError(f"operator returned {result}")

    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("no mesh object was created")
    return mesh_objects


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_version():
    require(
        io_scene_lwo.bl_info["version"] == (2, 0, 0),
        f"unexpected add-on version {io_scene_lwo.bl_info['version']}",
    )


def validate_lwo3_geometry():
    mesh = import_fixture("tests/basic/src/LWO3/box/box1.lwo")[0].data
    require(len(mesh.vertices) == 8, "LWO3 box should have 8 vertices")
    require(len(mesh.polygons) == 6, "LWO3 box should have 6 polygons")
    require(len(mesh.materials) == 6, "LWO3 box should have 6 materials")


def validate_lwo3_uv_texture():
    mesh = import_fixture("tests/basic/src/LWO3/box/box1-uv.lwo")[0].data
    require("Texture" in mesh.uv_layers, "LWO3 Texture UV map is missing")
    image_nodes = [
        node
        for material in mesh.materials
        for node in material.node_tree.nodes
        if node.bl_idname == "ShaderNodeTexImage"
    ]
    require(image_nodes, "LWO3 image texture node is missing")
    require(
        any(node.outputs["Color"].is_linked for node in image_nodes),
        "LWO3 image texture is not connected to a material",
    )


def validate_color_attributes():
    mesh = import_fixture(
        "tests/assimp/src/LWO/LWO2/box_2vc_1unused.lwo"
    )[0].data
    attribute = mesh.color_attributes.get("Vertex Color 0")
    require(attribute is not None, "Vertex Color 0 attribute is missing")
    require(attribute.domain == "CORNER", "vertex color domain should be CORNER")
    require(
        attribute.data_type == "FLOAT_COLOR",
        "vertex color type should be FLOAT_COLOR",
    )


def validate_custom_normals():
    mesh = import_fixture(
        "tests/assimp/src/LWO/LWO2/ModoExport_vertNormals.lwo"
    )[0].data
    require(mesh.has_custom_normals, "custom vertex normals are missing")


def main():
    io_scene_lwo.register()
    failures = []
    imported = 0

    try:
        for path in fixture_files():
            try:
                import_fixture(path.relative_to(ROOT))
                imported += 1
                print(f"PASS {path.relative_to(ROOT)}")
            except Exception as error:
                failures.append((str(path.relative_to(ROOT)), error))
                print(f"FAIL {path.relative_to(ROOT)}: {error}")

        feature_checks = (
            ("add-on version", validate_version),
            ("LWO3 geometry and materials", validate_lwo3_geometry),
            ("LWO3 UV texture nodes", validate_lwo3_uv_texture),
            ("Blender 5.2 color attributes", validate_color_attributes),
            ("Blender 5.2 custom normals", validate_custom_normals),
        )
        for label, check in feature_checks:
            try:
                check()
                print(f"PASS {label}")
            except Exception as error:
                failures.append((label, error))
                print(f"FAIL {label}: {error}")
    finally:
        clear_scene()
        io_scene_lwo.unregister()

    print(
        f"Validated {imported} files and {len(feature_checks)} feature checks; "
        f"{len(failures)} failures"
    )
    if failures:
        summary = "\n".join(f"{label}: {error}" for label, error in failures)
        raise RuntimeError(f"BlenderLight fixture validation failed:\n{summary}")


if __name__ == "__main__":
    main()
