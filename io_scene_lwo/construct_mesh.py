# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import mathutils
import numpy as np
from .gen_material import lwo2cycles, get_existing


def _create_mesh(name, points, polygons):
    coordinates = np.asarray(points, dtype=np.float32)
    if coordinates.size == 0:
        coordinates = coordinates.reshape((0, 3))
    if coordinates.ndim != 2 or coordinates.shape[1] != 3:
        raise ValueError(f"Layer {name!r} has invalid point data")

    face_data = [
        (polygon_id, polygon)
        for polygon_id, polygon in enumerate(polygons)
        if len(polygon) >= 3
    ]
    loose_edges = [polygon for polygon in polygons if len(polygon) == 2]
    polygon_remap = {
        polygon_id: face_id
        for face_id, (polygon_id, _) in enumerate(face_data)
    }

    polygon_sizes = np.fromiter(
        (len(polygon) for _, polygon in face_data),
        dtype=np.int32,
        count=len(face_data),
    )

    loop_count = int(polygon_sizes.sum())
    loop_vertices = np.fromiter(
        (vertex for _, polygon in face_data for vertex in polygon),
        dtype=np.int32,
        count=loop_count,
    )
    loose_edge_vertices = np.asarray(loose_edges, dtype=np.int32).reshape((-1, 2))
    referenced_vertices = np.concatenate(
        (loop_vertices, loose_edge_vertices.ravel())
    )
    if referenced_vertices.size and (
        int(referenced_vertices.min()) < 0
        or int(referenced_vertices.max()) >= len(coordinates)
    ):
        raise ValueError(f"Layer {name!r} contains an out-of-range point index")

    loop_starts = np.zeros(len(face_data), dtype=np.int32)
    if len(face_data) > 1:
        np.cumsum(polygon_sizes[:-1], out=loop_starts[1:])

    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(coordinates))
    mesh.edges.add(len(loose_edge_vertices))
    mesh.loops.add(loop_count)
    mesh.polygons.add(len(face_data))
    mesh.vertices.foreach_set("co", coordinates.ravel())
    if len(loose_edge_vertices):
        mesh.edges.foreach_set("vertices", loose_edge_vertices.ravel())
    mesh.loops.foreach_set("vertex_index", loop_vertices)
    mesh.polygons.foreach_set("loop_start", loop_starts)
    mesh.polygons.foreach_set("loop_total", polygon_sizes)
    mesh.update(calc_edges=True, calc_edges_loose=True)

    return (
        mesh,
        coordinates,
        loop_vertices,
        loop_starts,
        polygon_sizes,
        polygon_remap,
    )


def _set_materials(mesh, layer_data, lwo, polygon_remap):
    material_indices = np.zeros(len(mesh.polygons), dtype=np.int32)
    smooth_faces = np.zeros(len(mesh.polygons), dtype=np.bool_)
    material_slot = 0

    for tag_index, polygon_indices in layer_data.surf_tags.items():
        if tag_index >= len(lwo.tags):
            raise ValueError(f"Surface tag index {tag_index} is out of range")
        material = lwo.materials.get(lwo.tags[tag_index])
        if material is None:
            continue

        mesh.materials.append(material.mat)
        face_indices = np.asarray(
            [
                polygon_remap[polygon_id]
                for polygon_id in polygon_indices
                if polygon_id in polygon_remap
            ],
            dtype=np.int32,
        )
        material_indices[face_indices] = material_slot
        smooth_faces[face_indices] = material.smooth
        material_slot += 1

    if len(mesh.polygons):
        mesh.polygons.foreach_set("material_index", material_indices)
        mesh.polygons.foreach_set("use_smooth", smooth_faces)


