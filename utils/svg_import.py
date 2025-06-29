from sverchok_extra.dependencies import svgelements

if svgelements is not None:
    from svgelements import (
            SVG, Path, Circle, Ellipse,
            Rect, Polygon, Polyline, Line, Arc,
            SimpleLine, Group, Close,
            CubicBezier, QuadraticBezier)

import numpy as np
import mathutils

from sverchok.utils.curve.primitives import SvLine, SvCircle, SvEllipse
from sverchok.utils.curve.bezier import SvBezierCurve, SvCubicBezierCurve
from sverchok.utils.curve.algorithms import concatenate_curves, sort_curves_for_concat

def convert_matrix(transform, center):
    m = [[transform.a, transform.c, 0, transform.e],
         [transform.b, transform.d, 0, transform.f],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]]
    matrix = mathutils.Matrix(m)
    translate = mathutils.Matrix.Translation((center[0], center[1], 0))
    return matrix @ translate

def process_path(element, concatenate=True):
    result = []
    for segment in element:
        curve = process_path_element(segment)
        if curve:
            #print(curve)
            result.append(curve)
    if concatenate:
        result = sort_curves_for_concat(result, allow_flip=True).curves
        curve = concatenate_curves(result, allow_generic=False, allow_split=True)
        if isinstance(curve, list):
            result = curve
        else:
            result = [curve]
    return result

def process_path_element(segment):
    if isinstance(segment, CubicBezier):
        pts = [(p.x,p.y,0) for p in [segment.start, segment.control1, segment.control2, segment.end]]
        return SvCubicBezierCurve(*pts)
    elif isinstance (segment, QuadraticBezier):
        pts = [(p.x,p.y,0) for p in [segment.start, segment.control, segment.end]]
        return SvBezierCurve(pts)
    elif isinstance(segment, Line):
        pts = [(p.x,p.y,0) for p in [segment.start, segment.end]]
        return SvLine.from_two_points(*pts)
    elif isinstance(segment, Close):
        pts = [(p.x,p.y,0) for p in [segment.start, segment.end]]
        return SvLine.from_two_points(*pts)
    elif isinstance(segment, Arc):
        matrix = mathutils.Matrix.Rotation(segment.get_rotation().as_radians, 4, 'Z')
        center = segment.center
        matrix.translation = (center[0], center[1], 0)
        ellipse = SvEllipse(matrix, segment.rx, segment.ry)
        start_t = segment.get_start_t()
        ellipse.u_bounds = (start_t, start_t + segment.sweep)
        return ellipse
    else:
        print("Unsupported:", segment)

def process_element(element, concatenate_paths=True):
    result = []
    if isinstance(element, Group):
        for child in element:
            group = process_element(child, concatenate_paths=concatenate_paths)
            if group:
                result.extend(group)

    elif isinstance(element, Path):
        result.extend(process_path(element, concatenate=concatenate_paths))
        
    elif isinstance(element, (Line, SimpleLine)):
        start = (element.x1, element.y1, 0)
        end = (element.x2, element.y2, 0)
        result.append(SvLine.from_two_points(start, end))
    
    elif isinstance(element, Circle):
        cx, cy, r = element.cx, element.cy, element.rx
        m = convert_matrix(element.transform, (cx, cy))
        result.append(SvCircle(matrix = m, radius=r, center=(cx,cy, 0)))
    
    elif isinstance(element, Ellipse):
        #print("E", element)
        cx, cy, rx, ry = element.cx, element.cy, element.rx, element.ry
        m = convert_matrix(element.transform, (cx, cy))
        ellipse = SvEllipse(matrix=m, a=rx, b=ry)
        result.append(ellipse)
    
    elif isinstance(element, Rect):
        #segments = [segment * element.transform for segment in element.segments()]
        result.extend(process_path(element.segments(), concatenate=concatenate_paths))
    
    elif isinstance(element, (Polygon, Polyline)):
        points = [(p.x, p.y, 0) for p in element.points]
        for p1, p2 in zip(points, points[1:]):
            line = SvLine.from_two_points(p1, p2)
            result.append(line)
        if isinstance(element, Polygon):
            line = SvLine.from_two_points(points[-1], points[0])
            result.append(line)

    return result

def parse_svg(path, ppi=96.0, concatenate_paths=True, convert_coords=True):
    result = []
    svg = SVG.parse(path, ppi=ppi)

    if convert_coords:
        vector = np.array((0, svg.height, 0))

    for element in svg.elements():
        sub = process_element(element, concatenate_paths=concatenate_paths)
        if sub:
            if convert_coords:
                for curve in sub:
                    result.append(curve.mirror(1).translate(vector))
            else:
                result.extend(sub)
    return result

