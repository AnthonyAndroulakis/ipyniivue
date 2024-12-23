import pathlib

import anywidget
import ipywidgets
import traitlets as t
from ipywidgets import CallbackDispatcher

from ._constants import _SNAKE_TO_CAMEL_OVERRIDES
from ._options_mixin import OptionsMixin
from ._utils import (
    file_serializer,
    mesh_layers_serializer,
    serialize_options,
    snake_to_camel,
)

__all__ = ["NiiVue"]

class Mesh(ipywidgets.Widget):
    path = t.Union([t.Instance(pathlib.Path), t.Unicode()]).tag(
        sync=True, to_json=file_serializer
    )
    id = t.Unicode(default_value="").tag(sync=True)
    name = t.Unicode(default_value="").tag(sync=True)
    rgba255 = t.List([0, 0, 0, 0]).tag(sync=True)
    opacity = t.Float(1.0).tag(sync=True)
    visible = t.Bool(True).tag(sync=True)
    layers = t.List([]).tag(sync=True, to_json=mesh_layers_serializer)

    @t.validate('path')
    def _validate_path(self, proposal):
        if 'path' in self._trait_values and self.path and self.path != proposal['value']:
            raise t.TraitError('Cannot modify path once set.')
        return proposal['value']

    @t.validate('id')
    def _validate_id(self, proposal):
        if 'id' in self._trait_values and self.id and self.id != proposal['value']:
            raise t.TraitError('Cannot modify id once set.')
        return proposal['value']

class Volume(ipywidgets.Widget):
    # variables in init
    path = t.Union([t.Instance(pathlib.Path), t.Unicode()]).tag(
        sync=True, to_json=file_serializer
    )
    id = t.Unicode(default_value="").tag(sync=True)
    name = t.Unicode(default_value="").tag(sync=True)
    opacity = t.Float(1.0).tag(sync=True)
    colormap = t.Unicode("gray").tag(sync=True)
    colorbar_visible = t.Bool(True).tag(sync=True)
    cal_min = t.Float(None, allow_none=True).tag(sync=True)
    cal_max = t.Float(None, allow_none=True).tag(sync=True)

    # other properties that aren't in init
    colormap_invert = t.Bool(False).tag(sync=True)

    def __init__(self, **kwargs):
        if 'colormap_invert' in kwargs:
            kwargs.pop('colormap_invert')
        super().__init__(**kwargs)


    @t.validate('path')
    def _validate_path(self, proposal):
        if 'path' in self._trait_values and self.path and self.path != proposal['value']:
            raise t.TraitError('Cannot modify path once set.')
        return proposal['value']

    @t.validate('id')
    def _validate_id(self, proposal):
        if 'id' in self._trait_values and self.id and self.id != proposal['value']:
            raise t.TraitError('Cannot modify id once set.')
        return proposal['value']

