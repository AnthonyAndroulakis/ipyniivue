import type { AnyModel } from "@anywidget/types";

interface File {
	name: string;
	data: DataView;
}

export type VolumeModel = { model_id: string } & AnyModel<{
	path: File;
	id: string;
	name: string;
	colormap: string;
	opacity: number;
	visible: boolean;
	colorbar_visible: boolean;
	cal_min?: number;
	cal_max?: number;

	colormap_invert: boolean;
}>;

export type MeshLayerModel = { model_id: string } & AnyModel<{
    path: File;
    opacity: number;
    colormap: string;
    colormap_negative: string;
    use_negative_cmap: boolean;
    cal_min: number;
    cal_max: number;
    frame4D: number;
}>;

export type MeshModel = { model_id: string } & AnyModel<{
    path: File;
    id: string;
    name: string;
    rgba255: Array<number>;
    opacity: number;
    layers: Array<string>;
    visible: boolean;

    colormap_invert: boolean;
}>;

export type Model = AnyModel<{
	height: number;
	_volumes: Array<string>;
	_meshes: Array<string>;
	_opts: Record<string, unknown>;

	background_masks_overlays: boolean;
	id: string;
}>;
