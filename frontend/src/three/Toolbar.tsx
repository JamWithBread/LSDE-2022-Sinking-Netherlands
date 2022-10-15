import React from 'react'

type ToolbarProps = {
    isRenderingMesh1: boolean,
    toggleRenderingMesh1: () => void,
}

function Toolbar(props: ToolbarProps) {
    return (
        <div>
            <button onClick={props.toggleRenderingMesh1}>
                Toggle
            </button>
        </div>
    )
}

export default Toolbar
