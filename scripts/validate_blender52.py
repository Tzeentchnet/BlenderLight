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


def main():
    io_scene_lwo.register()
    failures = []
    imported = 0

    try:
        for path in fixture_files():
            clear_scene()
            bpy.types.Scene.ch.cancel_search = True
            try:
                result = bpy.ops.import_scene.lwo(filepath=str(path))
                if result != {"FINISHED"}:
                    raise RuntimeError(f"operator returned {result}")
                if not any(obj.type == "MESH" for obj in bpy.data.objects):
                    raise RuntimeError("no mesh object was created")
                imported += 1
                print(f"PASS {path.relative_to(ROOT)}")
            except Exception as error:
                failures.append((path, error))
                print(f"FAIL {path.relative_to(ROOT)}: {error}")
    finally:
        clear_scene()
        io_scene_lwo.unregister()

    print(f"Validated {imported} files; {len(failures)} failures")
    if failures:
        summary = "\n".join(
            f"{path.relative_to(ROOT)}: {error}" for path, error in failures
        )
        raise RuntimeError(f"BlenderLight fixture validation failed:\n{summary}")


if __name__ == "__main__":
    main()
