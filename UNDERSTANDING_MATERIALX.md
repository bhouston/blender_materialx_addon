A materialx file consists of the following:

```xml
<materialx>
  <surface_shader name="SR_default" type="surfaceshader">
  </surface_shader>
 <surfacematerial name="sdfsdfdsf" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="SR_default">
 </surfacematerial>
</materialx>
```

The glTF procedural material supports only "gltf_PBR" or "unlit" surfaceshader.  Or at least the converter here only supports those two types:

https://github.khronos.org/glTF-MaterialX-Converter/


So these "surfaceshaders" have their own mtlx files that define their nodes.

There is a "gltf_pbr" and a "standard_surface".  I would likely need a "blender_principled_v2" or something for my Blender import/export tool.

And it could then be mapped to a number of different underlying surfaces, like gltf_pbr or standard_surface?