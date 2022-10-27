import * as THREE from 'three'

const _changeEvent = {type: 'change'};

class FlyControls extends THREE.EventDispatcher {
    private camera: THREE.Camera;
    public domElement: HTMLElement;
    public movementSpeed: number;
    public rollSpeed: number;
    private dragToLook: boolean;
    private autoForward: boolean;
    private tmpQuaternion: THREE.Quaternion;
    private status: number;
    private moveState: { rollRight: number; left: number; forward: number; back: number; pitchDown: number; up: number; right: number; pitchUp: number; down: number; yawRight: number; yawLeft: number; rollLeft: number };
    private moveVector: THREE.Vector3;
    private rotationVector: THREE.Vector3;
    private movementSpeedMultiplier: number;
    private _keydown: OmitThisParameter<(event: KeyboardEvent) => void>;
    private _keyup: OmitThisParameter<(event: KeyboardEvent) => void>;
    private scope: this;
    private EPS: number;
    private lastQuaternion: THREE.Quaternion;
    private lastPosition: THREE.Vector3;

    constructor(camera: THREE.Camera, domElement: HTMLElement) {
        super()

        this.camera = camera
        this.domElement = domElement

        this.movementSpeed = 0.01
        this.movementSpeedMultiplier = 1.0
        this.rollSpeed = 0.005

        this.dragToLook = false
        this.autoForward = false

        this.scope = this

        this.EPS = 0.000001

        this.lastQuaternion = new THREE.Quaternion()
        this.lastPosition = new THREE.Vector3()

        this.tmpQuaternion = new THREE.Quaternion()

        this.status = 0

        this.moveState = {
            up: 0,
            down: 0,
            left: 0,
            right: 0,
            forward: 0,
            back: 0,
            pitchUp: 0,
            pitchDown: 0,
            yawLeft: 0,
            yawRight: 0,
            rollLeft: 0,
            rollRight: 0
        }
        this.moveVector = new THREE.Vector3(0, 0, 0)
        this.rotationVector = new THREE.Vector3(0, 0, 0)


        this._keydown = this.keydown.bind(this)
        this._keyup = this.keyup.bind(this)

        this.domElement.addEventListener('contextmenu', this.contextmenu)

        window.addEventListener('keydown', this._keydown)
        window.addEventListener('keyup', this._keyup)

        this.updateMovementVector()
        this.updateRotationVector()
    }

    keydown(event: KeyboardEvent) {
        if (event.altKey) {
            return;
        }
        const movementSpeedFoo = 100
        switch (event.code) {
            // case 'ShiftLeft':
            // case 'ShiftRight':
            //     this.movementSpeedMultiplier = .1;
            //     break;

            case 'KeyW':
                this.moveState.up = movementSpeedFoo;
                break;
            case 'KeyS':
                this.moveState.down = movementSpeedFoo;
                break;

            case 'KeyA':
                this.moveState.left = movementSpeedFoo;
                break;
            case 'KeyD':
                this.moveState.right = movementSpeedFoo;
                break;
            //
            // case 'KeyR':
            //     this.moveState.up = 1;
            //     break;
            // case 'KeyF':
            //     this.moveState.down = 1;
            //     break;

            case 'ArrowUp':
                this.moveState.forward = this.movementSpeed;
                break;
            case 'ArrowDown':
                this.moveState.back = this.movementSpeed;
                break;

            case 'ArrowLeft':
                this.moveState.yawLeft = 1;
                break;
            case 'ArrowRight':
                this.moveState.yawRight = 1;
                break;

            case 'KeyQ':
                this.moveState.rollLeft = 1;
                break;
            case 'KeyE':
                this.moveState.rollRight = 1;
                break;

        }
        this.updateMovementVector();
        this.updateRotationVector();
    };

    keyup(event: KeyboardEvent) {
        switch (event.code) {
            case 'ShiftLeft':
            case 'ShiftRight':
                this.movementSpeedMultiplier = 1;
                break;

            case 'KeyW':
                this.moveState.up = 0;
                break;
            case 'KeyS':
                this.moveState.down = 0;
                break;

            case 'KeyA':
                this.moveState.left = 0;
                break;
            case 'KeyD':
                this.moveState.right = 0;
                break;

            // case 'KeyR':
            //     this.moveState.up = 0;
            //     break;
            // case 'KeyF':
            //     this.moveState.down = 0;
            //     break;
            //
            case 'ArrowUp':
                this.moveState.forward = 0;
                break;
            case 'ArrowDown':
                this.moveState.back = 0;
                break;

            case 'ArrowLeft':
                this.moveState.yawLeft = 0;
                break;
            case 'ArrowRight':
                this.moveState.yawRight = 0;
                break;

            case 'KeyQ':
                this.moveState.rollLeft = 0;
                break;
            case 'KeyE':
                this.moveState.rollRight = 0;
                break;

        }

        this.updateMovementVector();
        this.updateRotationVector();
    };

    update(delta: number) {
        const moveMult = delta * this.scope.movementSpeed;
        const rotMult = delta * this.scope.rollSpeed;

        this.scope.camera.translateX(this.scope.moveVector.x * moveMult);
        this.scope.camera.translateY(this.scope.moveVector.y * moveMult);
        this.scope.camera.translateZ(this.scope.moveVector.z * moveMult);

        this.scope.tmpQuaternion.set(this.scope.rotationVector.x * rotMult, this.scope.rotationVector.y * rotMult, this.scope.rotationVector.z * rotMult, 1).normalize();
        this.scope.camera.quaternion.multiply(this.scope.tmpQuaternion);

        if (
            this.lastPosition.distanceToSquared(this.scope.camera.position) > this.EPS ||
            8 * (1 - this.lastQuaternion.dot(this.scope.camera.quaternion)) > this.EPS
        ) {

            this.scope.dispatchEvent(_changeEvent);
            this.lastQuaternion.copy(this.scope.camera.quaternion);
            this.lastPosition.copy(this.scope.camera.position);

        }
    };

    updateMovementVector() {
        const forward = (this.moveState.forward || (this.autoForward && !this.moveState.back)) ? 1 : 0;

        this.moveVector.x = (-this.moveState.left + this.moveState.right);
        this.moveVector.y = (-this.moveState.down + this.moveState.up);
        this.moveVector.z = (-forward + this.moveState.back);
    };

    updateRotationVector() {
        this.rotationVector.x = (-this.moveState.pitchDown + this.moveState.pitchUp);
        this.rotationVector.y = (-this.moveState.yawRight + this.moveState.yawLeft);
        this.rotationVector.z = (-this.moveState.rollRight + this.moveState.rollLeft);
    };

    getContainerDimensions() {
        return {
            size: [this.domElement.offsetWidth, this.domElement.offsetHeight],
            offset: [this.domElement.offsetLeft, this.domElement.offsetTop]
        };
    }

    dispose() {
        this.domElement.removeEventListener('contextmenu', this.contextmenu);
        window.removeEventListener('keydown', this._keydown);
        window.removeEventListener('keyup', this._keyup);
    }

    contextmenu(event: MouseEvent) {
        event.preventDefault();

    }
}

export {FlyControls};