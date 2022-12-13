
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
except ImportError:
    message =  "Sverchok addon is not available. Sverchok-Extra will not work."
    print(message)
    sverchok = None

pygalmesh_d = ex_dependencies["pygalmesh"] = SvDependency("pygalmesh", "https://github.com/nschloe/pygalmesh")
try:
    import pygalmesh
    pygalmesh_d.module = pygalmesh
except ImportError:
    pygalmesh = None

sdf_d = ex_dependencies["sdf"] = SvDependency("sdf", "https://github.com/fogleman/sdf")
try:
    import sdf
    sdf_d.module = sdf
except ImportError:
    sdf = None

pyexcel_d = ex_dependencies["pyexcel"] = SvDependency("pyexcel", "https://github.com/pyexcel/pyexcel")
try:
    import pyexcel
    pyexcel_d.module = pyexcel
except ImportError:
    pyexcel = None

pyexcel_xls_d = ex_dependencies["pyexcel_xls"] = SvDependency("pyexcel_xls", "https://github.com/pyexcel/pyexcel-xls")
try:
    import pyexcel_xls
    pyexcel_xls_d.module = pyexcel_xls
except ImportError:
    pyexcel_xls = None

pyexcel_xlsx_d = ex_dependencies["pyexcel_xlsx"] = SvDependency("pyexcel_xlsx", "https://github.com/pyexcel/pyexcel-xlsx")
try:
    import pyexcel_xlsx
    pyexcel_xlsx_d.module = pyexcel_xlsx
except ImportError:
    pyexcel_xlsx = None

pyexcel_ods_d = ex_dependencies["pyexcel_ods"] = SvDependency("pyexcel_ods", "https://github.com/pyexcel/pyexcel-ods")
try:
    import pyexcel_ods
    pyexcel_ods_d.module = pyexcel_ods
except ImportError:
    pyexcel_ods = None

