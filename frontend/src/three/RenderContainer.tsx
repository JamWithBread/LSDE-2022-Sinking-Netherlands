import React from 'react'

import Renderer from "./Renderer";
import Toolbar from "./Toolbar";
import {useState} from "react";

function RenderContainer() {
    const [isRenderingMeshAHN3, setRenderingMeshAHN3] = useState(true)
    const [isRenderingMeshAHN2, setRenderingMeshAHN2] = useState(true)
    const [isRenderingWater, setRenderingWater] = useState(false)
    const [waterHeight, setWaterHeight] = useState(0.0)

    return (
        <div style={{display: 'flex'}}>
            <Toolbar
                isRenderingMeshAHN3={isRenderingMeshAHN3}
                toggleRenderingMeshAHN3={() => setRenderingMeshAHN3(!isRenderingMeshAHN3)}
                isRenderingMeshAHN2={isRenderingMeshAHN2}
                toggleRenderingMeshAHN2={() => setRenderingMeshAHN2(!isRenderingMeshAHN2)}
                isRenderingWater={isRenderingWater}
                toggleRenderingWater={() => setRenderingWater(!isRenderingWater)}
                waterHeight={waterHeight}
                setWaterHeight={(height) => setWaterHeight(height)}
            />
            <Renderer
                isRenderingMeshAHN3={isRenderingMeshAHN3}
                isRenderingMeshAHN2={isRenderingMeshAHN2}
                isRenderingWater={isRenderingWater}
                waterHeight={waterHeight}
            />
        </div>
    )
}

export default RenderContainer
