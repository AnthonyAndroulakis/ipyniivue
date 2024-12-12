# ipyniivue-test

A Jupyter Widget for [Niivue](https://github.com/niivue/niivue) based on
anywidget.

## Experimental testing version
whats been added:
- on-event callbacks (from https://niivue.github.io/niivue/devdocs/classes/Niivue.html)
- id + name for volumes syncing up (so you can do nv.get_volume_index_by_id(volume.id))
- nv.save_scene
- nv.get_volume_index_by_id

## extra notes
- on_image_loaded is a little more involved since the callback takes in 1 argument of type niivue.Volume:
    ![onimageloaded](https://i.imgur.com/wLIiZWk.png)

    which functions like this, in the code:
    ```
    python
      load volumes

    ->

    ts niivue.load_volumes
      -> save model state w/id + name
      -> niivue.onimageloaded -> "image_loaded" msg

    ->

    python
      on_image_loaded -> get_volume_index_by_id
    ```

    and works because the onimageloaded callback is called at the end of volume loading:
      from niivue/packages/niivue/src/niivue/index.ts:
        ```ts
        addVolume(volume: NVImage): void {
          this.volumes.push(volume)
          const idx = this.volumes.length === 1 ? 0 : this.volumes.length - 1
          this.setVolume(volume, idx)
          this.onImageLoaded(volume)
          log.debug('loaded volume', volume.name)
          log.debug(volume)
        }
        ```
