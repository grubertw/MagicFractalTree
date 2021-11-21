# Blender add-on for creating a Magic Fractal Tree
Python script which can be installed as a Blender add-on for creating a tree with a set number of segments (i.e. edges), branching with a set probility (default is 50%) with a reduced number of segments (and segment length), and recursing until the number of segments is one. Once installed, the script is accessable as a button in the 3D viewport (Add > Mesh > Magic Fractal Tree). 

## Install instructions
1. Ensure you are using Blender 2.8.0 or greater
	1. Blender can be downloaded from here: [Blender](https://www.blender.org/download)
2. To install an add-on, go to Edit > Preferences > Add-ons
	1. Click "Install..." button
	2. Use Blender's file explorer to navigate to where the python script is on disk (where you cloned this git repo)
	3. Row should appear with an empty check-box for enabling "Add Mesh: Magic Fractal Tree"
	4. Enable the Add-on

## Usage
From the 3D Viewport, ensure 'Object Mode' is selected in the drop-down. Click 'Add', mouse over to 'Mesh', then mouse down to 'Add Magic Fractal Tree'. Give Blender some time, and it should create a randomly generated tree. An object called 'MagicFractalTree' should appear in your scene collection and remains selected. Before you de-select the object, take note of the UI box that appears at the bottom-left of the 3D Viewport. If you de-select the tree, this UI box dissapears. Open the box to play around with the settings. Note that any change to these settings will cause a new tree to be generated (overwriting the origional tree object).

### Branch Count
Starting number of segments (i.e. edges) used for the 'root' branch. Recursive iterations reduce this number by half for each new branch that is created - extruded from the verticies of the root (current) branch. Recursion stops when the branch count is reduced to one.

### Bend Range
Random rotation used for determining the direction a new vertex will be extruded as the branch is being created. The first direction the tree chosses to go is completely random (from world origin). Subsequent directions are then calculated as deltas from this first direction (plus/minus the Bend Range).

### Branch Split Probablity
Chance a new branch will be extruded from a vertex of the current branch. This is a float value between [0.0 - 1.0], where 0.0 creates no branches and 1.0 creates a branch at every vertex

### Initial Branch Radius
This plug-in uses the skin modifier to give the illusion of thickness to the branches. Thickness of the branches can be controlled with this parameter

### Reduce Branch Radius
For every new branch off the root branch, reduce the branch radius (thickness) by half. NOTE: This operation is extreemly time intensive because it is using UI operations. It is the author's hope that a new way can be found to do this by using data within the bmesh before mesh data is created. It is not reccomented to increase Branch Count beyond 20 when this feature is enabled. 