def _set_shape_keys(ob, layer_data, coordinates):
    if not layer_data.morphs:
        return

    print(f"Adding {len(layer_data.morphs)} Shapes Keys")
    ob.shape_key_add(name="Basis")
    for morph_name, morph_data in layer_data.morphs.items():
        shape_key = ob.shape_key_add(name=morph_name)
        shape_coordinates = coordinates.copy()
        for point_id, x, y, z in morph_data:
            if point_id < 0 or point_id >= len(shape_coordinates):
                raise ValueError(f"Morph {morph_name!r} references point {point_id}")
            shape_coordinates[point_id] = (x, y, z)
        shape_key.data.foreach_set("co", shape_coordinates.ravel())


def _to_rgba(value):
    color = np.ones(4, dtype=np.float32)
    components = np.asarray(value, dtype=np.float32)
    color[: min(4, len(components))] = components[:4]
    return color


def _set_color_attributes(
    mesh,
    layer_data,
    loop_vertices,
    loop_starts,
    polygon_sizes,
    polygon_remap,
):
    if not layer_data.colmaps:
        return

    print(f"Adding {len(layer_data.colmaps)} Color Attributes")
    for map_name, map_data in layer_data.colmaps.items():
        point_colors = np.ones((len(mesh.vertices), 4), dtype=np.float32)
        for point_id, color in map_data.get("PointMap", {}).items():
            if point_id < 0 or point_id >= len(point_colors):
                raise ValueError(f"Color map {map_name!r} references point {point_id}")
            point_colors[point_id] = _to_rgba(color)
        loop_colors = point_colors[loop_vertices].copy()

        for source_polygon_id, face_colors in map_data.get("FaceMap", {}).items():
            polygon_id = polygon_remap.get(source_polygon_id)
            if polygon_id is None:
                continue
            start = int(loop_starts[polygon_id])
            end = start + int(polygon_sizes[polygon_id])
            for loop_index in range(start, end):
                color = face_colors.get(int(loop_vertices[loop_index]))
                if color is not None:
                    loop_colors[loop_index] = _to_rgba(color)

        color_attribute = mesh.color_attributes.new(
            name=map_name,
            type="FLOAT_COLOR",
            domain="CORNER",
        )
        color_attribute.data.foreach_set("color", loop_colors.ravel())


def _set_uv_layers(
    mesh,
    layer_data,
    loop_vertices,
    loop_starts,
    polygon_sizes,
    polygon_remap,
):
    map_names = sorted(
        set(layer_data.uvmaps_vmap).union(layer_data.uvmaps_vmad)
    )
    if not map_names:
        return

    print(f"Adding {len(map_names)} UV Maps")
    for map_name in map_names:
        point_uvs = np.zeros((len(mesh.vertices), 2), dtype=np.float32)
        point_map = layer_data.uvmaps_vmap.get(map_name, {}).get("PointMap", {})
        for point_id, uv in point_map.items():
            if point_id < 0 or point_id >= len(point_uvs):
                raise ValueError(f"UV map {map_name!r} references point {point_id}")
            point_uvs[point_id] = uv
        loop_uvs = point_uvs[loop_vertices].copy()

        face_map = layer_data.uvmaps_vmad.get(map_name, {}).get("FaceMap", {})
        for source_polygon_id, face_uvs in face_map.items():
            polygon_id = polygon_remap.get(source_polygon_id)
            if polygon_id is None:
                continue
            start = int(loop_starts[polygon_id])
            end = start + int(polygon_sizes[polygon_id])
            for loop_index in range(start, end):
                uv = face_uvs.get(int(loop_vertices[loop_index]))
                if uv is not None:
                    loop_uvs[loop_index] = uv

        uv_layer = mesh.uv_layers.new(name=map_name)
        uv_layer.uv.foreach_set("vector", loop_uvs.ravel())


def _normalize(vectors):
    lengths = np.linalg.norm(vectors, axis=1)
    nonzero = lengths > 0.0
    vectors[nonzero] /= lengths[nonzero, np.newaxis]
    return vectors


