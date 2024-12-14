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
        if event in self._event_handlers:
            if event == "image_loaded":
                idx = self.get_volume_index_by_id(data["id"])
                if idx != -1:
                    self._event_handlers[event](self._volumes[idx])
                else:
                    self._event_handlers[event](data)
            else:
                self._event_handlers[event](data)

    """
    Custom events
    """

    def on_azimuth_elevation_change(self, callback, remove=False):
        """Register a callback for the 'azimuth_elevation_change' event.

        Parameters:
            callback (callable): A function that takes one argument (a dict with 'azimuth' and 'elevation' keys).
            remove (bool, optional): If `True`, remove the callback. Defaults to `False`.

        Example:
            >>> from ipywidgets import Output
            >>> from IPython.display import display
            >>> out = Output()
            >>> display(out)
            >>>
            >>> def my_callback(rotation):
            ...     with out:
            ...         print('Azimuth:', rotation['azimuth'])
            ...         print('Elevation:', rotation['elevation'])
            ...
            >>> nv.on_azimuth_elevation_change(my_callback)
        """
        self._register_callback("azimuth_elevation_change", callback, remove=remove)

    def on_click_to_segment(self, callback, remove=False):
        """Register a callback for the 'click_to_segment' event.

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
            ...         print('Volume mm³:', data['mm3'])
            ...         print('Volume mL:', data['mL'])
            ...
            >>> nv.on_click_to_segment(my_callback)
        """
        self._register_callback("click_to_segment", callback, remove=remove)

    def on_clip_plane_change(self, callback, remove=False):
        """Register a callback for the 'clip_plane_change' event."""
        self._register_callback("clip_plane_change", callback, remove=remove)

    def on_document_loaded(self, callback, remove=False):
        """Register a callback for the 'document_loaded' event."""
        self._register_callback("document_loaded", callback, remove=remove)

    def on_image_loaded(self, callback, remove=False):
        """Register a callback for the 'image_loaded' event.

        Parameters:
            callback (callable): A function that takes one argument (a niivue.Volume object).
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
        """Register a callback for the 'drag_release' event."""
        self._register_callback("drag_release", callback, remove=remove)

    def on_frame_change(self, callback, remove=False):
        """Register a callback for the 'frame_change' event."""
        self._register_callback("frame_change", callback, remove=remove)

    def on_intensity_change(self, callback, remove=False):
        """Register a callback for the 'intensity_change' event."""
        self._register_callback("intensity_change", callback, remove=remove)

    def on_location_change(self, callback, remove=False):
        """Register a callback for the 'location_change' event."""
        self._register_callback("location_change", callback, remove=remove)

    def on_mesh_added_from_url(self, callback, remove=False):
        """Register a callback for the 'mesh_added_from_url' event."""
        self._register_callback("mesh_added_from_url", callback, remove=remove)

    def on_mesh_loaded(self, callback, remove=False):
        """Register a callback for the 'mesh_loaded' event."""
        self._register_callback("mesh_loaded", callback, remove=remove)

    def on_mouse_up(self, callback, remove=False):
        """Register a callback for the 'mouse_up' event."""
        self._register_callback("mouse_up", callback, remove=remove)

    def on_volume_added_from_url(self, callback, remove=False):
        """Register a callback for the 'volume_added_from_url' event."""
        self._register_callback("volume_added_from_url", callback, remove=remove)

    def on_volume_updated(self, callback, remove=False):
        """Register a callback for the 'volume_updated' event."""
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

    def add_mesh(self, mesh: Mesh):
        """Add a single mesh to the widget.

        Parameters
        ----------
        mesh : dict
            A dictionary containing the mesh information.
        """
        self._meshes = [*self._meshes, mesh]

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
