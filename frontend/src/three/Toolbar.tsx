import React from 'react'

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

function Toolbar(props: ToolbarProps) {
    function handleSliderChange(e: React.ChangeEvent<HTMLInputElement>) {
        props.setWaterHeight(parseFloat(e.target.value)/1000)
    }
    return (
        <div>
            <div>
                <button onClick={props.toggleRenderingMeshAHN3}>
                    Toggle Mesh AHN3
                </button>
            </div>
            <div>
                <button onClick={props.toggleRenderingMeshAHN2}>
                    Toggle Mesh AHN2
                </button>
            </div>
            <div>
                <button onClick={props.toggleRenderingWater}>
                    Toggle Water
                </button>
            </div>
            <div className="slidecontainer">
                <input type="range" min="0" max="100" className="slider"
                       value={props.waterHeight}
                       onChange={handleSliderChange}/>
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
