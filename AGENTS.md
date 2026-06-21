# Sverchok-Extra — Agent Guide

## What is Sverchok-Extra?

**Sverchok-Extra** is a Blender add-on that extends [Sverchok](https://github.com/nortikin/sverchok) — a parametric, node-based geometry programming tool for Blender. It contains experimental and dependency-heavy nodes that are not suitable for the Sverchok core.

- **Version**: 0.1.0.0
- **Author**: Ilya Portnov
- **License**: GPL-3
- **Minimum Blender**: 2.81
- **Parent project**: Sverchok ≥ 1.4.0

Sverchok-Extra serves as a **sandbox / nursery** for new node ideas. If a node is too complex, too experimental, or requires additional dependencies, it belongs here rather than in Sverchok core.

---

## Project Structure

```
sverchok-extra/
├── __init__.py              # Add-on entry point; registers nodes & menu
├── dependencies.py          # External dependency detection (scipy, sdf, shapely, …)
├── settings.py              # Add-on preferences (dependency status UI)
├── icons.py                 # Custom icon provider for Sverchok
├── nodes_index.py           # Node catalog → Blender node tree menu mapping
├── testing.py               # Test runner harness (invoked by Blender --python)
├── run_tests.sh             # Shell wrapper: blender … --python testing.py
├── nodes/                   # All node implementations (see categories below)
│   ├── array/               # Array manipulation (40+ nodes)
│   ├── curve/               # Curves: optimal Bezier, Fourier, NURBS, geodesic
│   ├── data/                # Spreadsheet, Excel read/write
│   ├── exchange/            # SVG import, API in/out
│   ├── field/               # Vector fields, exponential maps
│   ├── matrix/              # Matrix operations
│   ├── sdf/                 # SDF operations (boolean, blend, twist, …)
│   ├── sdf_primitives/      # SDF primitives (box, sphere, torus, …)
│   ├── shapely/             # 2D geometry via shapely (polygons, voronoi, …)
│   ├── solid/               # Solid modeling (waffle)
│   ├── spatial/             # Delaunay triangulation
│   └── surface/             # Surfaces: spline, curvature lines, implicit
├── utils/                   # Shared utilities (no Blender dependency)
│   ├── array_math/          # Awkward-array math helpers
│   ├── curve/               # Optimal Bezier, Fourier curve algorithms
│   ├── modules/             # Reusable utility modules
│   ├── api.py               # API helper
│   ├── geodesic.py          # Geodesic curve computation
│   ├── manifolds.py         # Manifold utilities
│   ├── sdf.py               # SDF scalar field wrappers
│   ├── shapely.py           # Shapely geometry ↔ mesh conversion
│   ├── sockets.py           # Custom socket registration
│   └── svg_import.py        # SVG import via svgelements
├── tests/                   # Unit tests
├── docs/                    # Documentation sources (RST)
└── icons/                   # Custom PNG icons
```

---

## Sverchok Core Reference

Sverchok core sources are in separate directory. Key files:

| Path | Purpose |
|------|---------|
| `__init__.py` | Core entry point; imports core, nodes, registers |
| `node_tree.py` | `SverchCustomTreeNode` base class for all nodes |
| `data_structure.py` | `updateNode`, `zip_long_repeat`, `fullList`, `ensure_nesting_level` |
| `core/sockets.py` | Socket types: `SvVerticesSocket`, `SvStringsSocket`, `SvMatrixSocket`, `SvGeom2DSocket`, `SvScalarFieldSocket`, etc. |
| `core/update_system.py` | Node update system |
| `dependencies.py` | `SvDependency`, dependency detection, `draw_message` |
| `utils/testing.py` | `SverchokTestCase` base class for tests |
| `utils/field/scalar.py` | `SvScalarField` base class |
| `utils/field/vector.py` | `SvVectorField` base class |

---

## Node Conventions

### Class Definition

Every node is a Python class inheriting from both `SverchCustomTreeNode` and `bpy.types.Node`:

```python
import bpy
from sverchok.node_tree import SverchCustomTreeNode

class SvExMyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: My Node
    Tooltip: Short description shown in node search
    """
    bl_idname = 'SvExMyNode'
    bl_label = 'My Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EX_SOME_ICON'       # Custom icon from sverchok_extra icons
    sv_dependencies = {'shapely'}     # Set or list of required dependencies
```

### Sockets

- **Inputs**: created in `sv_init(self, context)` via `self.inputs.new(SocketClass, "Name")`
- **Outputs**: created in `sv_init(self, context)` via `self.outputs.new(SocketClass, "Name")`
- Common socket types:
  - `SvVerticesSocket` — list of 3D vertices
  - `SvStringsSocket` — generic data (lists, integers, strings)
  - `SvMatrixSocket` — transformation matrices
  - `SvGeom2DSocket` — 2D geometry (shapely)
  - `SvScalarFieldSocket` — scalar field (SDF)
  - `SvVectorFieldSocket` — vector field

### Data Processing

The `process(self)` method is the main entry point. Key patterns:

```python
def process(self):
    # Check if any output is linked (early exit optimization)
    if not any(socket.is_linked for socket in self.outputs):
        return

    # Get input data — returns list of lists (batched)
    data_s = self.inputs['Data'].sv_get()

    # Use zip_long_repeat for parallel iteration over multiple inputs
    for data in zip_long_repeat(data_s, other_s):
        # ... process ...
        pass

    # Set output data
    self.outputs['Output'].sv_set(result)
```

### Properties

Use `bpy.props` for node parameters:

```python
my_property : IntProperty(
    name="My Property",
    default=10,
    min=1,
    update=updateNode)
```

### Drawing Buttons

```python
def draw_buttons(self, context, layout):
    layout.prop(self, "my_property")

def draw_buttons_ext(self, context, layout):
    self.draw_buttons(context, layout)
    # Additional properties for the full panel
```

### Registration

Each node module must define `register()` and `unregister()`:

```python
def register():
    bpy.utils.register_class(SvExMyNode)

def unregister():
    bpy.utils.unregister_class(SvExMyNode)
```

Or use the factory shortcut (for single-class modules):

```python
register, unregister = bpy.utils.register_classes_factory([SvExMyNode])
```

---

## Node Categories & Key Nodes

### Array (`nodes/array/`)
40+ nodes for array manipulation. Heavily uses the **Awkward Array** library for high-performance nested array operations. Key nodes: `arr_math`, `flatten_array`, `broadcast_arrays`, `where_array`, `local_index`, `arr_vector_math`, `matrix_transform`, `join_mesh_array`.

### Curves (`nodes/curve/`)
- **Optimal Bezier** (`SvExOptimalBezierSplineNode`) — C2-continuous cubic Bezier spline with energy minimization
- **Fourier Curves** (`SvFourierCurveNode`, `SvApproxFourierCurveNode`, `SvInterpFourierCurveNode`)
- **NURBS Solver** (`SvNurbsCurveSolverNode`) with goal constraints (point, tangent, closed, cpt)
- **Geodesic Curves** (`SvExGeodesicCurveNode`, `SvExGeodesicCauchyNode`) — geodesic computation on meshes

### SDF (`nodes/sdf/` + `nodes/sdf_primitives/`)
Full SDF (Signed Distance Function) toolkit using the [fogleman/sdf](https://github.com/fogleman/sdf) library.

**Primitives**: box, sphere, cylinder, torus, capsule, rounded variants, platonic solids, 2D primitives (circle, hexagon, polygon).

**Operations**: translate, scale, rotate, orient, general transform, boolean (union/intersection/difference), blend, transitions (linear/radial), dilate/erode, shell, twist, linear bend, slice, extrude, extrude-to, revolve, generate (marching cubes).

### Shapely 2D Geometry (`nodes/shapely/`)
2D geometry operations using the [shapely](https://github.com/shapely/shapely) library:
- Creation: polygon, polyline, point, from mesh
- Operations: transform, boolean, buffer, offset, clip by rect
- Analysis: convex hull, concave hull, simplify, boundary, length, area, distance
- Voronoi diagram, triangulation

### Surface (`nodes/surface/`)
- **Smooth Bivariate Spline** — scipy-based surface interpolation
- **Implicit Surface Solver** — experimental implicit surface generation
- **Surface Curvature Lines** — curvature line extraction
- **Triangular Mesh** — mesh generation (uses pygalmesh)

### Spatial (`nodes/spatial/`)
- **Delaunay 3D on Surface** — 3D Delaunay triangulation on surfaces
- **Delaunay Mesh** — adds vertices to existing mesh via Delaunay triangulation

### Field (`nodes/field/`)
- **Vector Field Lines on Surface** — streamline visualization
- **Exponential Map** — Riemannian exponential map computation

### Data (`nodes/data/`)
- **Spreadsheet** — tabular data editor
- **Excel Read/Write** — pyexcel-based spreadsheet I/O

### Exchange (`nodes/exchange/`)
- **SVG Read** — import SVG files via svgelements
- **API In/Out** — external API integration

---

## Dependencies

Dependencies are declared in `dependencies.py` and checked at import time. Nodes declare their dependencies via `sv_dependencies` (set or list).

### External Libraries

| Library | Used By | Pip Installable |
|---------|---------|-----------------|
| **scipy** | Surface splines, curvature lines, vector fields | Yes |
| **sdf** (fogleman) | SDF primitives & operations | Yes |
| **shapely** | 2D geometry nodes | Yes |
| **awkward** | Array math nodes | Yes |
| **pygalmesh** | Triangular mesh generation | Yes |
| **pyexcel** + family | Excel I/O | Yes |
| **svgelements** | SVG import | Yes |

### Dependency Pattern

```python
from sverchok_extra.dependencies import shapely

class SvExMyNode(SverchCustomTreeNode, bpy.types.Node):
    sv_dependencies = {'shapely'}

    def process(self):
        if shapely is None:
            return  # Graceful skip when dependency unavailable
        # ... use shapely ...
```

---

## Testing

### Running Tests

```bash
# From sverchok-extra root:
./run_tests.sh

# Or with custom Blender path:
BLENDER=/path/to/blender ./run_tests.sh
```

### Test Structure

Tests live in `tests/`. They inherit from `sverchok.utils.testing.SverchokTestCase`:

```python
from sverchok.utils.testing import SverchokTestCase
from sverchok_extra.utils.curve.optimal_bezier import optimal_bezier_spline

class TestOptimalBezier(SverchokTestCase):
    def test_basic(self):
        points = np.array([[0,0,0], [1,1,0], [2,0,0]], dtype=np.float64)
        curve = optimal_bezier_spline(points)
        self.assertIsNotNone(curve)
```

### Test Conventions

- Use `np.allclose()` for floating-point comparisons
- Test data should be deterministic (seeded random, or fixed values)
- Each test file should have a clear, descriptive name matching the module under test
- Tests should be self-contained and not depend on Blender UI state

---

## Utility Modules

### `utils/curve/optimal_bezier.py`
Implements the optimal Bezier spline algorithm from the paper "Optimal Bezier Curves" by V. Borisenko. Key function: `optimal_bezier_spline(points)` → returns `SvCurve` object.

### `utils/sdf.py`
Wraps the `sdf` library into Sverchok's field system:
- `SvExSdfScalarField` — 3D scalar field wrapping `sdf3`
- `SvExSdf2DScalarField` — 2D scalar field wrapping `sdf2`
- `scalar_field_to_sdf(field, iso_value)` — convert SvScalarField → sdf object
- `scalar_field_to_sdf_2d(field, iso_value)` — convert to 2D sdf
- `estimate_bounds(field)` — auto-estimate bounding box for SDF evaluation
- `geometry_from_points(points)` — extract mesh from marching cubes points

### `utils/shapely.py`
Converts between shapely geometries and mesh data:
- `to_mesh(verts, edges, faces)` → shapely geometry
- `to_mesh(geometry)` → (verts, edges, faces)
- `triangulate(geometry)` — Delaunay triangulation of shapely geometry
- `boundary(geometry)`, `union_collection(geometry)`

### `utils/geodesic.py`
Geodesic curve computation on surfaces.

### `utils/manifolds.py`
Manifold-related utilities.

---

## Adding a New Node

1. **Create the module**: `nodes/<category>/<name>.py`
2. **Define the node class** following the conventions above
3. **Declare dependencies** via `sv_dependencies`
4. **Register/unregister** the class
5. **Add to `nodes_index.py`** under the appropriate category:
   ```python
   ("category.subcategory", "SvExMyNewNode"),
   ```
6. **Add tests** in `tests/`
7. **Add documentation** in `docs/nodes/<category>/` (RST format)
8. **Optionally add an icon**: `icons/sv_ex_my_new_icon.png`

### Module `__init__.py`

Each node subdirectory has an `__init__.py` that imports and registers all node classes from its modules. Ensure new node modules are imported there.

---

## Architecture Notes

### How Nodes Are Loaded

1. `__init__.py` calls `nodes_index()` to get the menu structure
2. `make_node_list()` extracts module paths from the index
3. Each module is imported via `importlib.import_module()`
4. `register_nodes()` calls `module.register()` for each

### Reload Support

Sverchok supports hot-reloading. When `bpy` is already in `locals()`, a reload event fires and modules are re-imported via `importlib.reload()`.

### Data Flow

Sverchok uses a **batched data model**:
- Data is always a list of lists (or deeper nesting)
- Each outer list element = one "item" or "batch"
- `zip_long_repeat()` iterates over multiple inputs in parallel, repeating the last element
- `ensure_nesting_level()` normalizes data nesting
- `fullList()` extends short lists to match a reference length

### Socket Types Hierarchy

All custom sockets inherit from Blender's `NodeSocket`:
- `SvBaseSocket` → `SvStringsSocket`, `SvVerticesSocket`, `SvMatrixSocket`, etc.
- `SvGeom2DSocket` → for shapely 2D geometry
- `SvScalarFieldSocket` → for SDF scalar fields
- `SvVectorFieldSocket` → for vector fields

---

## Coding Style

- Follow the existing code style in the project
- Include the Sverchok license header (GPL3) in new files
- Use type hints where helpful
- Keep node classes focused — complex algorithms should be in `utils/`
- Document node purpose in docstrings (`Triggers:` for search, `Tooltip:` for hover)
- Use `sv_icon` for custom icons; fall back to `bl_icon` for standard icons

---

## Common Pitfalls

1. **Missing dependency check**: Always check if a dependency is `None` before using it
2. **Data nesting**: Use `ensure_nesting_level()` when input data may have varying nesting depths
3. **Early exit**: Always check `any(socket.is_linked for socket in self.outputs)` at the start of `process()`
4. **Socket naming**: Use descriptive socket names that match Sverchok conventions
5. **Icon naming**: Custom icons use the pattern `sv_ex_<name>.png` in the `icons/` directory
6. **Node ID naming**: Use `SvEx` prefix for all node IDs to avoid conflicts with core Sverchok nodes

---

## Documentation

- RST documentation files go in `docs/nodes/<category>/`
- The main Sverchok documentation is at http://nortikin.github.io/sverchok/
- Sverchok-Extra documentation is generated alongside core docs

---

## Quick Reference: Key Imports

```python
# Always needed for nodes
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, fullList

# For properties
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, StringProperty

# For math
import numpy as np
from mathutils import Matrix, Vector

# For dependency checks
from sverchok_extra.dependencies import shapely, scipy, sdf, awkward

# For testing
from sverchok.utils.testing import SverchokTestCase
```
