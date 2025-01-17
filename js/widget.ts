import * as niivue from "@niivue/niivue";
import { v4 as uuidv4 } from '@lukeed/uuid';

import type { Model } from "./types.ts";
import { Disposer } from "./lib.ts";
import { render_meshes } from "./mesh.ts";
import { render_volumes } from "./volume.ts";

const nvMap = new Map<string, niivue.Niivue>();

export default {
  async initialize({ model }: { model: Model }) {
    let id = model.get("id");
    console.log("Initializing called on model:", id);
    const disposer = new Disposer();

    let nv = nvMap.get(model.get("id"));

    if (!nv) {
      console.log("Creating new Niivue instance");
      nv = new niivue.Niivue(model.get("_opts"));
      nvMap.set(model.get("id"), nv);
    }

    // Attach non-display event handlers
    attachModelEventHandlers(nv, model, disposer);

    // Attach niivue event handlers
    attachNiivueEventHandlers(nv, model);

    // Return cleanup function for non-display things
    return () => {
      disposer.disposeAll();

      model.off("change:_volumes");
      model.off("change:_meshes");
      model.off("change:_opts");
      model.off("change:background_masks_overlays");
      model.off("msg:custom");
      model.off("change:height");

      // remove the nv instance
      nvMap.delete(model.get("id"));
    };
  },

  async render({ model, el }: { model: Model; el: HTMLElement }) {
    const nv = nvMap.get(model.get("id"));
    if (!nv) {
      console.error("Niivue instance not found for model", model.get("id"));
      return;
    }

    const disposer = new Disposer();

    if (!nv.canvas?.parentNode) {
      console.log('drawing first render')
      // Create a container div and set its height
      const container = document.createElement("div");
      container.style.height = `${model.get("height")}px`;
      el.appendChild(container);

      // Create a new canvas and attach it to the container
      const canvas = document.createElement("canvas");
      container.appendChild(canvas);

      // Handle height changes
      model.on("change:height", () => {
        container.style.height = `${model.get("height")}px`;
      });

      nv.attachToCanvas(canvas);

      // Load initial volumes and meshes
      await render_volumes(nv, model, disposer);
      await render_meshes(nv, model, disposer);
    } else {
      console.log('moving render around')
      // Ensure the canvas is attached to the container
      if (nv.canvas.parentNode?.parentNode) {
        nv.canvas.parentNode.parentNode.removeChild(nv.canvas.parentNode);
      }
      el.appendChild(nv.canvas.parentNode);
    }

    // Return cleanup function, runs when page reloaded or cell run again
    return () => {
      //disposer.disposeAll(); //commented out...otherwise, reruning the cell will remove observers
      // only want to run disposer when nv widget is removed, not when it is re-displayed

      if (nv.canvas?.parentNode?.parentNode) {
        nv.canvas.parentNode.parentNode.removeChild(nv.canvas.parentNode);
      }
    };
  },
};

