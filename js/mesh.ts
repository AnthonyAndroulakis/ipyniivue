import * as niivue from "@niivue/niivue";
import * as lib from "./lib.ts";
import type { MeshModel, MeshLayerModel, Model } from "./types.ts";

/**
 * Create a new NVMesh and attach the necessary event listeners
 * Returns the NVMesh and a cleanup function that removes the event listeners.
 */
async function create_mesh(
    nv: niivue.Niivue,
    mmodel: MeshModel,
): Promise<[niivue.NVMesh, () => void]> {
    let mesh: niivue.NVMesh;
	let layerModels: MeshLayerModel[] = [];
    if (mmodel.get("path").name === "<preloaded>") {
        let idx = nv.meshes.findIndex((m) => m.id === mmodel.get("id"));
        mesh = nv.meshes[idx];
    } else {
        mesh = niivue.NVMesh.readMesh(
            mmodel.get("path").data.buffer,
            mmodel.get("path").name,
            nv.gl,
            mmodel.get("opacity"),
            new Uint8Array(mmodel.get("rgba255")),
            mmodel.get("visible"),
        );

		// Gather MeshLayer models
		const layerIDs = mmodel.get("layers");

		if (layerIDs.length > 0) {
			// Use gather_models to fetch the MeshLayerModel instances
			layerModels = await lib.gather_models<MeshLayerModel>(
				mmodel,
				layerIDs,
			);

			// Add layers to the mesh
			layerModels.forEach((layerModel) => {
				let layer = niivue.NVMeshLoaders.readLayer(
					layerModel.get("path").name,
					layerModel.get("path").data.buffer,
					mesh,
					layerModel.get("opacity") ?? 0.5,
					layerModel.get("colormap") ?? "warm",
					layerModel.get("colormap_negative") ?? "winter",
					layerModel.get("use_negative_cmap") ?? false,
					layerModel.get("cal_min") ?? null,
					layerModel.get("cal_max") ?? null,
					layerModel.get("frame4D") ?? 0,
				);
                if (!layer) {
                    return;
                }
                mesh.layers.push(layer);

				// Observe changes to the layer propertie
				// Handling 'opacity'
				layerModel.on('change:opacity', () => {
                    layer.opacity = layerModel.get('opacity');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'colormap'
				layerModel.on('change:colormap', () => {
                    layer.colormap = layerModel.get('colormap');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'colormap_negative' (mapped to 'colormapNegative')
				layerModel.on('change:colormap_negative', () => {
                    layer.colormapNegative = layerModel.get('colormap_negative');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'use_negative_cmap' (mapped to 'useNegativeCmap')
				layerModel.on('change:use_negative_cmap', () => {
                    layer.useNegativeCmap = layerModel.get('use_negative_cmap');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'cal_min'
				layerModel.on('change:cal_min', () => {
                    layer.cal_min = layerModel.get('cal_min');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'cal_max'
				layerModel.on('change:cal_max', () => {
                    layer.cal_max = layerModel.get('cal_max');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

				// Handling 'frame4D'
				layerModel.on('change:frame4D', () => {
                    layer.frame4D = layerModel.get('frame4D');
                    mesh.updateMesh(nv.gl);
					nv.updateGLVolume();
				});

			});
		}
    }

    mesh.updateMesh(nv.gl);

    mmodel.set("id", mesh.id);
    mmodel.set("name", mesh.name);
    mmodel.save_changes();

    // Handle changes to the mesh properties
    function opacity_changed() {
        mesh.opacity = mmodel.get("opacity");
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }
    function rgba255_changed() {
        mesh.rgba255 = new Uint8Array(mmodel.get("rgba255"));
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }
    function visible_changed() {
        mesh.visible = mmodel.get("visible");
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }
    function colormap_invert_changed() {
        mesh.colormapInvert = mmodel.get("colormap_invert");
        nv.updateGLVolume();
    }

    mmodel.on("change:opacity", opacity_changed);
    mmodel.on("change:rgba255", rgba255_changed);
    mmodel.on("change:visible", visible_changed);
    mmodel.on("change:colormap_invert", colormap_invert_changed);

    return [
        mesh,
        () => {
            // Remove event listeners for mesh properties
            mmodel.off("change:opacity", opacity_changed);
            mmodel.off("change:rgba255", rgba255_changed);
            mmodel.off("change:visible", visible_changed);
            mmodel.off("change:colormap_invert", colormap_invert_changed);

            // Remove event listeners for layer properties
            layerModels.forEach((layerModel) => {
                const properties = [
                    "opacity",
                    "colormap",
                    "colormap_negative",
                    "use_negative_cmap",
                    "cal_min",
                    "cal_max",
                    "frame4D",
                ];
                properties.forEach((prop) => {
                    layerModel.off(`change:${prop}`);
                });
            });
        },
    ];
}

export async function render_meshes(
    nv: niivue.Niivue,
    model: Model,
    disposer: lib.Disposer,
) {
    const mmodels = await lib.gather_models<MeshModel>(
        model,
        model.get("_meshes"),
    );

    const backend_meshes = mmodels;
    const frontend_meshes = nv.meshes;

    const backend_mesh_map = new Map<string, MeshModel>();
    const frontend_mesh_map = new Map<string, niivue.NVMesh>();

    // create backend mesh map
    backend_meshes.forEach((mmodel, index) => {
        const id = mmodel.get("id") || `__temp_id__${index}`;
        backend_mesh_map.set(id, mmodel);
    });

    // create frontend mesh map
    frontend_meshes.forEach((mesh, index) => {
        const id = mesh.id || `__temp_id__${index}`;
        frontend_mesh_map.set(id, mesh);
    });

    // add meshes
    for (const [id, mmodel] of backend_mesh_map.entries()) {
        if (
            !frontend_mesh_map.has(id)
            || mmodel.get("id") === ""
            || (mmodel.get("path").name === "<preloaded>"
                && nv.meshes.findIndex((m) => m.id === mmodel.get("id")) !== -1)
        ) {
            // Create and add the mesh
            const [mesh, cleanup] = await create_mesh(nv, mmodel);
            disposer.register(mesh, cleanup);
            if (mmodel.get("path").name === "<preloaded>") {
                nv.addMesh(mesh);
            }
        }
    }

    // remove meshes
    for (const [id, mesh] of frontend_mesh_map.entries()) {
        if (!backend_mesh_map.has(id)) {
            // Remove mesh
            nv.removeMesh(mesh);
            disposer.dispose(mesh.id);
        }
    }

    // Match frontend mesh order to backend order
    const new_meshes_order: niivue.NVMesh[] = [];
    backend_meshes.forEach((mmodel) => {
        const id = mmodel.get("id") || "";
        const mesh = nv.meshes.find((m) => m.id === id);
        if (mesh) {
            new_meshes_order.push(mesh);
        }
    });
    nv.meshes = new_meshes_order;
    nv.updateGLVolume();
}