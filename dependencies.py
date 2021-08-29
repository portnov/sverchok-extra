
from sverchok.dependencies import SvDependency

ex_dependencies = dict()

try:
    import sverchok
    from sverchok.utils.logging import info, error, debug

    from sverchok.dependencies import (
            SvDependency,
            ensurepip,
            pip, scipy, geomdl, skimage,
            mcubes, circlify,
            FreeCAD
        )

    sverchok_d = ex_dependencies["sverchok"] = SvDependency(None, "https://github.com/nortikin/sverchok")
    sverchok_d.module = sverchok
    sverchok_d.message =  "Sverchok addon is available"
except ImportError:
    message =  "Sverchok addon is not available. Sverchok-Extra will not work."
    print(message)
    sverchok = None

pygalmesh_d = ex_dependencies["pygalmesh"] = SvDependency("pygalmesh", "https://github.com/nschloe/pygalmesh")
try:
    import pygalmesh
    pygalmesh_d.message = "Pygalmesh package is available"
    pygalmesh_d.module = pygalmesh
except ImportError:
    pygalmesh_d.message = "Pygalmesh package is not available. Corresponding nodes will not be available"
    info(pygalmesh_d.message)
    pygalmesh = None

sdf_d = ex_dependencies["sdf"] = SvDependency("sdf", "https://github.com/fogleman/sdf")
try:
    import sdf
    sdf_d.message = "SDF package is available"
    sdf_d.module = sdf
except ImportError:
    sdf_d.message = "SDF package is not available. SDF-based nodes will not be available"
    info(sdf_d.message)
    sdf = None

