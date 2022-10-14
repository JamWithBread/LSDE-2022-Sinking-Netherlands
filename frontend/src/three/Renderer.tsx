import React, {useEffect, useRef} from 'react'
import * as THREE from 'three'
import {FlyControls} from './Control'
import {shade} from "../utils/color";
import mesh_data from '../mesh_data/random_sample_1665765047.json';

const cameraFOV = 75
const cameraNear = 0.1
const cameraFar = 1000

function initScene(ref: React.RefObject<HTMLElement>): () => void {
    const scene = new THREE.Scene()

    const camera = new THREE.PerspectiveCamera(
        cameraFOV,
        window.innerWidth / window.innerHeight,
        cameraNear,
        cameraFar
    )
    const renderer = new THREE.WebGLRenderer()
    const controls = new FlyControls(camera, renderer.domElement)
    const clock = new THREE.Clock()

    controls.movementSpeed = 5;
    controls.domElement = renderer.domElement;
    controls.rollSpeed = Math.PI / 3;

    renderer.setSize(window.innerWidth, window.innerHeight)

    const htmlEl = ref.current
    if (htmlEl == null) {
        console.error("rendererDivRef is null; can't mount threejs renderer to it")
        return () => {
        }
    }
    htmlEl.appendChild(renderer.domElement)

    const skyboxMesh = createSkyboxMesh()
    scene.add(skyboxMesh);

    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);

    // const meshData =

    const [mesh1, edges1] = createMesh(
        new Float32Array(mesh_data.positions),
        mesh_data.color,
    )
    scene.add(mesh1)
    scene.add(edges1)

    camera.position.z = 5

    function animate() {
        requestAnimationFrame(animate)

        const delta = clock.getDelta();
        controls.update(delta);

        renderer.render(scene, camera)

    }

    animate()

    return () => {
        htmlEl.removeChild(renderer.domElement)
    }
}

function createSkyboxMesh() {
    const baseFilename = process.env.PUBLIC_URL + "/skybox/galaxy/galaxy";
    const fileType = ".png";
    const sides = ["+Z", "-Z", "+Y", "-Y", "+X", "-X"];
    const pathStrings = sides.map(side => baseFilename + side + fileType)
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


function createMesh(vertices: Float32Array, color: string) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3))
    const material = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
    })
    const mesh = new THREE.Mesh(geometry, material)
    const edges = new THREE.EdgesGeometry(geometry);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
        color: shade(color, -0.5),
        linewidth: 3,  // Due to limitations of the OpenGL Core Profile with the WebGL renderer on most platforms linewidth will always be 1 regardless of the set value.
    }));
    return [mesh, line]
}

function Renderer() {
    const rendererDivRef = useRef<HTMLDivElement>(null)
    useEffect(() => {
        const cleanup = initScene(rendererDivRef)
        return () => {
            cleanup()
        }
    }, [])
    return (
        <div ref={rendererDivRef}>

        </div>
    )
}

export default Renderer