def _set_custom_normals(
    mesh,
    layer_data,
    loop_vertices,
    loop_starts,
    polygon_sizes,
    polygon_remap,
):
    if not layer_data.vnorms and not layer_data.lnorms:
        return

    print("Adding Custom Normals")
    vertex_normals = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get("normal", vertex_normals.ravel())
    for point_id, normal in layer_data.vnorms.items():
        if point_id < 0 or point_id >= len(vertex_normals):
            raise ValueError(f"Normal map references point {point_id}")
        vertex_normals[point_id] = normal
    _normalize(vertex_normals)

    if not layer_data.lnorms:
        mesh.normals_split_custom_set_from_vertices(vertex_normals.tolist())
        return

    loop_normals = vertex_normals[loop_vertices].copy()
    for source_polygon_id, normals in layer_data.lnorms.items():
        polygon_id = polygon_remap.get(source_polygon_id)
        if polygon_id is None:
            continue
        start = int(loop_starts[polygon_id])
        end = start + int(polygon_sizes[polygon_id])
        polygon_loops = {
            int(loop_vertices[loop_index]): loop_index
            for loop_index in range(start, end)
        }
        for point_id, x, y, z in normals:
            loop_index = polygon_loops.get(point_id)
            if loop_index is not None:
                loop_normals[loop_index] = (x, y, z)
    mesh.normals_split_custom_set(_normalize(loop_normals).tolist())


def _set_edge_creases(mesh, edge_weights):
    if not edge_weights:
        return

    edge_lookup = {
        tuple(sorted((edge.vertices[0], edge.vertices[1]))): edge.index
        for edge in mesh.edges
    }
    crease_values = np.zeros(len(mesh.edges), dtype=np.float32)
    for edge_key, weight in edge_weights.items():
        first, second = (int(value) for value in edge_key.split())
        edge_index = edge_lookup.get(tuple(sorted((first, second))))
        if edge_index is not None:
            crease_values[edge_index] = max(0.0, min(1.0, weight))

    crease_attribute = mesh.attributes.get("crease_edge")
    if crease_attribute is None:
        crease_attribute = mesh.attributes.new(
            name="crease_edge",
            type="FLOAT",
            domain="EDGE",
        )
    crease_attribute.data.foreach_set("value", crease_values)


def build_armature(layer_data, bones):
    """Build an armature from the skelegon data in the mesh."""
    print("Building Armature")

    # New Armatures include a default bone, remove it.
    bones.remove(bones[0])

    # Now start adding the bones at the point locations.
    prev_bone = None
    for skb_idx in range(len(layer_data.bones)):
        if skb_idx in layer_data.bone_names:
            nb = bones.new(layer_data.bone_names[skb_idx])
        else:
            nb = bones.new("Bone")

        nb.head = layer_data.pnts[layer_data.bones[skb_idx][0]]
        nb.tail = layer_data.pnts[layer_data.bones[skb_idx][1]]

        if skb_idx in layer_data.bone_rolls:
            xyz = layer_data.bone_rolls[skb_idx].split(" ")
            vec = mathutils.Vector((float(xyz[0]), float(xyz[1]), float(xyz[2])))
            quat = vec.to_track_quat("Y", "Z")
            nb.roll = max(quat.to_euler("YZX"))
            if nb.roll == 0.0:
                nb.roll = min(quat.to_euler("YZX")) * -1
            # YZX order seems to produce the correct roll value.
        else:
            nb.roll = 0.0

        if prev_bone is not None:
            if nb.head == prev_bone.tail:
                nb.parent = prev_bone

        nb.use_connect = True
        prev_bone = nb


def build_materials(lwo, ch):
    print(f"Adding {len(lwo.surfs)} Materials")

    # renderer = bpy.context.scene.render.engine
    for key, surf in lwo.surfs.items():
        m = get_existing(surf, ch.use_existing_materials)
        if m is None:
            m = lwo2cycles(surf)
        lwo.materials[key] = m


