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

class Volume(ipywidgets.Widget):
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

class NiiVue(OptionsMixin, anywidget.AnyWidget):
    """Represents a Niivue instance."""

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
