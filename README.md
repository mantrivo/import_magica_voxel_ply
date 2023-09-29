# Magica Voxel .ply Importer Addon for Blender

[Download for Blender 3.5 and above](https://github.com/mantrivo/import_magica_voxel_ply/raw/main/io_import_magica_ply.py)
[Download for Blender 3.4 and below](https://raw.githubusercontent.com/mantrivo/import_magica_voxel_ply/4afaf9619c9e899d23d5470b0ac4b04c77366b3c/io_import_magica_ply.py)

Rightclick > Save As to download the addon

- Imports a .ply File form Magica Voxel to Blender via the .ply Addon
- Generates UV Map (Cube Project, Pack Islands)
- Generates Material for Baking
- Generates a Texture with Cycles Baking
- Optimizes Geometry (Limited Dissolve, Triangulate via Modifiers or Operators)

**Important:** Importing Geometry with many isolated planar sections will not work with Blender 3.4 as the
Pack Islands Operator in Blender will take really long. (eg dont try to load
the meneger example of magica Voxel (1/4 of meneger takes >15min, the whole
likely more than 2h), the monu examples work fine (~10s))
This Issue is resolved, as the Pack Islands Operator is geatly speed up recently.
