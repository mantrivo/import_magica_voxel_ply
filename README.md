# Magica Voxel .ply Importer Addon for Blender

[Download](https://github.com/mantrivo/import_magica_voxel_ply/raw/main/io_import_magica_ply.py)


Rightclick > Save As to download the addon

- Imports a .ply File form Magica Voxel to Blender via the .ply Addon
- Generates UV Map (Cube Project, Pack Islands)
- Generates Material for Baking
- Generates a Texture with Cycles Baking
- Optimizes Geometry (Limited Dissolve, Triangulate via Modifiers or Operators)

**Important:** Importing Geometry with many small faces will not work as the
Pack Islands Operator in Blender will take really long. (eg dont ty to load
the meneger example of magica Voxel (1/4 of meneger takes >15min, the whole
likely more than 2h), the monu examples work fine (~10s))
