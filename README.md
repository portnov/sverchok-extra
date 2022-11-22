README
======

```
   _____                     __          __         ______     __            
  / ___/   _____  __________/ /_  ____  / /__      / ____/  __/ /__________ _
  \__ \ | / / _ \/ ___/ ___/ __ \/ __ \/ //_/_____/ __/ | |/_/ __/ ___/ __ `/
 ___/ / |/ /  __/ /  / /__/ / / / /_/ / ,< /_____/ /____>  </ /_/ /  / /_/ / 
/____/|___/\___/_/   \___/_/ /_/\____/_/|_|     /_____/_/|_|\__/_/   \__,_/
initialized.
```

This is an addon for [Blender][1], which was desined to extend he [Sverchok][2]
addon by features, that could not be included into Sverchok because it would
add new dependencies and make installation of Sverchok core too complicated for
most usages.

At the moment, all the most interesting and usable stuff is moved into Sverchok
addon itself. Sverchok-Extra still contains some nodes that can be interesting
in certain applications. Sverchok-Extra will continue to exist as a sandbox, or
a nursery, for new Sverchok nodes. If you have an idea for a node, which is too
complex to be a scripted node, but too young, or uses some new dependency, and
you doubt it will be useful in Sverchok core in it's current state — put it
into Sverchok-Extra.

**NOTE**: Sverchok-Extra contains nodes that are in early development stage; there are
many things that can change in future. So, please do not depend on this addon
in your production projects yet. But you can already test it and play with it.

The documentation is currently almost absent, partly because of amount of
changes that might occur at any time at this stage of development.

Features
--------

At the moment, this addon includes the following nodes for Sverchok:

* *Surface Extra* category:
  * Smooth Bivariate Spline (uses [SciPy][3])
  * Implicit Surface Solver / Wrap (no dependencies, experimental node)
  * Surface Curvature Lines (uses [SciPy][3])
* *Field Extra* category (please refer to the [wiki page][5] about used concept of the field):
  * Vector Field Lines on a Surface (uses SciPy)
* *Data* category:
  * Spreadsheet
  * Data Item
* *Matrix Extra* category:
  * Project Matrix on Plane
* *Solid Extra* category:
  * Solid Waffle
* *Spatial Extra* category:
  * Delanuay 3D on Surface
  * Delaunay Mesh - add vertices to existing mesh by use of Delaunay triangulation
* *SDF Primitives* category (uses [SDF][7]):
  * SDF Box
  * SDF Cylinder
  * ..and many more
* *SDF Operations* category (uses [SDF][7]):
  * SDF Translate
  * SDF Scale
  * SDF Rotate
  * SDF Orient
  * SDF General Transform
  * SDF Boolean
  * SDF Blend
  * SDF Linear Transition
  * SDF Radial Transition
  * SDF Dilate / Erode
  * SDF Shell
  * SDF Twist
  * SDF Linear Bend
  * SDF Slice
  * SDF Exrtude
  * SDF Extrude To
  * SDF Revolve
  * SDF Generate (specialized version of Marching Cubes)

There will be more.

Installation
------------

At the moment, Sverchok-Extra does not have any specific dependencies, except
for [Sverchok][2] and it's dependencies. Sverchok-Extra currently can use
SciPy, which can be installed as a dependency for Sverchok. Please refer to
[Sverchok documentation][6] about how to install dependencies.

After you installed all of dependencies you've decided to install, installation
of Sverchok-Extra by itself is simple:

* Download [Sverchok-Extra zip archive][4] from GitHub
* In Blender, go to User Preferences > Addons > install from file > choose
  zip-archive > activate flag beside Sverchok-Extra.
* Save preferences, if you want to enable the addon permanently.

LICENSE: GPL-3.

[1]: http://blender.org
[2]: https://github.com/nortikin/sverchok
[3]: https://scipy.org/
[4]: https://github.com/portnov/sverchok-extra/archive/master.zip
[5]: https://github.com/portnov/sverchok-extra/wiki/Fields
[6]: https://github.com/nortikin/sverchok/wiki/Dependencies
[7]: https://github.com/fogleman/sdf

