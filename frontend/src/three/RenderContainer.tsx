import React from 'react'

import Renderer from "./Renderer";
import Toolbar from "./Toolbar";
import {useState} from "react";

function RenderContainer() {
    const [isRenderingMesh1, setRenderingMesh1] = useState(false);

    return (
        <div style={{display: 'flex'}}>
            <Toolbar
                isRenderingMesh1={isRenderingMesh1}
                toggleRenderingMesh1={() => setRenderingMesh1(!isRenderingMesh1)}
            />
            <Renderer
                isRenderingMesh1={isRenderingMesh1}
            />
        </div>
    )
}

export default RenderContainer
