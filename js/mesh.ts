import * as niivue from "@niivue/niivue";
import * as lib from "./lib.ts";
import type { MeshModel, MeshLayerModel, Model } from "./types.ts";

/**
 * Set up event listeners to handle changes to the layer properties.
 * Returns a function to clean up the event listeners.
 */
function setup_layer_property_listeners(
    layer: any,
    layerModel: MeshLayerModel,
    mesh: niivue.NVMesh,
    nv: niivue.Niivue
): () => void {

    function opacity_changed() {
        layer.opacity = layerModel.get('opacity');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function colormap_changed() {
        layer.colormap = layerModel.get('colormap');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function colormap_negative_changed() {
        layer.colormapNegative = layerModel.get('colormap_negative');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function use_negative_cmap_changed() {
        layer.useNegativeCmap = layerModel.get('use_negative_cmap');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function cal_min_changed() {
        layer.cal_min = layerModel.get('cal_min');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function cal_max_changed() {
        layer.cal_max = layerModel.get('cal_max');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    function frame4D_changed() {
        layer.frame4D = layerModel.get('frame4D');
        mesh.updateMesh(nv.gl);
        nv.updateGLVolume();
    }

    // Set up the event listeners
    layerModel.on('change:opacity', opacity_changed);
    layerModel.on('change:colormap', colormap_changed);
    layerModel.on('change:colormap_negative', colormap_negative_changed);
    layerModel.on('change:use_negative_cmap', use_negative_cmap_changed);
    layerModel.on('change:cal_min', cal_min_changed);
    layerModel.on('change:cal_max', cal_max_changed);
    layerModel.on('change:frame4D', frame4D_changed);

    // Return a cleanup function
    return () => {
        layerModel.off('change:opacity', opacity_changed);
        layerModel.off('change:colormap', colormap_changed);
        layerModel.off('change:colormap_negative', colormap_negative_changed);
        layerModel.off('change:use_negative_cmap', use_negative_cmap_changed);
        layerModel.off('change:cal_min', cal_min_changed);
        layerModel.off('change:cal_max', cal_max_changed);
        layerModel.off('change:frame4D', frame4D_changed);
    };
}

/**
 * Set up event listeners to handle changes to the mesh properties.
 * Returns a function to clean up the event listeners.
 */
function setup_mesh_property_listeners(
    mesh: niivue.NVMesh,
    mmodel: MeshModel,
    nv: niivue.Niivue
): () => void {
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

    // Return a function to remove the event listeners
    return () => {
        mmodel.off("change:opacity", opacity_changed);
        mmodel.off("change:rgba255", rgba255_changed);
        mmodel.off("change:visible", visible_changed);
        mmodel.off("change:colormap_invert", colormap_invert_changed);
    };
}

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
    let layerCleanupFunctions: (() => void)[] = [];

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
    }

    // Gather MeshLayer models
    const layerIDs = mmodel.get("layers");

    if (layerIDs.length > 0) {
        // Use gather_models to fetch the MeshLayerModel instances
        layerModels = await lib.gather_models<MeshLayerModel>(
            mmodel,
            layerIDs,
        );

        // Add layers to the mesh
        layerModels.forEach((layerModel, layerIndex) => {
            let layer: any;
            if (layerModel.get("path").name === "<preloaded>") {
                layer = mesh.layers[layerIndex];
            } else {
                layer = niivue.NVMeshLoaders.readLayer(
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
                mesh.layers.push(layer);
            }
            if (!layer) {
                return;
            }

            // Set up event listeners for the layer properties
            const cleanup_layer_listeners = setup_layer_property_listeners(layer, layerModel, mesh, nv);
            layerCleanupFunctions.push(cleanup_layer_listeners);
        });
    }

    mesh.updateMesh(nv.gl);

    mmodel.set("id", mesh.id);
    mmodel.set("name", mesh.name);
    mmodel.save_changes();

    // Handle changes to the mesh properties
    const cleanup_mesh_listeners = setup_mesh_property_listeners(mesh, mmodel, nv);

    return [
        mesh,
        () => {
            // Remove event listeners for mesh properties
            cleanup_mesh_listeners();

            // Remove event listeners for layer properties
            layerCleanupFunctions.forEach(cleanup => cleanup());
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
            if (mmodel.get("path").name !== "<preloaded>") {
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