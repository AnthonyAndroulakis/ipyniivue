import * as niivue from "@niivue/niivue";
import * as lib from "./lib.ts";
import type { MeshModel, Model } from "./types.ts";

/**
 * Create a new NVMesh and attach the necessary event listeners
 * Returns the NVMesh and a cleanup function that removes the event listeners.
 */
function create_mesh(
	nv: niivue.Niivue,
	mmodel: MeshModel,
): [niivue.NVMesh, () => void] {
	let mesh: niivue.NVMesh;
	if (mmodel.get("path").name === "<preloaded>") { 
		let idx = nv.meshes.findIndex((m) => m.id === mmodel.get("id"));
		mesh = nv.meshes[idx];
	} else {
		mesh = niivue.NVMesh.readMesh(
			mmodel.get("path").data.buffer, // buffer
			mmodel.get("path").name, // name (used to identify the mesh)
			nv.gl, // gl
			mmodel.get("opacity"), // opacity
			new Uint8Array(mmodel.get("rgba255")), // rgba255
			mmodel.get("visible"), // visible
		);
		for (const layer of mmodel.get("layers")) {
			// https://github.com/niivue/niivue/blob/10d71baf346b23259570d7b2aa463749adb5c95b/src/nvmesh.ts#L1432C5-L1455C6
			niivue.NVMeshLoaders.readLayer(
				layer.path.name,
				layer.path.data.buffer,
				mesh,
				layer.opacity ?? 0.5,
				layer.colormap ?? "warm",
				layer.colormapNegative ?? "winter",
				layer.useNegativeCmap ?? false,
				layer.cal_min ?? null,
				layer.cal_max ?? null,
			);
		}
	}

	mmodel.set("id", mesh.id);
	mmodel.set("name", mesh.name);
	mmodel.save_changes();

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
	mmodel.on("change:opacity", opacity_changed);
	mmodel.on("change:rgba255", rgba255_changed);
	mmodel.on("change:visible", visible_changed);
	return [
		mesh,
		() => {
			mmodel.off("change:opacity", opacity_changed);
			mmodel.off("change:rgba255", rgba255_changed);
			mmodel.off("change:visible", visible_changed);
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
  
	// create backend mesh map, use 'id' value if available, otherwise use temp key
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
			|| (mmodel.get("path").name === "<preloaded>" && nv.meshes.findIndex((m) => m.id === mmodel.get("id")) !== -1) // getting mesh index is for extra verification
		) {
			// case: mesh is in backend but not in frontend, or id is empty
			// result: add mesh
			const [mesh, cleanup] = create_mesh(nv, mmodel);
			disposer.register(mesh, cleanup);
			nv.addMesh(mesh);
		}
	}
  
	// remove meshes
	for (const [id, mesh] of frontend_mesh_map.entries()) {
		if (!backend_mesh_map.has(id)) {
			// case: mesh is in frontend but not in backend
			// result: remove mesh
			nv.removeMesh(mesh);
			disposer.dispose(mesh.id);
		}
	}
  
	// match frontend mesh order to backend order
	const new_meshes_order: niivue.NVMesh[] = [];
	backend_meshes.forEach((mmodel) => {
		const id = mmodel.get("id") || "";
		const mesh = nv.meshes.find((m) => m.id === id);
		if (mesh) {
			new_meshes_order.push(mesh);
		} else {
			// handle case where mesh was just added and id isn't set yet
			const temp_index = backend_meshes.indexOf(mmodel);
			const temp_id = `__temp_id__${temp_index}`;
			const mesh_temp = nv.meshes.find((m) => m.id === temp_id);
			if (mesh_temp) {
				new_meshes_order.push(mesh_temp);
			}
		}
	});
  
	nv.meshes = new_meshes_order;
	nv.updateGLVolume();
}