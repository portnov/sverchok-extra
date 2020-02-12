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

This is an addon for [Blender][1], which is meant to extend the [Sverchok][2]
addon by features, that could not be included into Sverchok because it would
add new dependencies and make installation of Sverchok core too complicated for
most usages.

**NOTE**: Sverchok-Extra is currently in early development stage; there are
many things that can change in future. So, please do not depend on this addon
in your production projects yet. But you can already test it and play with it.

The documentation is currently almost absent, partly because of amount of
changes that might occur at any time at this stage of development.

Features
--------

At the moment, this addon includes the following nodes for Sverchok:

* *Curve* category:
  * Straight line curve
  * Formula-defined curve
  * Interpolation Curve (cubic spline, uses numpy only)
  * Minimal (interpolation) Curve (uses [SciPy][4])
  * NURBS Curve (uses [Geomdl][3] library)
  * NURBS Interpolation Curve (uses Geomdl library)
  * NURBS Approximation Curve (uses Geomdl library)
  * Apply Vector Field to Curve
  * Evaluate Curve
  * Marching Squares (uses [Scikit-Image][5] library)
* *Surface* category:
  * Plane Surface
  * Formula-defined Surface
  * Smooth Bivariate Spline (uses [SciPy][4])
  * NURBS Surface (uses Geomdl)
  * NURBS Interpolation Surface (uses Geomdl)
  * NURBS Approximation Surface (uses Geomdl)
  * Quads to NURBS (uses Geomdl)
  * Minimal Surface (uses SciPy)
  * Curves to Surface (optionally uses SciPy and/or Geomdl)
  * Apply Vector Field to Surface
  * Evaluate Surface (universal node for NURBS / minimal surfaces)
  * Marching Cubes (uses either [PyMCubes][8] or [Scikit-Image][5])
* *Spatial* category:
  * Voronoi 3D (uses SciPy)
  * Spherical Voronoi (uses SciPy)
  * Scalar Field Random Probe
* *Field* category (please refer to the [wiki page][11] about used concept of the field; most of these nodes do not use external libraries, except for numpy):
  * Generate Scalar field by formula
  * Generate Vector field by formula
  * Compose Vector Field (from three Scalar fields)
  * Decompose Vector Field (into three Scalar fields)
  * Scalar field of a point
  * Attractor Field
  * Mesh Nearest Normals Field (optionally uses SciPy)
  * Merge Scalar Fields
  * Minimal Scalar Field (uses SciPy)
  * Minimal Vector Field (uses SciPy)
  * Voronoi 3D Scalar / Vector Field (uses Blender's mathutils only)
  * Bend along Surface (universal node for NURBS / minimal surfaces)
  * Bend along Curve (universal node for NURBS / interpolation curves)
  * Noise Vector Field
  * Scalar field math
  * Vector field math
  * Field differential operators (gradient, divergence, laplacian...)
  * Apply vector field
  * Evaluate vector field
  * Evaluate scalar field

There will be more.

Installation
------------

This addon depends on several libraries, and you have to install at least some
of them in order to use Sverchok-Extra. If you do not need all features, you
may install only one or two of libraries, but you have to install at least
something, otherwise Sverchok-Extra will just do nothing.

One thing you will have to install anyway if you want to use Sverchok-Extra is
[pip][6]. All libraries are installed with it.

### Install pip

This I tested on latest Blender 2.81 builds. The similar instructions should
work for other Blender 2.8x versions.

    $ /path/to/blender/2.xx/python/bin/python3 -m ensurepip
    $ /path/to/blender/2.xx/python/bin/python3 -m pip install --upgrade pip setuptools wheel

(exact name of `python` executable depends on specific blender build).

In some cases, it may appear that Blender's python already knows about your
system's installation of python (python is usually installed by default on most
Linux distros). In such cases, you may use just `pip install something` to
install libraries.

### Install SciPy

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U scipy

### Install SciKit-Image

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U scikit-image

### Install PyMCubes

This is more complex. First, you have to install [Cython][7]:

    $ /path/to/blender/2.xx/python/bin/python3 -m pip install Cython

Then you have to set up a build environment for Cython. You will need 1) to
install development files for Python (such as `Python.h` and others), and 2) to
explain Blender's python where to find them. **Note**: you have to have headers
for exactly the same version of Python that your Blender build is using.

On Debian/Ubuntu, you can install Python's development files by `apt-get
install libpython3.7-dev` for `python3.7m` used in Blender 2.80/2.81. On other
Linux distros, the command will be similar. On Windows or MacOS this can be
more tricky, I did not try.

You have to somehow tell Blender's built-in python where to look for headers.
I've found the simplest way is to do

    $ ln -s /usr/include/python3.7m/* /path/to/blender/2.xx/python/include

There may be more correct way, but I do not know it.

After that, you can install PyMCubes by

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U PyMCubes

### Install Geomdl

In the simplest case, you can install Geomdl by

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U geomdl

but this way you will get pure-python library, which is very slow. If you want
it fast, then you have to install Cython (see previous paragraph for
instruction). After you installed Cython, you can install "cythonized" geomdl
as it is described in [Geomdl instruction][9]:

    $ /path/to/blender/2.xx/python/bin/python3 -m pip install geomdl --install-option="--use-cython"

### Install Sverchok

I hope you've done it already. The instuction is in Sverchok's README.
Basically, you have to download the zip file from GitHub and install it in
Blender's preferences dialog.

### Install Sverchok-Extra

After you installed all of dependencies you've decided to install, installation
of Sverchok-Extra by itself is simple:

* Download [Sverchok-Extra zip archive][10] from GitHub
* In Blender, go to User Preferences > Addons > install from file > choose
  zip-archive > activate flag beside Sverchok-Extra.
* Save preferences, if you want to enable the addon permanently.

LICENSE: GPL-3.

[1]: http://blender.org
[2]: https://github.com/nortikin/sverchok
[3]: https://onurraufbingol.com/NURBS-Python/
[4]: https://scipy.org/
[5]: https://scikit-image.org/
[6]: https://pypi.org/project/pip/
[7]: https://cython.org/
[8]: https://github.com/pmneila/PyMCubes
[9]: https://nurbs-python.readthedocs.io/en/latest/install.html
[10]: https://github.com/portnov/sverchok-extra/archive/master.zip
[11]: https://github.com/portnov/sverchok-extra/wiki/Fields