function attachNiivueEventHandlers(nv: niivue.Niivue, model: Model) {
  // Attach Niivue event handlers
  nv.onAzimuthElevationChange = function (azimuth: number, elevation: number) {
    model.send({
      event: "azimuth_elevation_change",
      data: { azimuth, elevation },
    }) 
  };

  nv.onClickToSegment = function (data: { mm3: number; mL: number; }) {
    model.send({
      event: "click_to_segment",
      data,
    })
  };

  nv.onClipPlaneChange = function (clipPlane: number[]) {
    model.send({
      event: "clip_plane_change",
      data: clipPlane,
    });
  }

  nv.onDocumentLoaded = function (document: niivue.NVDocument) {
    model.send({
      event: "document_loaded",
      data: {
        title: document.title || "",
        opts: document.opts || {},
        volumes: document.volumes.map((volume) => volume.id),
        meshes: document.meshes.map((mesh) => mesh.id),
      },
    })
  };

  nv.onImageLoaded = async function (volume: niivue.NVImage) {
    // Check if the volume is already in the backend
    const volumeID = volume.id;
    const volumeModels = await Promise.all(
      model.get("_volumes").map(async (v: string) => {
        const modelID = v.slice("IPY_MODEL_".length);
        const vmodel = await model.widget_manager.get_model(modelID);
        return vmodel;
      })
    );

    const backendVolumeIds = volumeModels.map((vmodel) => vmodel?.get("id") || "");

    if (!backendVolumeIds.includes(volumeID) && nv) {
      // Volume is new; create a new VolumeModel in the backend
      // volume.toUint8Array().slice().buffer for data
      const volumeData = {
        path: '<preloaded>',
        id: volume.id,
        name: volume.name,
        colormap: volume.colormap,
        opacity: volume.opacity,
        colorbar_visible: volume.colorbarVisible,
        cal_min: volume.cal_min,
        cal_max: volume.cal_max,
        // Include the index of the volume in nv.volumes
        index: nv.getVolumeIndexByID(volume.id),
      };
    
      // Send a custom message to the backend to add the volume with the index
      model.send({
        event: "add_volume",
        data: volumeData,
      });
    }

    // Existing code for handling image_loaded event
    model.send({
      event: "image_loaded",
      data: {
        id: volume.id,
      },
    });
  };

  nv.onDragRelease = function (params: niivue.DragReleaseParams) {
    model.send({
      event: "drag_release",
      data: {
        fracStart: params.fracStart,
        fracEnd: params.fracEnd,
        voxStart: params.voxStart,
        voxEnd: params.voxEnd,
        mmStart: params.mmStart,
        mmEnd: params.mmEnd,
        mmLength: params.mmLength,
        tileIdx: params.tileIdx,
        axCorSag: params.axCorSag,
      },
    })
  };

  nv.onFrameChange = function (volume: niivue.NVImage, frame: number) {
    model.send({
      event: "frame_change",
      data: {
        id: volume.id,
        frame,
      },
    })
  };

  nv.onIntensityChange = function (volume: niivue.NVImage) {
    model.send({
      event: "intensity_change",
      data: {
        id: volume.id,
      },
    })
  };

  nv.onLocationChange = function (location: any) {
    model.send({
      event: "location_change",
      data: {
        axCorSag: location.axCorSag,
        frac: location.frac,
        mm: location.mm,
        string: location.string || "",
        vox: location.vox,
        values: location.values,
        xy: location.xy,
      },
    })
  };

  nv.onMeshAddedFromUrl = function (meshOptions: any, mesh: niivue.NVMesh) {
    model.send({
      event: "mesh_added_from_url",
      data: {
        url: meshOptions.url,
        headers: meshOptions?.headers || {},
        mesh: {
          id: mesh.id,
          name: mesh.name,
          rgba255: Array.from(mesh.rgba255),
          opacity: mesh.opacity,
          visible: mesh.visible
        },
      },
    })
  };

  nv.onMeshLoaded = async function (mesh: niivue.NVMesh) {
    // Check if the mesh is already in the backend
    const meshID = mesh.id;
    const meshModels = await Promise.all(
        model.get("_meshes").map(async (m: string) => {
            const modelID = m.slice("IPY_MODEL_".length);
            const mmodel = await model.widget_manager.get_model(modelID);
            return mmodel;
        })
    );

    const backendMeshIds = meshModels.map((mmodel) => mmodel?.get("id") || "");
    console.log(backendMeshIds)

    if (!backendMeshIds.includes(meshID) && nv) {
        // Mesh is new; create a new MeshModel in the backend

        // Prepare layers data
        const layersData = mesh.layers.map((layer: any) => {
            if (!layer.id) {
              layer.id = uuidv4();
            }
            return {
                path: '<preloaded>',
                opacity: layer.opacity,
                colormap: layer.colormap,
                colormap_negative: layer.colormapNegative,
                use_negative_cmap: layer.useNegativeCmap,
                cal_min: layer.cal_min,
                cal_max: layer.cal_max,
                frame4D: layer.frame4D,
                id: layer.id,
            };
        });

        const meshData = {
            path: '<preloaded>',
            id: mesh.id,
            name: mesh.name,
            rgba255: Array.from(mesh.rgba255),
            opacity: mesh.opacity,
            visible: mesh.visible,
            layers: layersData,
            // Include the index of the mesh in nv.meshes
            index: nv.meshes.findIndex((m) => m.id === mesh.id),
        };

        // Send a custom message to the backend to add the mesh
        model.send({
            event: "add_mesh",
            data: meshData,
        });
    }

    // Existing code for handling mesh_loaded event
    model.send({
        event: "mesh_loaded",
        data: {
            id: mesh.id,
        },
    });
  };

  nv.onMouseUp = function (data: any) {
    model.send({
      event: "mouse_up",
      data: {
        mouse_button_right_down: data.mouseButtonRightDown,
        mouse_button_center_down: data.mouseButtonCenterDown,
        is_dragging: data.isDragging,
        mouse_pos: data.mousePos,
        frac_pos: data.fracPos
      },
    })
  };

  nv.onVolumeAddedFromUrl = function (imageOptions: any, volume: niivue.NVImage) {
    model.send({
      event: "volume_added_from_url",
      data: {
        url: imageOptions.url,
        headers: imageOptions?.headers || {},
        volume: {
          id: volume.id,
          name: volume.name,
          colormap: volume.colormap,
          opacity: volume.opacity,
          colorbar_visible: volume.colorbarVisible,
          cal_min: volume.cal_min,
          cal_max: volume.cal_max,
        }
      },
    })
  };

  nv.onVolumeUpdated = function () {
    model.send({
      event: "volume_updated",
    })
  };
}

function attachModelEventHandlers(nv: niivue.Niivue, model: Model, disposer: Disposer) {
  model.on("change:_volumes", () => {
    if (nv.canvas) {
      render_volumes(nv, model, disposer)
    }
  });
  model.on("change:_meshes", () => {
    if (nv.canvas) {
      render_meshes(nv, model, disposer)
    }
  });

  // Any time we change the options, we need to update the nv object
  // and redraw the scene.
  model.on("change:_opts", () => {
    console.log('Updating opts callback');
    // Update nv.opts with the new options
    nv.document.opts = { ...nv.opts, ...model.get("_opts") };
    nv.updateGLVolume();
  });

  model.on("change:background_masks_overlays", () => {
    let backgroundMasksOverlays = model.get("background_masks_overlays");
    if (typeof backgroundMasksOverlays === "boolean") {
      nv.backgroundMasksOverlays = Number(backgroundMasksOverlays)
      nv.updateGLVolume();
    }
  });

  // Handle custom messages from the backend
  model.on("msg:custom", (payload: {type: string, data: any}) => {
    const { type, data } = payload;
    switch (type) { 
      case "save_scene":
        nv.saveScene(data);
        break;
      case "add_colormap":
        nv.addColormap(data.name, data.cmap);
        break;
      case "set_gamma":
        nv.setGamma(data);
        break;
      case "set_clip_plane":
        nv.setClipPlane(data);
        break;
      case "set_mesh_shader":
        nv.setMeshShader(data.mesh_id, data.shader);
        break;
    }
  });
}