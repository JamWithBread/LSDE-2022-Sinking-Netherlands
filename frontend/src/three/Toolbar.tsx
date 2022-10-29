import React from 'react'
import metadata_ahn3 from "../chunks/ahn3/_metadata.json";

type ToolbarProps = {
    isRenderingMeshAHN3: boolean,
    toggleRenderingMeshAHN3: () => void,
    isRenderingMeshAHN2: boolean,
    toggleRenderingMeshAHN2: () => void,
    isRenderingWater: boolean,
    toggleRenderingWater: () => void,
    waterHeight: number,
    setWaterHeight: (arg0: number) => void,
}
const minY = metadata_ahn3.minY
const maxY = metadata_ahn3.maxY
const yRange = maxY - minY

function Toolbar(props: ToolbarProps) {
    function handleSliderChange(e: React.ChangeEvent<HTMLInputElement>) {
        props.setWaterHeight((parseFloat(e.target.value)))
    }

    return (
        <div>
            <div>
                <button style={{opacity: (props.isRenderingMeshAHN3) ? 1 : 0.5}}
                        onClick={props.toggleRenderingMeshAHN3}>
                    Toggle Mesh AHN3
                </button>
            </div>
            <div>
                <button style={{opacity: (props.isRenderingMeshAHN2) ? 1 : 0.5}}
                        onClick={props.toggleRenderingMeshAHN2}>
                    Toggle Mesh AHN2
                </button>
            </div>
            <div>
                <button style={{opacity: (props.isRenderingWater) ? 1 : 0.5}}
                        onClick={props.toggleRenderingWater}>
                    Toggle Water
                </button>
            </div>
            <div>
                <input type="range" min="0" max="100" className="slider"
                       value={props.waterHeight}
                       onChange={handleSliderChange}/>
                <p> Current water
                    level: {props.isRenderingWater ? (((props.waterHeight / 100) - 0.5) * (yRange)).toFixed(2) : "-"}</p>
            </div>
            <div>
                <p><code>W</code> Up</p>
                <p><code>A</code> Left</p>
                <p><code>S</code> Down</p>
                <p><code>D</code> Right</p>
                <p><code>Q</code> Rotate left</p>
                <p><code>E</code> Rotate right</p>
                <p><code>&#8593;</code> Zoom in</p>
                <p><code>&#8595;</code> Zoom out</p>
                <p><code>&#8592;</code> Tilt left</p>
                <p><code>&#8594;</code> Tilt right</p>
            </div>
            <footer>
                <p>GROUP 02</p>
                <p>The Sinking Netherlands</p>

            </footer>
        </div>
    )
}

export default Toolbar
