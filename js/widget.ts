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
		nv.onImageLoaded = function (volume: niivue.NVImage) {
			model.send({
				event: "image_loaded",
				data: {
					name: volume.name,
					colormap: volume.colormap,
					opacity: volume.opacity,
					cal_min: volume.cal_min,
					cal_max: volume.cal_max,
					trustCalMinMax: volume.trustCalMinMax,
					percentileFrac: volume.percentileFrac,
					ignoreZeroVoxels: volume.ignoreZeroVoxels,
					useQFormNotSForm: volume.useQFormNotSForm,
					colormapNegative: volume.colormapNegative,
					frame4D: volume.frame4D,
				},
			});
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

		// All the logic for cleaning up the event listeners and the nv object
		return () => {
			disposer.disposeAll();
			model.off("change:_volumes");
			model.off("change:_opts");
		};
	},
};