class NiiVue(OptionsMixin, anywidget.AnyWidget):
    """
    Represents a Niivue instance.

    Parameters:
        height (int, optional): The height of the widget in pixels. Defaults to `300`.
        text_height (float, optional): Height of text labels. Defaults to `0.06`.
        colorbar_height (float, optional): Height of the colorbar as a fraction of the canvas height. Defaults to `0.05`.
        crosshair_width (int, optional): Width of the crosshair lines in pixels. Defaults to `1`.
        ruler_width (int, optional): Width of the ruler lines in pixels. Defaults to `4`.
        show_3d_crosshair (bool, optional): Whether to display the 3D crosshair. Defaults to `False`.
        back_color (tuple, optional): Background color as an RGBA tuple. Defaults to `(0, 0, 0, 1)`.
        crosshair_color (tuple, optional): Crosshair color as an RGBA tuple. Defaults to `(1, 0, 0, 1)`.
        font_color (tuple, optional): Font color as an RGBA tuple. Defaults to `(0.5, 0.5, 0.5, 1)`.
        selection_box_color (tuple, optional): Selection box color as an RGBA tuple. Defaults to `(1, 1, 1, 0.5)`.
        clip_plane_color (tuple, optional): Clip plane color as an RGBA tuple. Defaults to `(0.7, 0, 0.7, 0.5)`.
        ruler_color (tuple, optional): Ruler color as an RGBA tuple. Defaults to `(1, 0, 0, 0.8)`.
        colorbar_margin (float, optional): Margin around the colorbar as a fraction of canvas size. Defaults to `0.05`.
        trust_cal_min_max (bool, optional): Whether to trust cal_min and cal_max from image header. Defaults to `True`.
        clip_plane_hot_key (str, optional): Hotkey to toggle clip plane. Defaults to `"KeyC"`.
        view_mode_hot_key (str, optional): Hotkey to toggle view modes. Defaults to `"KeyV"`.
        double_touch_timeout (int, optional): Timeout for double touch in milliseconds. Defaults to `500`.
        long_touch_timeout (int, optional): Timeout for long touch in milliseconds. Defaults to `1000`.
        key_debounce_time (int, optional): Debounce time for key events in milliseconds. Defaults to `50`.
        is_nearest_interpolation (bool, optional): Use nearest neighbor interpolation if `True`. Defaults to `False`.
        is_resize_canvas (bool, optional): Automatically resize the canvas to fit container if `True`. Defaults to `True`.
        is_atlas_outline (bool, optional): Display atlas outlines if `True`. Defaults to `False`.
        is_ruler (bool, optional): Enable ruler tool if `True`. Defaults to `False`.
        is_colorbar (bool, optional): Display colorbar if `True`. Defaults to `False`.
        is_orient_cube (bool, optional): Display orientation cube if `True`. Defaults to `False`.
        multiplanar_pad_pixels (int, optional): Padding in pixels for multiplanar views. Defaults to `0`.
        multiplanar_force_render (bool, optional): Force rendering of multiplanar views if `True`. Defaults to `False`.
        is_radiological_convention (bool, optional): Use radiological convention if `True`. Defaults to `False`.
        mesh_thickness_on_2d (float, optional): Thickness of the mesh overlay on 2D slices. Defaults to `float('inf')`.
        drag_mode (DragMode, optional): Mode for drag interactions. Defaults to `DragMode.CONTRAST`.
        yoke_3d_to_2d_zoom (bool, optional): Yoke 3D zoom to 2D zoom if `True`. Defaults to `False`.
        is_depth_pick_mesh (bool, optional): Enable depth picking for meshes if `True`. Defaults to `False`.
        is_corner_orientation_text (bool, optional): Display corner orientation text if `True`. Defaults to `False`.
        sagittal_nose_left (bool, optional): Display nose on the left in sagittal view if `True`. Defaults to `False`.
        is_slice_mm (bool, optional): Use millimeters for slice labels if `True`. Defaults to `False`.
        is_v1_slice_shader (bool, optional): Use version 1 slice shader if `True`. Defaults to `False`.
        is_high_resolution_capable (bool, optional): Allow high-resolution rendering if `True`. Defaults to `True`.
        log_level (str, optional): Logging level. Choices are `"debug"`, `"info"`, `"warn"`, `"error"`. Defaults to `"info"`.
        loading_text (str, optional): Text to display while loading images. Defaults to `"waiting for images..."`.
        is_force_mouse_click_to_voxel_centers (bool, optional): Snap mouse clicks to voxel centers if `True`. Defaults to `False`.
        drag_and_drop_enabled (bool, optional): Enable drag-and-drop of images if `True`. Defaults to `True`.
        drawing_enabled (bool, optional): Enable drawing tools if `True`. Defaults to `False`.
        pen_value (int, optional): Value for the pen when drawing. Defaults to `1`.
        flood_fill_neighbors (int, optional): Number of neighbors for flood fill tool (6 or 26). Defaults to `6`.
        is_filled_pen (bool, optional): Use filled pen when drawing if `True`. Defaults to `False`.
        thumbnail (str, optional): URL or path to a thumbnail image. Defaults to `""`.
        max_draw_undo_bitmaps (int, optional): Maximum number of undo steps for drawing. Defaults to `8`.
        slice_type (SliceType, optional): Type of slice display. Options are `AXIAL`, `CORONAL`, `SAGITTAL`, `MULTIPLANAR`. Defaults to `SliceType.MULTIPLANAR`.
        mesh_x_ray (float, optional): X-ray effect intensity for meshes. Range from `0.0` (none) to `1.0` (full). Defaults to `0.0`.
        is_anti_alias (bool, optional): Enable anti-aliasing if `True`. Defaults to `None`.
        limit_frames_4d (float, optional): Limit the number of frames for 4D data. Defaults to `float('nan')`.
        is_additive_blend (bool, optional): Use additive blending for overlays if `True`. Defaults to `False`.
        show_legend (bool, optional): Display the legend if `True`. Defaults to `True`.
        legend_background_color (tuple, optional): Background color of the legend as RGBA tuple. Defaults to `(0.3, 0.3, 0.3, 0.5)`.
        legend_text_color (tuple, optional): Text color of the legend as RGBA tuple. Defaults to `(1.0, 1.0, 1.0, 1.0)`.
        multiplanar_layout (MuliplanarType, optional): Layout for multiplanar view. Options are `AXIAL`, `CORONAL`, `SAGITTAL`, `MULTIPLANAR`, `YOKE`. Defaults to `MuliplanarType.AUTO`.
        render_overlay_blend (float, optional): Blend factor for overlay rendering. Range from `0.0` to `1.0`. Defaults to `1.0`.
    """

    _esm = pathlib.Path(__file__).parent / "static" / "widget.js"

    height = t.Int().tag(sync=True)
    _opts = t.Dict({}).tag(sync=True, to_json=serialize_options)
    _volumes = t.List(t.Instance(Volume), default_value=[]).tag(
        sync=True, **ipywidgets.widget_serialization
    )
    _meshes = t.List(t.Instance(Mesh), default_value=[]).tag(
        sync=True, **ipywidgets.widget_serialization
    )

    def __init__(self, height: int = 300, **options):
        # convert to JS camelCase options
        _opts = {
            _SNAKE_TO_CAMEL_OVERRIDES.get(k, snake_to_camel(k)): v
            for k, v in options.items()
        }
        super().__init__(height=height, _opts=_opts, _volumes=[], _meshes=[])

        # on event
        self._event_handlers = {}
        self.on_msg(self._handle_custom_msg)

    def _register_callback(self, event_name, callback, remove=False):
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = CallbackDispatcher()
        if remove:
            self._event_handlers[event_name].remove(callback)
        else:
            self._event_handlers[event_name].register_callback(callback)

    def _handle_custom_msg(self, content, buffers):
        event = content.get("event", "")
        data = content.get("data", {})
        if event == "add_volume":
            self._add_volume_from_frontend(data)
            return
        elif event == "add_mesh":
            self._add_mesh_from_frontend(data)
            return

        if event in self._event_handlers:
            if event == "azimuth_elevation_change":
                self._event_handlers[event](data["azimuth"], data["elevation"])
            elif event == "frame_change":
                idx = self.get_volume_index_by_id(data["id"])
                if idx != -1:
                    self._event_handlers[event](self._volumes[idx], data["frame_index"])
            elif event == "image_loaded":
                idx = self.get_volume_index_by_id(data["id"])
                if idx != -1:
                    self._event_handlers[event](self._volumes[idx])
                else:
                    self._event_handlers[event](data)
            elif event == "intensity_change":
                idx = self.get_volume_index_by_id(data["id"])
                if idx != -1:
                    self._event_handlers[event](self._volumes[idx])
            elif event == "mesh_added_from_url":
                mesh_options = {
                    'url': data['url'], 
                    'headers': data['headers']
                }
                self._event_handlers[event](mesh_options, data['mesh'])
            elif event == "mesh_loaded":
                idx = self.get_mesh_index_by_id(data["id"])
                if idx != -1:
                    self._event_handlers[event](self._meshes[idx])
                else:
                    self._event_handlers[event](data)
            elif event == "volume_added_from_url":
                image_options = {
                    'url': data['url'], 
                    'headers': data['headers']
                }
                self._event_handlers[event](image_options, data['volume'])
            else:
                self._event_handlers[event](data)
                

    def _add_volume_from_frontend(self, volume_data):
        index = volume_data.pop('index', None)
        volume = Volume(**volume_data)
        if index is not None and 0 <= index <= len(self._volumes):
            self._volumes = self._volumes[:index] + [volume] + self._volumes[index:]
        else:
            self._volumes = [*self._volumes, volume]

    def _add_mesh_from_frontend(self, mesh_data):
        index = mesh_data.pop('index', None)
        mesh = Mesh(**mesh_data)
        if index is not None and 0 <= index <= len(self._meshes):
            self._meshes = self._meshes[:index] + [mesh] + self._meshes[index:]
        else:
            self._meshes = [*self._meshes, mesh]

    """
    Custom events
    """

    def on_azimuth_elevation_change(self, callback, remove=False):
        """Register a callback for the 'azimuth_elevation_change' event.

        set a callback function to run when the user changes the rotation of the 3D rendering

        Parameters:
            callback (callable): A function that takes two arguments:
                - **azimuth** (`float`): The azimuth angle in degrees.
                - **elevation** (`float`): The elevation angle in degrees.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(azimuth, elevation):
            ...     with out:
            ...         print('Azimuth:', azimuth)
            ...         print('Elevation:', elevation)
            ...
            >>> nv.on_azimuth_elevation_change(my_callback)
        """
        self._register_callback("azimuth_elevation_change", callback, remove=remove)

    def on_click_to_segment(self, callback, remove=False):
        """Register a callback for the 'click_to_segment' event.

        set a callback function when clickToSegment is enabled and the user clicks on the image

        Parameters:
            callback (callable): A function that takes one argument (a dict with 'mm3' and 'mL' keys).
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(data):
            ...     with out:
            ...         print('Clicked to segment')
            ...         print('Volume mm3:', data['mm3'])
            ...         print('Volume mL:', data['mL'])
            ...
            >>> nv.on_click_to_segment(my_callback)
        """
        self._register_callback("click_to_segment", callback, remove=remove)

    def on_clip_plane_change(self, callback, remove=False):
        """Register a callback for the 'clip_plane_change' event.

        set a callback function to run when the user changes the clip plane

        Parameters:
            callback (callable): A function that takes one argument (a list of numbers).
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(clip_plane):
            ...     with out:
            ...         print('Clip plane changed:', clip_plane)
            ...
            >>> nv.on_clip_plane_change(my_callback)
        """
        self._register_callback("clip_plane_change", callback, remove=remove)

    # todo: make volumes be a list of Volume objects and meshes be a list of Mesh objects
    def on_document_loaded(self, callback, remove=False):
        """Register a callback for the 'document_loaded' event.

        set a callback function to run when the user loads a new NiiVue document

        Parameters:
            callback (callable): A function that takes one argument—a `dict` representing the loaded document—with the following keys:
                - **title** (`str`): The title of the loaded document.
                - **opts** (`dict`): Options associated with the document.
                - **volumes** (`list` of `str`): A list of volume IDs loaded in the document.
                - **meshes** (`list` of `str`): A list of mesh IDs loaded in the document.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(document):
            ...     with out:
            ...         print('Document loaded:')
            ...         print('Title:', document['title'])
            ...         print('Options:', document['opts'])
            ...         print('Volumes:', document['volumes'])
            ...         print('Meshes:', document['meshes'])
            ...
            >>> nv.on_document_loaded(my_callback)
        """
        self._register_callback("document_loaded", callback, remove=remove)

    def on_image_loaded(self, callback, remove=False):
        """Register a callback for the 'image_loaded' event.

        set a callback function to run when a new volume is loaded

        Parameters:
            callback (callable): A function that takes one argument-a volume (`Volume`).
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(volume):
            ...     with out:
            ...         print('Image loaded:', volume.id)
            ...
            >>> nv.on_image_loaded(my_callback)
        """
        self._register_callback("image_loaded", callback, remove=remove)

    def on_drag_release(self, callback, remove=False):
        """Register a callback for the 'drag_release' event.

        set a callback function to run when the right mouse button is released after dragging

        Parameters:
            callback (callable): A function that takes one argument—a `dict` containing drag release parameters—with the following keys:
                - **fracStart** (`list` of `float`): The starting fractional coordinates `[X, Y, Z]` before the drag.
                - **fracEnd** (`list` of `float`): The ending fractional coordinates `[X, Y, Z]` after the drag.
                - **voxStart** (`list` of `float`): The starting voxel coordinates `[X, Y, Z]` before the drag.
                - **voxEnd** (`list` of `float`): The ending voxel coordinates `[X, Y, Z]` after the drag.
                - **mmStart** (`list` of `float`): The starting coordinates in millimeters `[X, Y, Z]` before the drag.
                - **mmEnd** (`list` of `float`): The ending coordinates in millimeters `[X, Y, Z]` after the drag.
                - **mmLength** (`float`): The length of the drag in millimeters.
                - **tileIdx** (`int`): The index of the image tile where the drag occurred.
                - **axCorSag** (`int`): The view index (axial=0, coronal=1, sagittal=2) where the drag occurred.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(params):
            ...     with out:
            ...         print('Drag release event:', params)
            ...
            >>> nv.on_drag_release(my_callback)
        """
        self._register_callback("drag_release", callback, remove=remove)

    def on_frame_change(self, callback, remove=False):
        """Register a callback for the 'frame_change' event.

        set a callback function to run whenever the current frame (timepoint) of a 4D image volume changes

        Parameters:
            callback (callable): A function that takes two arguments:
                - **volume** (`Volume`): The image volume object that has changed frame.
                - **frame_index** (`int`): The index of the new frame.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(volume, frame_index):
            ...     with out:
            ...         print('Frame changed')
            ...         print('Volume:', volume)
            ...         print('Frame index:', frame_index)
            ...
            >>> nv.on_frame_change(my_callback)
        """
        self._register_callback("frame_change", callback, remove=remove)

    def on_intensity_change(self, callback, remove=False):
        """Register a callback for the 'intensity_change' event.

        set a callback function to run when the user changes the intensity range with the selection box action (right click)

        Parameters:
            callback (callable): A function that takes one argument—a `Volume` object. 
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(volume):
            ...     with out:
            ...         print('Intensity changed for volume:', volume)
            ...
            >>> nv.on_intensity_change(my_callback)
        """
        self._register_callback("intensity_change", callback, remove=remove)

    def on_location_change(self, callback, remove=False):
        """Register a callback for the 'location_change' event.

        set a callback function to run when the crosshair location changes

        Parameters:
            callback (callable): A function that takes one argument—a `dict` containing the new location data—with the following keys:
                - **axCorSag** (`int`): The view index where the location changed.
                - **frac** (`list` of `float`): The fractional coordinates `[X, Y, Z]` in the volume.
                - **mm** (`list` of `float`): The coordinates `[X, Y, Z]` in millimeters.
                - **vox** (`list` of `int`): The voxel coordinates `[X, Y, Z]`.
                - **values** (`list` of `float`): The intensity values at the current location for each volume.
                - **string** (`str`): A formatted string representing the location and intensity values.
                - **xy** (`list` of `float`): The canvas coordinates `[X, Y]`.

            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(location):
            ...     with out:
            ...         print('Location changed', location)
            ...
            >>> nv.on_location_change(my_callback)
        """
        self._register_callback("location_change", callback, remove=remove)

    def on_mesh_added_from_url(self, callback, remove=False):
        """Register a callback for the 'mesh_added_from_url' event.

        set a callback function to run when a mesh is added from a url
        **Note:** This is called before the `mesh_loaded` event is emitted, so the mesh object will **not** be available in the callback.

        Parameters:
            callback (callable): A function that takes two arguments:
                - **mesh_options** (`dict`): A dictionary containing:
                    - **url** (`str`): The URL from which the mesh was loaded.
                    - **headers** (`dict`): The HTTP headers used when loading the mesh.
                - **mesh** (`dict`): A dictionary with the following properties:
                    - **id** (`str`): The ID of the mesh.
                    - **name** (`str`): The name of the mesh.
                    - **rgba255** (`list` of `int`): The RGBA color values (0-255) of the mesh.
                    - **opacity** (`float`): The opacity of the mesh.
                    - **visible** (`bool`): Whether the mesh is visible.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(mesh_options, mesh):
            ...     with out:
            ...         print('Mesh added from URL')
            ...         print('URL:', mesh_options['url'])
            ...         print('Headers:', mesh_options['headers'])
            ...         print('Mesh ID:', mesh['id'])
            ...
            >>> nv.on_mesh_added_from_url(my_callback)
        """
        self._register_callback("mesh_added_from_url", callback, remove=remove)

    def on_mesh_loaded(self, callback, remove=False):
        """Register a callback for the 'mesh_loaded' event.

        set a callback function to run when a new mesh is loaded

        Parameters:
            callback (callable): A function that takes one argument—the loaded mesh (`Mesh.`).
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(mesh):
            ...     with out:
            ...         print('Mesh loaded', mesh)
            ...
            >>> nv.on_mesh_loaded(my_callback)
        """
        self._register_callback("mesh_loaded", callback, remove=remove)

    def on_mouse_up(self, callback, remove=False):
        """Register a callback for the 'mouse_up' event.
        
        set a callback function to run when the left mouse button is released

        Parameters:
            callback (callable): A function that takes one argument—a `dict` containing mouse event data with the following keys:
                - **mouse_button_right_down** (`bool`): Indicates if the right mouse button is currently pressed (`True`) or not (`False`).
                - **mouse_button_center_down** (`bool`): Indicates if the middle mouse button is currently pressed (`True`) or not (`False`).
                - **is_dragging** (`bool`): Indicates if a drag action is in progress (`True`) or not (`False`).
                - **mouse_pos** (`tuple` of `int`): The `(x, y)` pixel coordinates of the mouse on the canvas when the button was released.
                - **frac_pos** (`tuple` of `float`): The fractional position `(X, Y, Z)` within the volume, with each coordinate ranging from 0.0 to 1.0.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(data):
            ...     with out:
            ...         print('Mouse button released', data)
            ...
            >>> nv.on_mouse_up(my_callback)
        """
        self._register_callback("mouse_up", callback, remove=remove)

    def on_volume_added_from_url(self, callback, remove=False):
        """Register a callback for the 'volume_added_from_url' event.

    set a callback function to run when a volume is added from a url
     **Note:** This is called before the `image_loaded` event is emitted, so the volume object will **not** be available in the callback.

    Parameters:
        callback (callable): A function that takes two arguments:
            - **image_options** (`dict`): A dictionary containing:
                - **url** (`str`): The URL from which the volume was loaded.
                - **headers** (`dict`): The HTTP headers used when loading the volume.
            - **volume** (`dict`): A dictionary with the following properties:
                - **id** (`str`): The ID of the volume.
                - **name** (`str`): The name of the volume.
                - **colormap** (`str`): The colormap used for the volume.
                - **opacity** (`float`): The opacity of the volume.
                - **colorbar_visible** (`bool`): Whether the colorbar is visible for the volume.
                - **cal_min** (`float` or `None`): The minimum calibration value.
                - **cal_max** (`float` or `None`): The maximum calibration value.
        remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

    Example:
        >>> from ipywidgets import Output
        >>> from IPython.display import display
        >>> out = Output()
        >>> display(out)
        >>>
        >>> def my_callback(image_options, volume):
        ...     with out:
        ...         print('Volume added from URL')
        ...         print('URL:', image_options['url'])
        ...         print('Headers:', image_options['headers'])
        ...         print('Volume ID:', volume['id'])
        ...
        >>> nv.on_volume_added_from_url(my_callback)
        """
        self._register_callback("volume_added_from_url", callback, remove=remove)

    def on_volume_updated(self, callback, remove=False):
        """Register a callback for the 'volume_updated' event.
        
        set a callback function to run when updateGLVolume is called (most users will not need to use
        
        Parameters:
            callback (callable): A function that takes no arguments.
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.
        
        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback():
            ...     with out:
            ...         print('Volumes updated')
            ...
            >>> nv.on_volume_updated(my_callback)
        """
        self._register_callback("volume_updated", callback, remove=remove)

    """
    Methods
    """
    def save_scene(self, filename: str = "screenshot.png"):
        """Send a message to the frontend to save the scene with the given filename.
        
        Parameters
        ----------
        filename : str
            The filename to save the scene to.
        """
        self.send({
            'type': 'save_scene',
            'data': filename
        })

    def get_volume_index_by_id(self, id_: str) -> int:
        """Return the index of the volume with the given id.

        Parameters
        ----------
        id_ : str
            The id of the volume.
        """
        for idx, vol in enumerate(self._volumes):
            if vol.id == id_:
                return idx
        return -1

    def get_mesh_index_by_id(self, id_: str) -> int:
        """Return the index of the mesh with the given id.

        Parameters
        ----------
        id_ : str
            The id of the mesh.
        """
        for idx, mesh in enumerate(self._meshes):
            if mesh.id == id_:
                return idx
        return -1

    def load_volumes(self, volumes: list):
        """Load a list of volumes into the widget.

        Parameters
        ----------
        volumes : list
            A list of dictionaries containing the volume information.
        """
        volumes = [Volume(**item) for item in volumes]
        self._volumes = volumes

    def add_volume(self, volume: dict):
        """Add a single volume to the widget.

        Parameters
        ----------
        volume : dict
            A dictionary containing the volume information.
        """
        self._volumes = [*self._volumes, Volume(**volume)]

    @property
    def volumes(self):
        """Returns the list of volumes."""
        return list(self._volumes)

    def load_meshes(self, meshes: list):
        """Load a list of meshes into the widget.

        Parameters
        ----------
        meshes : list
            A list of dictionaries containing the mesh information.
        """
        meshes = [Mesh(**item) for item in meshes]
        self._meshes = meshes

    def add_mesh(self, mesh: dict):
        """Add a single mesh to the widget.

        Parameters
        ----------
        mesh : dict
            A dictionary containing the mesh information.
        """
        self._meshes = [*self._meshes, Mesh(**mesh)]

    @property
    def meshes(self):
        """Returns the list of meshes."""
        return list(self._meshes)
    
    
    '''
    Other functions
    '''
    def colormaps(self):
        """Retrieve the list of available colormap names.

        Returns
        -------
        list of str
            A list containing the names of all available colormaps that can be used
        """
        return [
            "actc", "afni_blues_inv", "afni_reds_inv", "bcgwhw", "bcgwhw_dark",
            "blue", "blue2cyan", "blue2magenta", "blue2red", "bluegrn", "bone",
            "bronze", "cet_l17", "cividis", "cool", "copper", "copper2",
            "ct_airways", "ct_artery", "ct_bones", "ct_brain", "ct_brain_gray",
            "ct_cardiac", "ct_head", "ct_kidneys", "ct_liver", "ct_muscles",
            "ct_scalp", "ct_skull", "ct_soft", "ct_soft_tissue", "ct_surface",
            "ct_vessels", "ct_w_contrast", "cubehelix", "electric_blue",
            "freesurfer", "ge_color", "gold", "gray", "green", "green2cyan",
            "green2orange", "hot", "hotiron", "hsv", "inferno", "jet", "linspecer",
            "magma", "mako", "nih", "plasma", "random", "red", "redyell",
            "rocket", "roi_i256", "surface", "turbo", "violet", "viridis",
            "warm", "winter", "x_rain"
        ]

    def add_colormap(self, name: str, color_map: dict):
        """Add a colormap to the widget.

        Parameters
        ----------
        name : str
            The name of the colormap.
        color_map : dict
            A dictionary containing the colormap information. It must have the following keys:

            **Required keys**:
                - `'R'`: list of numbers
                - `'G'`: list of numbers
                - `'B'`: list of numbers
                - `'A'`: list of numbers
                - `'I'`: list of numbers

            **Optional keys**:
                - `'min'`: number
                - `'max'`: number
                - `'labels'`: list of strings

            All the `'R'`, `'G'`, `'B'`, `'A'`, `'I'` lists must have the same length.

        Raises
        ------
        ValueError
            If the colormap does not meet the required format.
        TypeError
            If the colormap values are not of the correct type.
        """
        # Validate that required keys are present and are lists of numbers
        required_keys = ['R', 'G', 'B', 'A', 'I']
        for key in required_keys:
            if key not in color_map:
                raise ValueError(f"ColorMap must include required key '{key}'")
            if not isinstance(color_map[key], list):
                raise TypeError(f"ColorMap key '{key}' must be a list")
            if not all(isinstance(x, (int, float)) for x in color_map[key]):
                raise TypeError(f"All elements in ColorMap key '{key}' must be numbers")

        # Check that all required lists have the same length
        lengths = [len(color_map[key]) for key in required_keys]
        if len(set(lengths)) != 1:
            raise ValueError("All 'R', 'G', 'B', 'A', 'I' lists must have the same length")

        # Validate optional keys
        if 'min' in color_map and not isinstance(color_map['min'], (int, float)):
            raise TypeError("ColorMap 'min' must be a number")

        if 'max' in color_map and not isinstance(color_map['max'], (int, float)):
            raise TypeError("ColorMap 'max' must be a number")

        if 'labels' in color_map:
            if not isinstance(color_map['labels'], list):
                raise TypeError("ColorMap 'labels' must be a list of strings")
            if not all(isinstance(label, str) for label in color_map['labels']):
                raise TypeError("All elements in ColorMap 'labels' must be strings")
            if len(color_map['labels']) != lengths[0]:
                raise ValueError("ColorMap 'labels' must have the same length as 'R', 'G', 'B', 'A', 'I' lists")

        # Send the colormap to the frontend
        self.send({
            'type': 'add_colormap',
            'data': {
                'name': name,
                'cmap': color_map
            }
        })
    
    def set_colormap(self, imageID: str, colormap: str):
        """set the colormap for a volume

        Parameters
        ----------
        imageID : str
            The ID of the volume.
        colormap : str
            The name of the colormap to set.
        
        Raises
        ------
        ValueError
            If the volume with the given ID is not found.
        """
        idx = self.get_volume_index_by_id(imageID)
        if idx != -1:
            self._volumes[idx].colormap = colormap
        else:
            raise ValueError(f"Volume with ID '{imageID}' not found")
    
    def set_selection_box_color(self, color: tuple):
        """set the selection box color

        Parameters
        ----------
        color : tuple of floats
            An RGBA array with values ranging from 0 to 1.

        Raises
        -------
        ValueError
            If the color is not a list of four numeric values.
        """
        if not isinstance(color, (list, tuple)) or len(color) != 4:
            raise ValueError("Color must be a list or tuple of four numeric values (RGBA).")
        if not all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in color):
            raise ValueError("Each color component must be a number between 0 and 1.")
        
        self.selection_box_color = tuple(color)

    def set_crosshair_color(self, color: tuple):
        """set the crosshair and colorbar outline color

        Parameters
        ----------
        color : tuple of floats
            An RGBA array with values ranging from 0 to 1.

        Raises
        -------
        ValueError
            If the color is not a list of four numeric values.
        """
        if not isinstance(color, (list, tuple)) or len(color) != 4:
            raise ValueError("Color must be a list or tuple of four numeric values (RGBA).")
        if not all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in color):
            raise ValueError("Each color component must be a number between 0 and 1.")
        
        self.crosshair_color = tuple(color)
    
    def set_crosshair_width(self, width: int):
        """set the crosshair width

        Parameters
        ----------
        width : int
            The width of the crosshair in pixels.
        """
        self.crosshair_width = width

    def set_gamma(self, gamma: float):
        """Adjust screen gamma. Low values emphasize shadows but can appear flat, high gamma hides shadow details.

        Parameters
        ----------
        gamma : float
            Selects luminance

        Raises
        ------
        TypeError
            If gamma is not a number

        Example
        -------
        >>> nv.set_gamma(1.0)
        """
        if not isinstance(gamma, (int, float)):
            raise TypeError("gamma must be a number")

        self.send({
            'type': 'set_gamma',
            'data': gamma
        })

class WidgetObserver:
    """Sets an observed for `widget` on the `attribute` of `object`."""

    def __init__(self, widget, object, attribute):
        self.widget = widget
        self.object = object
        self.attribute = attribute
        self._observe()

    def _widget_change(self, change):
        setattr(self.object, self.attribute, change["new"])

    def _observe(self):
        self.widget.observe(self._widget_change, names=["value"])
