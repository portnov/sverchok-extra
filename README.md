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
  * Straight line curve (segment)
  * Circle (Curve)
  * Formula-defined curve
  * Interpolation Curve (cubic or linear spline, uses numpy only)
  * Minimal (interpolation) Curve (uses [SciPy][4])
  * Catenary Curve (uses [SciPy][4])
  * NURBS Curve (uses [Geomdl][3] library)
  * NURBS Interpolation Curve (uses Geomdl library)
  * NURBS Approximation Curve (uses Geomdl library)
  * Circlify (pack a set of circles into another circle) (uses [Circlify][15] library)
  * Cast Curve (project curve to plane, sphere or cylinder)
  * Curve on Surface (curve in UV space of the surface)
  * Curve Lerp (linear interpolation between two curves, extrapolation is also possible)
  * Concatenate Curves (make single curve from several curves, assuming their endpoints coincide)
  * Blend Curves (by BSpline curve, uses [Geomdl][3] library)
  * Apply Vector Field to Curve
  * Curve Domain
  * Curve Length (can also calculate length of part of the curve)
  * Curve Length Parameter
  * Curve Curvature
  * Curve Torsion
  * Curve Frame ([Frenet][16] frame for the curve)
  * Curve Zero-Twist Frame (similar to previous, but rotates Frenet frame around the tangent to compensate curve's torsion)
  * Evaluate Curve
  * Marching Squares (uses [Scikit-Image][5] library)
* *Surface* category:
  * Plane Surface
  * Sphere Surface (several projections available)
  * Formula-defined Surface
  * Smooth Bivariate Spline (uses [SciPy][4])
  * NURBS Surface (uses Geomdl)
  * NURBS Interpolation Surface (uses Geomdl)
  * NURBS Approximation Surface (uses Geomdl)
  * Surface of revolution
  * Extrude Curve along Vector
  * Extrude Curve along Curve
  * Linear Surface (ruled surface made by linear interpolation of two curves; extrapolation is also possible)
  * Quads to NURBS (uses Geomdl)
  * Surface Domain (minimal / maximum values of U/V parameters of the surface)
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
  * Image Field (convert Image data block into scalar or vector field)
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
  * Vector Field Graph
  * Vector Field Lines
  * Scalar Field Graph
* *Exchange* category:
  * NURBS In (input Blender's NURBS curve or surface objects into Sverchok tree)
  * NURBS to JSON (uses Geomdl to represent NURBS surfaces or curves in JSON format which can be converted to Rhino's `3dm` by [rw3dm][12]
  * JSON to NURBS (uses Geomdl to read NURBS surfaces or curves from the same JSON format)

There will be more.

Installation
------------

This addon depends on several libraries, and you have to install at least some
of them in order to use Sverchok-Extra. If you do not need all features, you
may install only one or two of libraries, but you have to install at least
something, otherwise Sverchok-Extra will just do nothing.

One thing you will have to install anyway if you want to use Sverchok-Extra is
[pip][6]. All libraries are installed with it.

### Simple dependencies installation UI

Some of dependencies can be installed easily, by just running `pip`. For such
dependencies, Sverchok-Extra supports easy-to-use installation user interface.
To use it, navigate to Edit => Preferences, then locate Sverchok-Extra
preferences under Addons section:

![Settings](https://user-images.githubusercontent.com/284644/74547121-74555380-4f6d-11ea-8388-80421a04fc3f.png)

The dialog shows current status of all dependencies. For dependencies that can
be installed by `pip`, but are not yet installed, this dialog will show an
"Install" button. You'll have just to press the button and wait for when
Blender will say that the library is installed. If there will be any errors
during installation, Blender will report it and print details into console
output.

For dependencies that can not be installed that easily, the dialog contains a
button which opens the browser on an official web site of corresponding
library, so you can find installation instructions.

The following sections of this document will be useful if you can not install
the library by pressing the button. For libraries that can not be that easily
installed by `pip`, this document contains only short instructions. Please
refer to web sites of corresponding libraries for complete instructions and
support.

All commands provided in this document are for Linux-based systems. For Windows
and MacOS, commands may differ a bit, but the general idea will be the same.

### Install pip

In some cases, it may appear that Blender's python already knows about your
system's installation of python (python is usually installed by default on most
Linux distros). In such cases, you may use just `pip install something` to
install libraries.

There are two known ways to install `pip` into Blender.

#### Option 1

This I tested on latest Blender 2.81 builds. The similar instructions should
work for other Blender 2.8x versions.

    $ /path/to/blender/2.xx/python/bin/python3 -m ensurepip
    $ /path/to/blender/2.xx/python/bin/python3 -m pip install --upgrade pip setuptools wheel

(exact name of `python` executable depends on specific blender build).

#### Option 2

If, for some reason, Option 1 does not work for you (on some system Python says
`no module named ensurepip`), then you have to do the following:

1. Download [get-pip.py][13] script
2. Run it with Blender's python:

    $ /path/to/blender/2.xx/python/bin/python3.7m /path/to/get-pip.py

Please refer to [official pip site][14] for official installation instructions.

### Install SciPy

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U scipy

### Install SciKit-Image

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U scikit-image

### Install Circlify

    $ /path/to/blender/2.xx/python/bin/python3.7m -m pip install -U circlify

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
[12]: https://github.com/orbingol/rw3dm
[13]: https://bootstrap.pypa.io/get-pip.py
[14]: https://pip.pypa.io/en/stable/installing/
[15]: https://github.com/elmotec/circlify
[16]: https://en.wikipedia.org/wiki/Differentiable_curve#Frenet_frame

