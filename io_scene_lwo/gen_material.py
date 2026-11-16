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

# Copyright (C) 2026 Kenneth Peters

import os
import bpy

class _material:
    __slots__ = (
        "name",
        "mat",
        "smooth",
    )

    def __init__(self, name=None):
        self.name = name
        self.mat = None
        self.smooth = False


def get_existing(surf, use_existing_materials):
    m = None
    if not use_existing_materials:
        return m
    x = bpy.data.materials.get(surf.name)
    if not x is None:
        m = _material(surf.name)
        m.mat = x
        m.smooth = surf.smooth
    return m


def _clamp(value):
    return max(0.0, min(1.0, value))


def _set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def lwo2cycles(surf_data):
    m = _material(surf_data.name)
    mat_name = surf_data.name

    m.smooth = surf_data.smooth
    m.mat = bpy.data.materials.new(mat_name)
    nodes = m.mat.node_tree.nodes
    links = m.mat.node_tree.links

    alpha = 1.0 - _clamp(surf_data.tran)
    color = (*surf_data.colr, alpha)
    m.mat.diffuse_color = color

    principled = nodes.get("Principled BSDF")
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        output = nodes.get("Material Output") or nodes.new("ShaderNodeOutputMaterial")
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    roughness = surf_data.rough
    if roughness is None:
        roughness = 1.0 - surf_data.glos

    _set_input(principled, "Base Color", (*surf_data.colr, 1.0))
    _set_input(principled, "Metallic", _clamp(surf_data.metal))
    _set_input(principled, "Roughness", _clamp(roughness))
    _set_input(principled, "IOR", max(1.0, surf_data.rind))
    _set_input(principled, "Alpha", alpha)
    _set_input(principled, "Diffuse Roughness", _clamp(1.0 - surf_data.diff))
    _set_input(principled, "Specular IOR Level", _clamp(surf_data.spec))
    _set_input(principled, "Transmission Weight", _clamp(surf_data.tran))
    _set_input(principled, "Coat Weight", _clamp(surf_data.refl))
    _set_input(principled, "Coat Roughness", _clamp(surf_data.rblr))
    _set_input(principled, "Emission Color", (*surf_data.colr, 1.0))
    _set_input(principled, "Emission Strength", max(0.0, surf_data.lumi))

    if alpha < 1.0:
        m.mat.surface_render_method = "DITHERED"

    for textures_type, textures in surf_data.textures.items():
        for texture in textures:
            if not texture.enab:
                continue

            image_path = texture.image
            if image_path is None:
                continue

            image = bpy.data.images.load(image_path, check_existing=True)
            image_node = nodes.new("ShaderNodeTexImage")
            image_node.image = image
            image_node.label = f"{textures_type}: {os.path.basename(image_path)}"

            if texture.uvname:
                uv_node = nodes.new("ShaderNodeUVMap")
                uv_node.uv_map = texture.uvname
                links.new(uv_node.outputs["UV"], image_node.inputs["Vector"])

            color_output = image_node.outputs["Color"]
            if texture.nega:
                invert_node = nodes.new("ShaderNodeInvert")
                links.new(color_output, invert_node.inputs["Color"])
                color_output = invert_node.outputs["Color"]

            target_name = {
                "COLR": "Base Color",
                "LUMI": "Emission Color",
                "DIFF": "Diffuse Roughness",
                "SPEC": "Specular IOR Level",
                "REFL": "Coat Weight",
                "TRAN": "Transmission Weight",
            }.get(textures_type)
            if target_name is not None and principled.inputs.get(target_name) is not None:
                if textures_type != "COLR":
                    image.colorspace_settings.name = "Non-Color"
                links.new(color_output, principled.inputs[target_name])

            if textures_type == "COLR":
                links.new(image_node.outputs["Alpha"], principled.inputs["Alpha"])
            elif textures_type == "BUMP":
                image.colorspace_settings.name = "Non-Color"
                bump_node = nodes.new("ShaderNodeBump")
                bump_node.inputs["Strength"].default_value = _clamp(surf_data.bump)
                links.new(color_output, bump_node.inputs["Height"])
                links.new(bump_node.outputs["Normal"], principled.inputs["Normal"])

    return m
