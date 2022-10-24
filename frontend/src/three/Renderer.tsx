import React, {useEffect, useRef, useState} from 'react'
import * as THREE from 'three'
import {FlyControls} from './Control'
import {shade} from "../utils/color"
import axios from 'axios'

const cameraFOV = 75
const cameraNear = 0.1
const cameraFar = 1000

const minX = -1
const minZ = -1
const maxX = 1
const maxZ = 1

const columns = 64
const rows = 64
const chunks = columns * rows

const columnSize = (maxX - minX) / columns
const rowSize = (maxZ - minZ) / rows

const toFetch: ChunkBufferInfo[] = []
type ChunkBufferInfo = {
    id: string,
    column: number,
    row: number,
    level: number,
    isValid: boolean,
    minBufferIdx: number,
}

const MAX_TRIANGLES_PER_CHUNK = 512
const geometry = new THREE.BufferGeometry();
const BUFFER_SIZE_PER_CHUNK = MAX_TRIANGLES_PER_CHUNK * 9
const positions = new Float32Array(BUFFER_SIZE_PER_CHUNK * chunks); // 3 vertices per point
const chunkInfoMap: { [k: string]: ChunkBufferInfo } = {}

let counter = 0
for (let i = 0; i < columns; i++) {
    for (let j = 0; j < rows; j++) {
        const level = 0
        const chunkId = createChunkId(i, j)
        chunkInfoMap[chunkId] = {
            id: chunkId,
            column: i,
            row: j,
            level: -1,
            isValid: true,
            minBufferIdx: counter * BUFFER_SIZE_PER_CHUNK,
        }
        counter++
    }
}


geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

