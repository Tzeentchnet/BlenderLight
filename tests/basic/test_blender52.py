import os

import bpy
import pytest


def import_lwo(relative_path):
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.lwo(filepath=os.path.abspath(relative_path))
    assert result == {"FINISHED"}
    return [obj for obj in bpy.data.objects if obj not in before]


@pytest.fixture(autouse=True)
def reset_import_state():
    bpy.types.Scene.ch.search_paths = []
    bpy.types.Scene.ch.cancel_search = False
    bpy.types.Scene.ch.recursive = True
    yield
    for obj in list(bpy.data.objects):
        if obj.name != "Cube":
            bpy.data.objects.remove(obj, do_unlink=True)


def test_lwo3_geometry_and_materials():
    objects = import_lwo("tests/basic/src/LWO3/box/box1.lwo")
    mesh_object = next(obj for obj in objects if obj.type == "MESH")

    assert len(mesh_object.data.vertices) == 8
    assert len(mesh_object.data.polygons) == 6
    assert len(mesh_object.data.materials) == 6


def test_lwo3_uv_texture_nodes():
    objects = import_lwo("tests/basic/src/LWO3/box/box1-uv.lwo")
    mesh_object = next(obj for obj in objects if obj.type == "MESH")

    assert "Texture" in mesh_object.data.uv_layers
    image_nodes = [
        node
        for material in mesh_object.data.materials
        for node in material.node_tree.nodes
        if node.bl_idname == "ShaderNodeTexImage"
    ]
    assert image_nodes
    assert any(node.outputs["Color"].is_linked for node in image_nodes)


def test_blender52_color_attributes():
    objects = import_lwo("tests/assimp/src/LWO/LWO2/box_2vc_1unused.lwo")
    mesh_object = next(obj for obj in objects if obj.type == "MESH")

    assert mesh_object.data.color_attributes["Vertex Color 0"].domain == "CORNER"
    assert (
        mesh_object.data.color_attributes["Vertex Color 0"].data_type
        == "FLOAT_COLOR"
    )


def test_blender52_custom_normals():
    objects = import_lwo(
        "tests/assimp/src/LWO/LWO2/ModoExport_vertNormals.lwo"
    )
    mesh_object = next(obj for obj in objects if obj.type == "MESH")

    assert mesh_object.data.has_custom_normals
