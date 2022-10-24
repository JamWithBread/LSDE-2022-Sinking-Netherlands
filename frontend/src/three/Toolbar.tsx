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
        props.setWaterHeight(parseFloat(e.target.value)/100)
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
                <input type="range" min="0" max="100" className="slider" id="myRange"
                       value={props.waterHeight}
                       onChange={handleSliderChange}/>
            </div>
        </div>
    )
}

export default Toolbar
