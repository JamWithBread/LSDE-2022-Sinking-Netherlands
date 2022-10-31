import React, {useEffect, useRef, useState} from 'react'
import * as THREE from 'three'
import {FlyControls} from './Control'
import axios from 'axios'
import axiosRetry from 'axios-retry';
import metadata_ahn3 from '../chunks/ahn3/_metadata.json'
import metadata_ahn2 from '../chunks/ahn2/_metadata.json'
import {MathUtils} from "three";

axiosRetry(axios, {
    retries: 10,
    retryDelay: axiosRetry.exponentialDelay,
})
const nFetchPerFrame = 10  // we get errors when this number is high, but I am not a 100% sure if the retries help, they still occur but maybe less

const cameraFOV = 100
const cameraNear = 0.1
const cameraFar = 10000

const minX = metadata_ahn3.minX
const minZ = metadata_ahn3.minZ
const minY = metadata_ahn3.minY
const maxX = metadata_ahn3.maxX
const maxZ = metadata_ahn3.maxZ
const maxY = metadata_ahn3.maxY
const xRange = maxX - minX
const zRange = maxZ - minZ
const yRange = maxY - minY

const columns = metadata_ahn3.columns
const rows = metadata_ahn3.rows
const levels = metadata_ahn3.levels

let zoomFactor = 16
const fpsTarget = 60
const nAverage = 20
const fpsAverage: number[] = []
for (let i = 0; i < nAverage; i++) {
    fpsAverage.push(fpsTarget)
}
const maxLevelChangeCount = 2 * nAverage

const toFetchAHN3: ChunkBufferInfo[] = []
const toFetchAHN2: ChunkBufferInfo[] = []

type ChunkBufferInfo = {
    id: string,
    x: number,
    z: number,
    level: number,
    levelChangeCount: number,
    minBufferIdx: number,
    length: number,
}

const geometryAHN3 = new THREE.BufferGeometry()
const geometryAHN2 = new THREE.BufferGeometry()
const vertexLengthsAHN3 = metadata_ahn3.vertexLengths
const vertexLengthsAHN2 = metadata_ahn2.vertexLengths
const buffer_size_ahn3 = vertexLengthsAHN3.reduce((partialSum, a) => partialSum + a, 0)
const buffer_size_ahn2 = vertexLengthsAHN2.reduce((partialSum, a) => partialSum + a, 0)
const buffer_idxs_ahn3 = [0, ...vertexLengthsAHN3.map((elem, index) => vertexLengthsAHN3.slice(0, index + 1).reduce((a, b) => a + b))]
const buffer_idxs_ahn2 = [0, ...vertexLengthsAHN2.map((elem, index) => vertexLengthsAHN2.slice(0, index + 1).reduce((a, b) => a + b))]

const positionsAHN3 = new Float32Array(buffer_size_ahn3)
const positionsAHN2 = new Float32Array(buffer_size_ahn2)

type ChunkInfoMap = {
    [k: string]: ChunkBufferInfo
}
type levelChunkIdMap = {
    [l: string]: string[]
}

function createChunkInfoMap(chunkIds: string[], buffer_idxs: number[]): ChunkInfoMap {
    const chunkInfoMap: ChunkInfoMap = {}
    let counter = 0
    for (let i = 0; i < chunkIds.length; i++) {
        const level = -1
        const id = chunkIds[i]
        const idInt = parseInt(id)
        const column = idInt % rows
        const row = Math.floor(idInt / columns)
        let x = ((row / rows) - 0.5) * (xRange)
        let z = ((column / columns) - 0.5) * (zRange)

        chunkInfoMap[id] = {
            id: id,
            level: level,
            z: z,
            x: -x,
            levelChangeCount: 0,
            minBufferIdx: buffer_idxs[i],
            length: buffer_idxs[i + 1] - buffer_idxs[i],
        }
        counter++
    }
    return chunkInfoMap
}

const chunkInfoMapAHN3 = createChunkInfoMap(metadata_ahn3.chunkIds.combined, buffer_idxs_ahn3)
const chunkInfoMapAHN2 = createChunkInfoMap(metadata_ahn2.chunkIds.combined, buffer_idxs_ahn2)

type ChunkIds = {
    combined: string[],
    "0": string[],
    [l: string]: string[]
}

function createLevelChunkIdMap(chunkIds: ChunkIds): levelChunkIdMap {
    let levelChunkIdMap: levelChunkIdMap = {}
    for (const level of levels) {
        const levelStr = level.toString()
        if (Object.keys(chunkIds).includes(levelStr)) {
            levelChunkIdMap[levelStr] = chunkIds[levelStr]
        }
    }
    return levelChunkIdMap
}

const levelChunkIdMapAHN3 = createLevelChunkIdMap(metadata_ahn3.chunkIds)
const levelChunkIdMapAHN2 = createLevelChunkIdMap(metadata_ahn2.chunkIds)