def build_objects(lwo, ch):
    """Using the gathered data, create the objects."""
    ob_dict = {}  # Used for the parenting setup.

    build_materials(lwo, ch)

    # Single layer objects use the object file's name instead.
    if len(lwo.layers) and lwo.layers[-1].name == "Layer 1":
        lwo.layers[-1].name = lwo.name
        print(f"Building '{lwo.name}' Object")
    else:
        print(f"Building {len(lwo.layers)} Objects")

    # Before adding any meshes or armatures go into Object mode.
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")

    for layer_data in lwo.layers:
        (
            me,
            coordinates,
            loop_vertices,
            loop_starts,
            polygon_sizes,
            polygon_remap,
        ) = _create_mesh(layer_data.name, layer_data.pnts, layer_data.pols)

        ob = bpy.data.objects.new(layer_data.name, me)

        scn = bpy.context.collection
        scn.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(state=True)

        ob_dict[layer_data.index] = [ob, layer_data.parent_index]

        # Move the object so the pivot is in the right place.
        ob.location = layer_data.pivot

        _set_materials(me, layer_data, lwo, polygon_remap)

        # Create the Vertex Groups (LW's Weight Maps).
        if len(layer_data.wmaps) > 0:
            print(f"Adding {len(layer_data.wmaps)} Vertex Groups")
            for wmap_key in layer_data.wmaps:
                vgroup = ob.vertex_groups.new()
                vgroup.name = wmap_key
                wlist = layer_data.wmaps[wmap_key]
                for pvp in wlist:
                    if pvp[0] < 0 or pvp[0] >= len(me.vertices):
                        raise ValueError(
                            f"Weight map {wmap_key!r} references point {pvp[0]}"
                        )
                    vgroup.add((pvp[0],), pvp[1], "REPLACE")

        _set_shape_keys(ob, layer_data, coordinates)
        _set_color_attributes(
            me,
            layer_data,
            loop_vertices,
            loop_starts,
            polygon_sizes,
            polygon_remap,
        )
        _set_uv_layers(
            me,
            layer_data,
            loop_vertices,
            loop_starts,
            polygon_sizes,
            polygon_remap,
        )
        _set_edge_creases(me, layer_data.edge_weights)
        _set_custom_normals(
            me,
            layer_data,
            loop_vertices,
            loop_starts,
            polygon_sizes,
            polygon_remap,
        )
        print(f"{int(np.count_nonzero(polygon_sizes > 4))} native NGONs")
        me.update()

        # Unfortunately we can't exlude certain faces from the subdivision.
        if layer_data.has_subds and ch.add_subd_mod:
            ob.modifiers.new(name="Subsurf", type="SUBSURF")

        # Should we build an armature from the embedded rig?
        if len(layer_data.bones) > 0 and ch.skel_to_arm:
            bpy.ops.object.armature_add()
            arm_object = bpy.context.active_object
            arm_object.name = "ARM_" + layer_data.name
            arm_object.data.name = arm_object.name
            arm_object.location = layer_data.pivot
            bpy.ops.object.mode_set(mode="EDIT")
            build_armature(layer_data, arm_object.data.edit_bones)
            bpy.ops.object.mode_set(mode="OBJECT")

        # Clear out the dictionaries for this layer.
        layer_data.bone_names.clear()
        layer_data.bone_rolls.clear()
        layer_data.wmaps.clear()
        layer_data.colmaps.clear()
        layer_data.uvmaps_vmad.clear()
        layer_data.uvmaps_vmap.clear()
        layer_data.morphs.clear()
        layer_data.surf_tags.clear()

        print("done!")

    # With the objects made, setup the parents and re-adjust the locations.
    if len(ob_dict.keys()) > 1:
        empty = bpy.data.objects.new(name=lwo.name + "_empty", object_data=None)

        bpy.context.collection.objects.link(empty)

    for ob_key in ob_dict:
        if ob_dict[ob_key][1] != -1 and ob_dict[ob_key][1] in ob_dict:
            parent_ob = ob_dict[ob_dict[ob_key][1]]
            ob_dict[ob_key][0].parent = parent_ob[0]
            ob_dict[ob_key][0].location -= parent_ob[0].location
        elif len(ob_dict.keys()) > 1:
            ob_dict[ob_key][0].parent = empty

    bpy.context.view_layer.update()

    print("Done Importing LWO File")
