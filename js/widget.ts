import * as niivue from "@niivue/niivue";
import type { Model } from "./types.ts";

import { Disposer } from "./lib.ts";
import { render_meshes } from "./mesh.ts";
import { render_volumes } from "./volume.ts";

export default {
	async render({ model, el }: { model: Model; el: HTMLElement }) {
		const disposer = new Disposer();
		const canvas = document.createElement("canvas");
		const container = document.createElement("div");
		container.style.height = `${model.get("height")}px`;
		container.appendChild(canvas);
		el.appendChild(container);

		const nv = new niivue.Niivue(model.get("_opts") ?? {});
		nv.attachToCanvas(canvas);

		// Attach Niivue event handlers
    nv.onAzimuthElevationChange = function (azimuth: number, elevation: number) {
      model.send({
        event: "azimuth_elevation_change",
        data: { azimuth, elevation },
      });
    }

    nv.onClickToSegment = function (data: { mm3: number; mL: number; }) {
      model.send({
        event: "click_to_segment",
        data,
      });
    }

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
          title: document.title,
          opts: document.opts,
          volumes: document.volumes.map((volume) => volume.id),
          meshes: document.meshes.map((mesh) => mesh.id),
        },
      });
    }
    
		nv.onImageLoaded = function (volume: niivue.NVImage) {
			model.send({
				event: "image_loaded",
				data: {
          id: volume.id,
				},
			})
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
          string: location.string,
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
          mesh: mesh.id,
        },
      })
    };

    nv.onMeshLoaded = function (mesh: niivue.NVMesh) {
      model.send({
        event: "mesh_loaded",
        data: {
          id: mesh.id,
        },
      })
    };

    nv.onMouseUp = function (data: any) {
      model.send({
        event: "mouse_up",
        data,
      })
    };

    nv.onVolumeAddedFromUrl = function (imageOptions: any, volume: niivue.NVImage) {
      model.send({
        event: "volume_added_from_url",
        data: {
          url: imageOptions.url,
          headers: imageOptions?.headers || {},
          volume: volume.id,
        },
      })
    };

    nv.onVolumeUpdated = function () {
      model.send({
        event: "volume_updated",
      })
    };

		await render_volumes(nv, model, disposer);
		model.on("change:_volumes", () => render_volumes(nv, model, disposer));
		await render_meshes(nv, model, disposer);
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