geometryAHN3.setAttribute('position', new THREE.BufferAttribute(positionsAHN3, 3));
geometryAHN2.setAttribute('position', new THREE.BufferAttribute(positionsAHN2, 3));

const vertexShader = `
            varying vec3 positionVertex;

            void main() {
                positionVertex = position;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `

const fragmentShader = `
            uniform vec3 color1;
            uniform vec3 color2;

            varying vec3 positionVertex;

            void main() {
                gl_FragColor = vec4(mix(color1, color2, pow(positionVertex.y/${maxY}, 0.3)), 1.0);
            }
        `

const materialAHN3 = new THREE.ShaderMaterial({
    uniforms: {
        color1: {
            value: new THREE.Color(0xFF8000),
        },
        color2: {
            value: new THREE.Color(0xFFFBB6)
        }
    },
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    side: THREE.DoubleSide
})

const materialAHN2 = new THREE.ShaderMaterial({
    uniforms: {
        color1: {
            value: new THREE.Color(0x03045E),
        },
        color2: {
            value: new THREE.Color(0xCAF0F8)
        }
    },
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    side: THREE.DoubleSide
})
// const materialAHN2 = new THREE.MeshPhongMaterial({
//     color: 0xFF0000,    // red (can also use a CSS color string here)
//     flatShading: true,
//     side: THREE.DoubleSide
// });

const meshAHN3 = new THREE.Mesh(geometryAHN3, materialAHN3)
const meshAHN3Name = "mesh_ahn3"
meshAHN3.frustumCulled = false
meshAHN3.name = meshAHN3Name

const meshAHN2 = new THREE.Mesh(geometryAHN2, materialAHN2)
const meshAHN2Name = "mesh_ahn2"
meshAHN2.frustumCulled = false
meshAHN2.name = meshAHN2Name

const waterGeometry = new THREE.BufferGeometry();
// create a simple square shape. We duplicate the top left and bottom right
// vertices because each vertex needs to appear once per triangle.

// itemSize = 3 because there are 3 values (components) per vertex
waterGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
    minX, 0, minZ,
    minX, 0, maxZ,
    maxX, 0, maxZ,

    minX, 0, minZ,
    maxX, 0, maxZ,
    maxX, 0, minZ,
]), 3))
const waterMaterial = new THREE.MeshBasicMaterial({color: 0x005477})
const waterMesh = new THREE.Mesh(waterGeometry, waterMaterial);
const waterName = "water"
waterMesh.name = waterName
waterMesh.visible = false

type RenderProps = {
    isRenderingMeshAHN3: boolean
    isRenderingMeshAHN2: boolean
    isRenderingWater: boolean
    waterHeight: number
}

