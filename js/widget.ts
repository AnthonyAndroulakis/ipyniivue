import * as niivue from "@niivue/niivue";
import type { Model } from "./types.ts";

import { Disposer } from "./lib.ts";
import { render_meshes } from "./mesh.ts";
import { render_volumes } from "./volume.ts";

declare var globalThis: any;

if (!globalThis.nv) {
  globalThis.nv = new niivue.Niivue();
}

const nv: niivue.Niivue = globalThis.nv;
globalThis.eventHandlersInstalled = false;

export default {
	async render({ model, el }: { model: Model; el: HTMLElement }) {
		const disposer = new Disposer();
		const canvas = document.createElement("canvas");
		const container = document.createElement("div");
		container.style.height = `${model.get("height")}px`;
		container.appendChild(canvas);
		el.appendChild(container);

    nv.attachToCanvas(canvas);


    if (!globalThis.eventHandlersInstalled) {
      globalThis.eventHandlersInstalled = true;

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

        if (!backendVolumeIds.includes(volumeID)) {
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

        if (!backendMeshIds.includes(meshID)) {
          // Mesh is new; create a new MeshModel in the backend
          const meshData = {
            path: '<preloaded>',
            id: mesh.id,
            name: mesh.name,
            rgba255: Array.from(mesh.rgba255),
            opacity: mesh.opacity,
            layers: [], // Add layers if any
            visible: mesh.visible,
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

      // Load initial volumes and meshes
      await render_volumes(nv, model, disposer);
      await render_meshes(nv, model, disposer);
    }
	
		model.on("change:_volumes", () => render_volumes(nv, model, disposer));
		model.on("change:_meshes", () => render_meshes(nv, model, disposer));

		// Any time we change the options, we need to update the nv object
		// and redraw the scene.
		model.on("change:_opts", () => {
			nv.document.opts = { ...nv.opts, ...model.get("_opts") };
			nv.drawScene();
			nv.updateGLVolume();
		});
		model.on("change:height", () => {
			container.style.height = `${model.get("height")}px`;
		});

    // Handle custom messages from the backend
    model.on("msg:custom", (payload: {type: string, data: any}) => {
      const { type, data } = payload;
      switch (type) { 
        case "save_scene":
          nv.saveScene(data);
          break;
      }
    });

		// All the logic for cleaning up the event listeners and the nv object
		return () => {
			disposer.disposeAll();
			model.off("change:_volumes");
			model.off("change:_opts");
		};
	},
};
