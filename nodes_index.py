def nodes_index():
    return [{"Extra": [                                                                 # Group menu name
                ({'icon_name': 'SV_EX_ROOT_ICON'}, ),                                   # icon image ID of Group menu name. Used only first elem of tuple
                {"Extra Surfaces": [
                    ({'icon_name': 'SURFACE_DATA'}, ),                                  # icon image ID of Group menu name. Used only first elem of tuple
                    ("surface.smooth_spline", "SvExBivariateSplineNode"),               # Menu item path and class name
                    ("surface.curvature_lines", "SvExSurfaceCurvatureLinesNode"),
                    ("surface.implicit_surface_solver", "SvExImplSurfaceSolverNode"),
                    ("surface.triangular_mesh", "SvExGalGenerateMeshNode"),
                ]},
                {"Extra Curves": [
                    ({'icon_name': 'OUTLINER_OB_CURVE'}, ),                             # icon image ID of Group menu name. Used only first elem of tuple
                    ("curve.intersect_surface_plane", "SvExCrossSurfacePlaneNode"),
                    ("curve.fourier_curve", "SvFourierCurveNode"),
                    ("curve.approximate_fourier_curve", "SvApproxFourierCurveNode"),
                    ("curve.interpolate_fourier_curve", "SvInterpFourierCurveNode"),
                    ("curve.geodesic_curve", "SvExGeodesicCurveNode"),
                    None,
                    ("curve.nurbs_goal_point", "SvNurbsCurvePointsGoalNode"),
                    ("curve.nurbs_goal_tangent", "SvNurbsCurveTangentsGoalNode"),
                    ("curve.nurbs_goal_closed", "SvNurbsCurveClosedGoalNode"),
                    ("curve.nurbs_goal_cpt", "SvNurbsCurveCptGoalNode"),
                    ("curve.nurbs_solver", "SvNurbsCurveSolverNode")
                ]},
                {"Extra Fields": [
                    ({'icon_name': 'OUTLINER_OB_FORCE_FIELD'}, ),                                  # icon image ID of Group menu name. Used only first elem of tuple
                    ("field.vfield_lines_on_surface", "SvExVFieldLinesOnSurfNode"),
                    ("sdf.estimate_bounds", "SvExSdfEstimateBoundsNode")
                ]},
                {"Extra Solids": [
                    ({'icon_name': 'MESH_CUBE'}, ),                                                # icon image ID of Group menu name. Used only first elem of tuple
                    ("solid.solid_waffle", "SvSolidWaffleNode")
                ]},
                {"Extra Spatial": [
                    ({'icon_name': 'POINTCLOUD_DATA'}, ),                                          # icon image ID of Group menu name. Used only first elem of tuple
                    ("spatial.delaunay3d_surface", "SvDelaunayOnSurfaceNode"),
                    ("spatial.delaunay_mesh", "SvDelaunayOnMeshNode")
                ]},
                {"Extra Matrix": [
                    ({'icon_name': 'EMPTY_AXIS'}, ),                                               # icon image ID of Group menu name. Used only first elem of tuple
                    ("matrix.project_matrix", "SvProjectMatrixNode"),
                ]},
                {"2D Geometry": [
                    ({'icon_name': 'EMPTY_AXIS'}, ),                                               # icon image ID of Group menu name. Used only first elem of tuple
                    ("shapely.shapely_polygon", "SvExShapelyPolygonNode"),
                    ("shapely.shapely_polyline", "SvExShapelyPolylineNode"),
                    ("shapely.shapely_point", "SvExShapelyPointNode"),
                    ("shapely.shapely_from_mesh", "SvExShapelyFromMeshNode"),
                    ("shapely.shapely_voronoi", "SvExShapelyVoronoiNode"),
                    None,
                    ("shapely.shapely_transform", "SvExShapelyTransformNode"),
                    ("shapely.shapely_boolean", "SvExShapelyBooleanNode"),
                    ("shapely.shapely_buffer", "SvExShapelyBufferNode"),
                    ("shapely.shapely_offset", "SvExShapelyOffsetNode"),
                    ("shapely.shapely_boundary", "SvExShapelyBoundaryNode"),
                    None,
                    ("shapely.shapely_area", "SvExShapelyAreaNode"),
                    None,
                    ("shapely.shapely_triangulate", "SvExShapelyTriangulateNode")
                ]},
                {"SDF Primitives": [
                    ({'icon_name': 'SV_EX_SDF_ICON'}, ),                                           # icon image ID of Group menu name. Used only first elem of tuple
                    ("sdf_primitives.sdf_sphere", "SvExSdfSphereNode"),
                    ("sdf_primitives.sdf_box", "SvExSdfBoxNode"),
                    ("sdf_primitives.sdf_platonic_solid", "SvExSdfPlatonicSolidNode"),
                    ("sdf_primitives.sdf_plane", "SvExSdfPlaneNode"),
                    ("sdf_primitives.sdf_slab", "SvExSdfSlabNode"),
                    ("sdf_primitives.sdf_rounded_box", "SvExSdfRoundedBoxNode"),
                    ("sdf_primitives.sdf_torus", "SvExSdfTorusNode"),
                    ("sdf_primitives.sdf_cylinder", "SvExSdfCylinderNode"),
                    ("sdf_primitives.sdf_rounded_cylinder", "SvExSdfRoundedCylinderNode"),
                    ("sdf_primitives.sdf_capsule", "SvExSdfCapsuleNode"),
                    None,
                    ("sdf_primitives.sdf2d_circle", "SvExSdf2dCircleNode"),
                    ("sdf_primitives.sdf2d_hexagon", "SvExSdf2dHexagonNode"),
                    ("sdf_primitives.sdf2d_polygon", "SvExSdf2dPolygonNode"),
                ]},
                {"SDF Operations": [
                    ({'icon_name': 'ORIENTATION_LOCAL'}, ),                                         # icon image ID of Group menu name. Used only first elem of tuple
                    ("sdf.sdf_translate", "SvExSdfTranslateNode"),
                    ("sdf.sdf_scale", "SvExSdfScaleNode"),
                    ("sdf.sdf_rotate", "SvExSdfRotateNode"),
                    ("sdf.sdf_orient", "SvExSdfOrientNode"),
                    ("sdf.sdf_transform", "SvExSdfTransformNode"),
                    None,
                    ("sdf.sdf_boolean", "SvExSdfBooleanNode"),
                    ("sdf.sdf_blend", "SvExSdfBlendNode"),
                    ("sdf.sdf_transition_linear", "SvExSdfLinearTransitionNode"),
                    ("sdf.sdf_transition_radial", "SvExSdfRadialTransitionNode"),
                    ("sdf.sdf_dilate_erode", "SvExSdfDilateErodeNode"),
                    ("sdf.sdf_shell", "SvExSdfShellNode"),
                    ("sdf.sdf_twist", "SvExSdfTwistNode"),
                    ("sdf.sdf_linear_bend", "SvExSdfLinearBendNode"),
                    None,
                    ("sdf.sdf_slice", "SvExSdfSliceNode"),
                    ("sdf.sdf_extrude", "SvExSdfExtrudeNode"),
                    ("sdf.sdf_extrude_to", "SvExSdfExtrudeToNode"),
                    ("sdf.sdf_revolve", "SvExSdfRevolveNode"),
                    None,
                    ("sdf.sdf_generate", "SvExSdfGenerateNode"),
                ]},
                {"Data": [
                    ({'icon_name': 'THREE_DOTS'}, ),                                                # icon image ID of Group menu name. Used only first elem of tuple
                    ("data.spreadsheet", "SvSpreadsheetNode"),
                    ("data.data_item", "SvDataItemNode"),
                    ("data.excel_read", "SvReadExcelNode"),
                    ("data.excel_write", "SvWriteExcelNode")
                ]},
                {"API": [
                    ({'icon_name': 'FILE_REFRESH'}, ),                                              # icon image ID of Group menu name. Used only first elem of tuple
                    ("exchange.api_in", "SvExApiInNode"),
                    ("exchange.api_out", "SvExApiOutNode"),
                ]},
                {"Array": [
                    ({'icon_name': 'SV_ALPHA'}, ),                                                  # icon image ID of Group menu name. Used only first elem of tuple
                    ("array.input_value", "SvInputValueNode"),
                    ("array.input_array", "SvInputArrayNode"),
                    ("array.arr_number_range", "SvArrNumberRangeNode"),
                    ("array.random_array", "SvRandomArrayNode"),
                    ("array.py_to_array", "SvPyToArrayNode"),
                    ("array.arr_vector_in", "SvArrVectorInNode"),
                    ("array.arr_matrix_in", "SvArrMatrixInNode"),
                    ("array.arr_polyline", "SvArrPolylineNode"),
                    None,
                    ("array.arr_math", "SvArrMathNode"),
                    ("array.bridge_polylines", "SvArrBridgePolylinesNode"),
                    ("array.arr_polyline_length", "SvArrPolylineLengthNode"),
                    ("array.arr_resample_polyline", "SvResamplePolylineNode"),
                    ("array.arr_subdivide_polyline", "SvArrSubdividePolylineNode"),
                    ("array.arr_vector_math", "SvArrVectorMathNode"),
                    ("array.arr_rotate_vector", "SvArrRotateVectorNode"),
                    ("array.move_vertices", "SvArrMoveVerticesNode"),
                    ("array.arr_vector_noise", "SvArrVectorNoiseNode"),
                    ("array.matrix_transform", "SvArrMatrixTransformNode"),
                    ("array.move_mesh_array", "SvArrMoveMeshNode"),
                    ("array.join_mesh_array", "SvArrJoinMeshNode"),
                    ("array.flip_mesh_normals_array", "SvArrFlipMeshNormalsNode"),
                    None,
                    ("array.array_length", "SvArrayLengthNode"),
                    ("array.run_lengths", "SvArrRunLengthsNode"),
                    ("array.zip_array", "SvZipArrayNode"),
                    ("array.set_field", "SvSetFieldNode"),
                    ("array.unzip_array", "SvUnzipArrayNode"),
                    ("array.arr_get_item", "SvArrGetItemNode"),
                    ("array.slice_array", "SvSliceArrayNode"),
                    ("array.concatenate_arrays", "SvConcatenateArraysNode"),
                    ("array.to_regular_array", "SvToRegularArrayNode"),
                    ("array.new_axis", "SvNewAxisNode"),
                    ("array.unflatten_array", "SvUnflattenArrayNode"),
                    ("array.unflattening_array", "SvUnflatteningArrayNode"),
                    ("array.flatten_array", "SvFlattenArrayNode"),
                    ("array.flattening_array", "SvFlatteningArrayNode"),
                    ("array.broadcast_arrays", "SvBroadcastArraysNode"),
                    ("array.where_array", "SvWhereArrayNode"),
                    ("array.local_index", "SvLocalIndexNode"),
                    None,
                    ("array.array_to_py", "SvArrayToPyNode"),
                    ("array.print_array", "SvPrintArrayNode"),
                    ("array.array_viewer", "SvArrMeshViewerNode"),
                ]}
            ]}]