type TrackedObjects = {
    [meshAHN3Name]?: THREE.Mesh;
    [meshAHN2Name]?: THREE.Mesh;
    [waterName]?: THREE.Mesh;
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
        const mesh = trackedObjects[meshAHN3Name]
        if (typeof mesh === 'undefined') {
            return
        }
        mesh.visible = !mesh.visible
    }, [props.isRenderingMeshAHN3])
    useEffect(() => {
        if (trackedObjects === null) {
            return
        }
        const mesh = trackedObjects[meshAHN2Name]
        if (typeof mesh === 'undefined') {
            return
        }
        mesh.visible = !mesh.visible
    }, [props.isRenderingMeshAHN2])
    useEffect(() => {
        if (trackedObjects === null) {
            return
        }
        const mesh = trackedObjects[waterName]
        if (typeof mesh === 'undefined') {
            return
        }
        mesh.visible = !mesh.visible
    }, [props.isRenderingWater])
    useEffect(() => {
        if (trackedObjects === null) {
            return
        }
        const mesh = trackedObjects[waterName]
        if (typeof mesh === 'undefined') {
            return
        }

        const positions_current = mesh.geometry.attributes.position.array;
        const convertedWaterHeight = (((props.waterHeight / 100) - 0.5) * (yRange))
        for (let i = 1; i < positions_current.length; i += 3) {
            // @ts-ignore
            positions_current[i] = convertedWaterHeight
        }
        mesh.geometry.attributes.position.needsUpdate = true
    }, [props.waterHeight])
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

    const axesHelper = new THREE.AxesHelper(5)
    scene.add(axesHelper)

    scene.add(meshAHN3)
    scene.add(meshAHN2)

    scene.add(waterMesh)

    camera.position.y = maxY * 10
    camera.lookAt(0, 0, 0)
    camera.rotateZ(MathUtils.degToRad(180))


    window.onresize = function () {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
        const delta = clock.getDelta()
        updateChunks(delta, camera.position.x, camera.position.y, camera.position.z)
        for (let i = 0; i < nFetchPerFrame && toFetchAHN3.length > 0; i++) {
            const chunkToFetch = toFetchAHN3.pop()
            if (chunkToFetch !== undefined) {
                fetchChunk(3, chunkToFetch.id, chunkToFetch.level).then(positions => updateChunk(3, chunkToFetch, positions))
            }
        }
        for (let i = 0; i < nFetchPerFrame && toFetchAHN2.length > 0; i++) {
            const chunkToFetch = toFetchAHN2.pop()
            if (chunkToFetch !== undefined) {
                fetchChunk(2, chunkToFetch.id, chunkToFetch.level).then(positions => updateChunk(2, chunkToFetch, positions))
            }
        }

        requestAnimationFrame(animate)
        controls.update(delta)
        renderer.render(scene, camera)
    }

    animate()


    return {
        trackedObjects: {
            [meshAHN3Name]: meshAHN3,
            [meshAHN2Name]: meshAHN2,
            [waterName]: waterMesh,
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

function updateChunk(ahn: number, chunkInfo: ChunkBufferInfo, positions_chunk: Float32Array) {

    let position
    if (ahn === 3) {
        position = meshAHN3.geometry.attributes.position;
    } else {
        position = meshAHN2.geometry.attributes.position;
    }
    const positions_current = position.array

    const start = chunkInfo.minBufferIdx
    const endOfPositions = chunkInfo.minBufferIdx + positions_chunk.length
    const end = chunkInfo.minBufferIdx + chunkInfo.length
    if (start % 9 !== 0) {
        console.error("start should be divisible by 9: " + start)
        return
    }
    for (let i = start; i < endOfPositions; i++) {
        // @ts-ignore
        positions_current[i] = positions_chunk[i - start]
    }
    // TODO setting to 0 is unnecessary if we're zooming in but I doubt that it takes a significant amount of time
    for (let i = endOfPositions; i < end; i++) {
        // @ts-ignore
        positions_current[i] = 0
    }
    position.needsUpdate = true

}

async function fetchChunk(ahn: number, chunkId: string, level: number): Promise<Float32Array> {
    const url = `${process.env.PUBLIC_URL}/chunks/ahn${ahn}/${chunkId}_${level}.json`
    const res = await axios.get(url)
    const positions = res.data.positions
    return positions
}

function updateChunks(delta: number, x: number, y: number, z: number) {
    for (const id of metadata_ahn2.chunkIds.combined) {
        const chunkInfo = chunkInfoMapAHN2[id]
        const calculatedLevel = calculateLevel(chunkInfo, delta, x, y, z)
        if (calculatedLevel !== chunkInfo.level && levelChunkIdMapAHN2[calculatedLevel].includes(id)) {
            if (chunkInfo.levelChangeCount < maxLevelChangeCount) {
                chunkInfo.levelChangeCount++
            } else {
                chunkInfo.level = calculatedLevel
                chunkInfo.levelChangeCount = 0
                toFetchAHN2.push(chunkInfo)
            }
        }
    }
    for (const id of metadata_ahn3.chunkIds.combined) {
        const chunkInfo = chunkInfoMapAHN3[id]
        const calculatedLevel = calculateLevel(chunkInfo, delta, x, y, z)
        if (calculatedLevel !== chunkInfo.level && levelChunkIdMapAHN3[calculatedLevel].includes(id)) {
            if (chunkInfo.levelChangeCount < maxLevelChangeCount) {
                chunkInfo.levelChangeCount++
            } else {
                chunkInfo.level = calculatedLevel
                chunkInfo.levelChangeCount = 0
                toFetchAHN3.push(chunkInfo)
            }
        }
    }
}

function calculateLevel(chunk: ChunkBufferInfo, delta: number, x: number, y: number, z: number): number {
    const x_dist = Math.pow(chunk.x - x, 2)
    const z_dist = Math.pow(chunk.z - z, 2)
    const dist = (x_dist + z_dist)
    fpsAverage.push(1 / delta)
    fpsAverage.shift()
    const fpsCurrent = fpsAverage.reduce((a, b) => a + b, 0) / nAverage
    if (fpsCurrent < fpsTarget * 0.25) {
        zoomFactor *= 0.9995
    } else if (fpsCurrent < fpsTarget * 0.5) {
        zoomFactor *= 0.9999
    } else if (fpsCurrent > fpsTarget * 1.5) {
        zoomFactor *= 1.000005
    } else if (fpsCurrent > fpsTarget * 1.2) {
        zoomFactor *= 1.000001
    }
    zoomFactor = Math.max(1, zoomFactor)
    zoomFactor = Math.min(64, zoomFactor)
    for (let i = 0; i < levels.length - 1; i++) {
        if ((dist < (zRange + xRange) * zoomFactor) && y < maxY * 8) {
            return levels[i]
        }
    }
    return levels[levels.length - 1]
}

export default Renderer
