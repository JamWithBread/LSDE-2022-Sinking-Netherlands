import React, {useEffect, useRef, useState} from 'react'
import * as THREE from 'three'
import {FlyControls} from './Control'
import {shade} from "../utils/color";
import mesh_data from '../mesh_data/random_sample_1665765047.json';

const cameraFOV = 75
const cameraNear = 0.1
const cameraFar = 1000

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
        const {trackedObjects: to, cleanup} = initScene(rendererDivRef)
        setTrackedObjects(to)
        return () => {
            cleanup()
        }
    }, [])
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
        mesh_data.positions,
        mesh_data.color,
        mesh1Name
    )
    scene.add(mesh1)
    scene.add(edges1)

    camera.position.z = 5

    function animate() {
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


function createMesh(vertices: number[], color: string, name?: string): [THREE.Mesh, THREE.LineSegments] {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
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
                gl_FragColor = vec4(mix(color1, color2, pow(positionVertex.y, 0.4) - 0.75), 1.0);
            }
        `,
    });
    const mesh = new THREE.Mesh(geometry, material)
    if (typeof name !== 'undefined') {
        mesh.name = name
    }
    const edges = new THREE.EdgesGeometry(geometry);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
        color: shade(color, -0.5),
        linewidth: 3,  // Due to limitations of the OpenGL Core Profile with the WebGL renderer on most platforms linewidth will always be 1 regardless of the set value.
    }));
    return [mesh, line]
}

export default Renderer