const material = new THREE.ShaderMaterial({
    uniforms: {
        color1: {
            value: new THREE.Color(0x006994),
        },
        color2: {
            value: new THREE.Color(0xf48037)
        }
    },
    vertexShader: `
            varying vec3 positionVertex;

            void main() {
                positionVertex = position;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
    fragmentShader: `
            uniform vec3 color1;
            uniform vec3 color2;

            varying vec3 positionVertex;

            void main() {
                gl_FragColor = vec4(mix(color1, color2, pow(positionVertex.y, 0.4)), 1.0);
            }
        `,
    side: THREE.DoubleSide
})

// const material = new THREE.MeshPhongMaterial({
//     color: 0xFF0000,    // red (can also use a CSS color string here)
//     flatShading: true,
// });

const mesh = new THREE.Mesh(geometry, material)

const mesh1Name = "mesh1"

type RenderProps = {
    isRenderingMesh1: boolean;
}

type TrackedObjects = {
    [mesh1Name]?: THREE.Object3D;
}

function Renderer(props: RenderProps) {
    const rendererDivRef = useRef<HTMLDivElement>(null)
    const [trackedObjects, setTrackedObjects] = useState<TrackedObjects | null>(null)

    useEffect(() => {
        const res = initScene(rendererDivRef)
        setTrackedObjects(res.trackedObjects)

        return () => {
            res.cleanup()
        };
    }, []);
    useEffect(() => {
        if (trackedObjects === null) {
            return
        }
        const mesh1 = trackedObjects[mesh1Name]
        if (typeof mesh1 === 'undefined') {
            return
        }
        mesh1.visible = !mesh1.visible
    }, [props.isRenderingMesh1])
    return (
        <div ref={rendererDivRef}>

        </div>
    )
}

function initScene(ref: React.RefObject<HTMLElement>): { trackedObjects: TrackedObjects, cleanup: () => void } {
    let width = window.innerWidth * 0.9
    let height = window.innerHeight
    const scene = new THREE.Scene()

    const camera = new THREE.PerspectiveCamera(
        cameraFOV,
        width / height,
        cameraNear,
        cameraFar
    )
    const renderer = new THREE.WebGLRenderer()
    const controls = new FlyControls(camera, renderer.domElement)
    const clock = new THREE.Clock()

    controls.movementSpeed = 5;
    controls.domElement = renderer.domElement;
    controls.rollSpeed = Math.PI / 3;

    renderer.setSize(width, height)

    const htmlEl = ref.current
    if (htmlEl == null) {
        console.error("rendererDivRef is null; can't mount threejs renderer to it")
        return {
            trackedObjects: {},
            cleanup: () => {
            }
        }
    }
    htmlEl.appendChild(renderer.domElement)

    const skyboxMesh = createSkyboxMesh()
    scene.add(skyboxMesh);

    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);

    const [mesh1, edges1] = createMesh(
        mesh1Name
    )

    scene.add(mesh1)
    scene.add(edges1)

    camera.position.z = 5

    function animate() {
        updateChunks(camera.position.x, camera.position.y, camera.position.z)
        const chunkToFetch = toFetch.pop()
        if (chunkToFetch !== undefined) {
            fetchChunk(chunkToFetch.id, chunkToFetch.level).then(positions => updateChunk(chunkToFetch, positions))
        }

        requestAnimationFrame(animate)
        const delta = clock.getDelta()
        controls.update(delta)
        renderer.render(scene, camera)


    }

    animate()


    return {
        trackedObjects: {
            [mesh1Name]: mesh1
        },
        cleanup: () => {
            htmlEl.removeChild(renderer.domElement)
        }
    }
}

function createSkyboxMesh() {
    const baseUrl = process.env.PUBLIC_URL + "/skybox/galaxy/galaxy";
    const fileType = ".png";
    const sides = ["+Z", "-Z", "+Y", "-Y", "+X", "-X"];
    const pathStrings = sides.map(side => baseUrl + side + fileType)
    const materialArray = pathStrings.map(image =>
        new THREE.MeshBasicMaterial({
            map: new THREE.TextureLoader().load(
                image,
                undefined,
                undefined,
                function (err) {
                    console.error('An error happened.')
                    console.log(err)
                }
            ),
            side: THREE.BackSide
        })
    )
    const geometry = new THREE.BoxGeometry(cameraFar, cameraFar, cameraFar)
    const skyboxMesh = new THREE.Mesh(geometry, materialArray)
    return skyboxMesh
}

function updateChunk(chunkInfo: ChunkBufferInfo, positions_chunk?: Float32Array) {
    if (positions_chunk === undefined) {
        // not all chunks have data, e.g. it is water for now we just try to get these chunks anyway and get a 404 which will make positions be undefined
        // we might be able to handle this in a better way
        chunkInfo.isValid = false
        return
    }

    const positions_current = mesh.geometry.attributes.position.array;

    const start = chunkInfo.minBufferIdx
    const endOfPositions = chunkInfo.minBufferIdx + positions_chunk.length
    const end = chunkInfo.minBufferIdx + BUFFER_SIZE_PER_CHUNK
    // console.log("start " + (start))
    // console.log("positions_length " + (endOfPositions - start))
    // console.log(positions_chunk)
    if (start % 9 !== 0) {
        console.error("start should be divisible by 9: " + start)
        return
    }
    for (let i = start; i < endOfPositions; i++) {
        // @ts-ignore
        positions_current[i] = positions_chunk[i - start]
        // console.log(i-start)
    }
    // for (let i = 0; i < positions_chunk.length; i++) {
    //     // @ts-ignore
    //     positions_current[i] = positions_chunk[i]
    // }
    // TODO setting to 0 is unnecessary if we're zooming in but I doubt that it takes a significant amount of time
    for (let i = endOfPositions; i < end; i++) {
        // @ts-ignore
        // positions_current[i] = 0
    }
    // // @ts-ignore
    // positions_current[0] = 3
    // // @ts-ignore
    // positions_current[1] = 3
    // // @ts-ignore
    // positions_current[2] = 3
    // // @ts-ignore
    // positions_current[3] = 2
    // // @ts-ignore
    // positions_current[4] = 3
    // // @ts-ignore
    // positions_current[5] = 2
    // // @ts-ignore
    // positions_current[6] = 2
    // // @ts-ignore
    // positions_current[7] = 2
    // // @ts-ignore
    // positions_current[8] = 2

    mesh.geometry.attributes.position.needsUpdate = true
}

async function fetchChunk(chunkId: string, level: number): Promise<Float32Array | undefined> {
    const url = `${process.env.PUBLIC_URL}/chunks/${chunkId}_${level}.json`
    // const url = `${process.env.PUBLIC_URL}/chunks/0_0.json`
    let res
    try {
        res = await axios.get(url)
    } catch (e) {
        return undefined
    }
    const positions = res.data.positions
    return positions
}

function positionToChunkId(x: number, z: number): string {
    const isXValid = x >= minX || x <= maxX
    const isZValid = z >= minZ || z <= maxZ
    if (!isXValid || !isZValid) {
        throw new Error(`Received invalid coordinates x=${x} valid? ${isXValid}, z=${z} valid? ${isZValid}`)
    }
    let level = 0
    // TODO implement some logic to set level based on z value
    const column = Math.floor((x / columnSize))
    const row = Math.floor((z / rowSize))
    const chunkId = createChunkId(column, row)
    return chunkId
}

async function updateChunks(x: number, y: number, z: number): Promise<void> {
    for (let i = 0; i < columns; i++) {
        for (let j = 0; j < rows; j++) {
            const chunkId = createChunkId(i, j)
            const chunkInfo = chunkInfoMap[chunkId]
            if (!chunkInfo.isValid) {
                continue
            }

            const calculatedLevel = calculateLevel(chunkInfo, x, y, z)
            if (calculatedLevel !== chunkInfo.level) {
                chunkInfo.level = calculatedLevel
                toFetch.push(chunkInfo)
            }
        }
    }
    // console.log(toFetch)
    // console.log(toFetch.length)
    // await Promise.all(toFetch.map(async chunkInfo => {
    //     const positions = await fetchChunk(chunkInfo.id, chunkInfo.level)
    //     updateChunk(chunkInfo, positions)
    // }))
}

function calculateLevel(chunk: ChunkBufferInfo, x: number, y: number, z: number): number {
    const level = 0  // TODO do some logic on y
    return level
}

function createChunkId(column: number, row: number): string {
    return `${(column * rows) + row}`
}


function createMesh(name?: string): [THREE.Mesh, THREE.LineSegments] {
    if (typeof name !== 'undefined') {
        mesh.name = name
    }
    const edges = new THREE.EdgesGeometry(geometry);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
        color: shade('#006994', -0.5),
        linewidth: 3,  // Due to limitations of the OpenGL Core Profile with the WebGL renderer on most platforms linewidth will always be 1 regardless of the set value.
    }));
    return [mesh, line]
}

export default Renderer
