
ex_dependencies = dict()

try:
    import sverchok
    from sverchok.utils.logging import info, error, debug

    from sverchok.dependencies import (
            SvDependency,
            ensurepip,
            pip, scipy, geomdl, skimage,
            mcubes, circlify, ladybug,
            FreeCAD
        )

    sverchok_d = ex_dependencies["sverchok"] = SvDependency(None, "https://github.com/nortikin/sverchok")
    sverchok_d.module = sverchok
    sverchok_d.message =  "Sverchok addon is available"
except ImportError:
    message =  "Sverchok addon is not available. Sverchok-Extra will not work."
    print(message)
    sverchok = None

pygalmesh_d = dependencies["pygalmesh"] = Dependency("pygalmesh", "https://github.com/nschloe/pygalmesh")
try:
    import pygalmesh
    pygalmesh_d.message = "Pygalmesh package is available"
    pygalmesh_d.module = pygalmesh
except ImportError:
    pygalmesh_d.message = "Pygalmesh package is not available. Corresponding nodes will not be available"
    info(pygalmesh_d.message)
    pygalmesh = None

