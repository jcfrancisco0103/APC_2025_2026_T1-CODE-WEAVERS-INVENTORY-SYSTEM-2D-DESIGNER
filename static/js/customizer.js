/// Jersey Customizer JavaScript

document.addEventListener("DOMContentLoaded", () => {
  // Configuration object to store all jersey customization settings
  const config = {
    jerseyType: "tshirt",
    currentView: "front",
    primaryColor: "#ffffff",
    secondaryColor: "#ffffff",
    pattern: "none",
    frontNumber: "",
    backName: "",
    backNumber: "",
    textColor: "#000000",
    logo: null,
    logoPlacement: "front",
    logoSize: 0.5,
    // Number positions no longer controlled by sliders; use drag only
    backNamePosition: { x: 0, y: 0.2 },
    logoPosition: { x: 0, y: 0 },
  }

  // Three.js variables
let scene, camera, renderer, controls
let jersey, bodyMeshes = [], sleeveMeshes = []
let bodyMaterial, sleeveMaterial
let frontNumberMesh, backNameMesh, backNumberMesh, logoMesh
let decalMesh = null
let gridHelper
// track painted original materials so we can restore them
const paintedMaterials = new Map()
// Toggle to visualize debug markers and logs in the scene. Enable from browser console: window.DEBUG = true
window.DEBUG = window.DEBUG || false

  // Dragging support: state and helpers
  const dragState = {
    raycaster: new THREE.Raycaster(),
    mouse: new THREE.Vector2(),
    isDragging: false,
    target: null,
    side: null,
  }
  // Dragging enable toggle (controlled by UI button)
  let dragEnabled = false

function _addDebugSphereAtWorld(pos, color = 0xff0000, ttl = 3000) {
  try {
    const s = new THREE.Mesh(new THREE.SphereGeometry(0.01, 8, 8), new THREE.MeshBasicMaterial({ color }))
    s.position.copy(pos)
    s.name = 'debug-sphere'
    scene.add(s)
    setTimeout(() => { try { if (s.parent) s.parent.remove(s) } catch (e) {} }, ttl)
  } catch (e) { console.warn('debug sphere failed', e) }
}

  // DOM elements
  const canvasContainer = document.getElementById("canvas-container")
  const jerseyTypeSelect = document.getElementById("jersey-type")
  const frontViewBtn = document.getElementById("front-view")
  const backViewBtn = document.getElementById("back-view")
  const primaryColorInput = document.getElementById("primary-color")
  const secondaryColorInput = document.getElementById("secondary-color")
  const patternSelect = document.getElementById("pattern")
  const frontNumberInput = document.getElementById("front-number")
  const backNameInput = document.getElementById("back-name")
  const backNumberInput = document.getElementById("back-number")
  const textColorInput = document.getElementById("text-color")
  const logoUpload = document.getElementById("logo-upload")
  const logoSizeInput = document.getElementById("logo-size")
  const logoPlacementSelect = document.getElementById("logo-placement")
  const frontOptions = document.getElementById("front-options")
  const backOptions = document.getElementById("back-options")
  const logoOptions = document.getElementById("logo-options")
  const resetViewBtn = document.getElementById("reset-view")
  const toggleDragBtn = document.getElementById("toggle-drag")
  const clearAllBtn = document.getElementById("clear-all")
  const downloadDesignBtn = document.getElementById("download-design")

// Position sliders
// Number position sliders removed; users drag numbers directly
const backNameXSlider = document.getElementById("back-name-x")
const backNameYSlider = document.getElementById("back-name-y")
const logoXSlider = document.getElementById("logo-x")
const logoYSlider = document.getElementById("logo-y")

  // Initialize Three.js scene
  function initScene() {
    // Create scene
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0x1a202c)

    // Create camera
    camera = new THREE.PerspectiveCamera(50, canvasContainer.clientWidth / canvasContainer.clientHeight, 0.1, 1000)
    camera.position.z = 2

    // Create renderer
renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
    renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
// ensure correct color space handling
try { renderer.outputEncoding = THREE.sRGBEncoding } catch (e) {}
try { renderer.toneMappingExposure = 1.0 } catch (e) {}
    canvasContainer.appendChild(renderer.domElement)

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(1, 1, 1)
    scene.add(directionalLight)

    // Removed grid helper to keep scene clean

    // Add orbit controls with rotation limits
    controls = new THREE.OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.minDistance = 1
    controls.maxDistance = 5
    // Limit rotation to only 2 axes (X and Y)
    controls.minPolarAngle = 0
    controls.maxPolarAngle = Math.PI

    // Load jersey model
    loadJerseyModel()

    // Handle window resize
    window.addEventListener("resize", onWindowResize)

    // Start animation loop
    animate()
  }

  // Load jersey model based on selected type
  function loadJerseyModel() {
    const loader = new THREE.GLTFLoader()
    const modelPath = (typeof window !== 'undefined' && window.modelPath) ? window.modelPath : "/static/jersey_customizer/models/t_shirt.gltf"

    // Remove existing jersey if any
    if (jersey) {
      scene.remove(jersey)
    }

    // Clear body and sleeve meshes arrays before adding new meshes
    bodyMeshes = []
    sleeveMeshes = []

    // Remove and dispose decal mesh if exists
    if (logoMesh) {
      if (logoMesh.parent) logoMesh.parent.remove(logoMesh)
      logoMesh.geometry.dispose()
      logoMesh.material.dispose()
      logoMesh = null
    }

    loader.load(modelPath, (gltf) => {
      jersey = gltf.scene

      // Position the jersey in the center of the viewport
      jersey.position.set(0, -1.4, 0.5)

      scene.add(jersey)

      // Classify meshes into body and sleeves based on bounding box center x-position
      // Log for verification; adjust threshold as needed (e.g., |center.x| > 0.2 for sleeves)
      jersey.traverse((child) => {
        if (child.isMesh) {
          child.geometry.computeBoundingBox();
          const center = new THREE.Vector3();
          child.geometry.boundingBox.getCenter(center);
          console.log(`Mesh "${child.name}": bounding box center x = ${center.x.toFixed(2)}`);

          // Threshold: central (|x| <= 0.2) = body, sides = sleeves (adjust after logging)
          if (Math.abs(center.x) <= 0.2) {
            bodyMeshes.push(child);
          } else {
            sleeveMeshes.push(child);
          }
        }
      });

      // Apply initial colors
      applyBodyColor();
      applySleeveColor();

      // Create text and logo elements
      createTextElements()

      // Update jersey rotation based on current view
      updateJerseyRotation()
    },
    // onProgress callback
    (xhr) => {
      if (xhr.lengthComputable) {
        console.log(`Model loading: ${(xhr.loaded / xhr.total * 100).toFixed(2)}% loaded`)
      } else {
        console.log(`Model loading: ${xhr.loaded} bytes loaded`)
      }
    },
    // onError callback
    (error) => {
      console.error('An error happened while loading the model:', error)
      // Fallback: create a simple front/back plane so features still work
      try {
        jersey = new THREE.Group()
        const frontPlane = new THREE.Mesh(
          new THREE.PlaneGeometry(0.8, 1.2),
          new THREE.MeshStandardMaterial({ color: config.primaryColor, side: THREE.DoubleSide })
        )
        frontPlane.position.set(0, -0.2, 0.02)
        const backPlane = new THREE.Mesh(
          new THREE.PlaneGeometry(0.8, 1.2),
          new THREE.MeshStandardMaterial({ color: config.primaryColor, side: THREE.DoubleSide })
        )
        backPlane.position.set(0, -0.2, -0.02)
        backPlane.rotation.y = Math.PI
        jersey.add(frontPlane)
        jersey.add(backPlane)
        scene.add(jersey)
        bodyMeshes = [frontPlane, backPlane]
        sleeveMeshes = []
        applyBodyColor()
        createTextElements()
        updateJerseyRotation()
        console.warn('Fallback jersey planes created due to missing GLTF model')
      } catch (e2) {
        console.error('Fallback creation failed:', e2)
      }
    })
  }

  // Create text and logo elements
  function createTextElements() {
    console.log("createTextElements called")
    // Remove existing text elements
    if (jersey) {
      if (frontNumberMesh) jersey.remove(frontNumberMesh)
      if (backNameMesh) jersey.remove(backNameMesh)
      if (backNumberMesh) jersey.remove(backNumberMesh)
    }
    // Remove decal mesh from scene and dispose
    if (logoMesh) {
      if (logoMesh.parent) logoMesh.parent.remove(logoMesh)
      logoMesh.geometry.dispose()
      logoMesh.material.dispose()
      logoMesh = null
    }
    // ... (do not restore painted materials here; restore only on Clear All)
    frontNumberMesh = null
    backNameMesh = null
    backNumberMesh = null

    // Create front number
    if (config.frontNumber) {
      const canvas = document.createElement("canvas")
      canvas.width = 256
      canvas.height = 256
      const ctx = canvas.getContext("2d")
      ctx.fillStyle = config.textColor
      ctx.font = "bold 150px Arial"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(config.frontNumber, 128, 128)

      const texture = new THREE.CanvasTexture(canvas)
      const geometry = new THREE.PlaneGeometry(0.3, 0.3)
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        side: THREE.DoubleSide,
      })

      frontNumberMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(frontNumberMesh)
      // Position relative to jersey
      // Initial default; user can drag to place anywhere (raised higher)
      frontNumberMesh.position.set(0.15, 0.55, 0.01)
      frontNumberMesh.rotation.y = Math.PI // Ensure it faces forward
      // Restore dragged world position if available
      if (config.frontNumberWorldPos) {
        const p = config.frontNumberWorldPos
        frontNumberMesh.position.set(p.x, p.y, p.z)
      }
    }

    // Create back name
    if (config.backName) {
      const canvas = document.createElement("canvas")
      canvas.width = 512
      canvas.height = 128
      const ctx = canvas.getContext("2d")
      ctx.fillStyle = config.textColor
      ctx.font = "bold 80px Arial"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(config.backName.toUpperCase(), 256, 64)

      const texture = new THREE.CanvasTexture(canvas)
      const geometry = new THREE.PlaneGeometry(0.5, 0.125)
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        side: THREE.DoubleSide,
      })

      backNameMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(backNameMesh)
      // Position relative to jersey
      backNameMesh.position.set(config.backNamePosition.x, config.backNamePosition.y, -0.01)
    }

    // Create back number
    if (config.backNumber) {
      const canvas = document.createElement("canvas")
      canvas.width = 256
      canvas.height = 256
      const ctx = canvas.getContext("2d")
      ctx.fillStyle = config.textColor
      ctx.font = "bold 150px Arial"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(config.backNumber, 128, 128)

      const texture = new THREE.CanvasTexture(canvas)
      const geometry = new THREE.PlaneGeometry(0.3, 0.3)
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        side: THREE.DoubleSide,
      })

      backNumberMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(backNumberMesh)
      // Position relative to jersey
      // Initial default; user can drag to place anywhere (raised higher)
      backNumberMesh.position.set(0, 0.45, -0.01)
      // Restore dragged world position if available
      if (config.backNumberWorldPos) {
        const p = config.backNumberWorldPos
        backNumberMesh.position.set(p.x, p.y, p.z)
      }
    }

    // Create logo if available using a decal projection onto the mesh surface
    if (config.logo && bodyMeshes.length > 0) {
      const textureLoader = new THREE.TextureLoader()
      textureLoader.crossOrigin = "anonymous"
      textureLoader.load(config.logo, (texture) => {
        texture.encoding = THREE.sRGBEncoding
        try { texture.flipY = false } catch (e) {}
        texture.wrapS = THREE.ClampToEdgeWrapping
        texture.wrapT = THREE.ClampToEdgeWrapping
        texture.needsUpdate = true

        // Helper: paint the uploaded image into the mesh's material map at the given UV coordinate
        function paintLogoToMeshTexture(targetMesh, image, uv, sizeFactor) {
          try {
            // Only proceed if mesh has UVs
            const geom = targetMesh.geometry
            if (!geom || !geom.attributes || !geom.attributes.uv) return false

            // Get base texture size if present
            let baseImg = null
            if (targetMesh.material && targetMesh.material.map && targetMesh.material.map.image) baseImg = targetMesh.material.map.image
            const W = baseImg ? baseImg.width : 1024
            const H = baseImg ? baseImg.height : 1024

            const canvas = document.createElement('canvas')
            canvas.width = W
            canvas.height = H
            const ctx = canvas.getContext('2d')

            if (baseImg) {
              try { ctx.drawImage(baseImg, 0, 0, W, H) } catch (e) { ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,W,H) }
            } else {
              ctx.fillStyle = '#ffffff'
              ctx.fillRect(0, 0, W, H)
            }

            // UV to pixel coordinates (invert v because canvas origin is top-left)
            const px = uv.x * W
            const py = (1 - uv.y) * H

            // Determine logo pixel size
            const s = Math.max(4, Math.floor(Math.min(W, H) * Math.min(1, sizeFactor)))
            const w = s
            const h = Math.floor(s * (image.height / image.width || 1))

            // Draw the logo centered at UV
            try { ctx.drawImage(image, px - w / 2, py - h / 2, w, h) } catch (e) { console.warn('failed draw logo image', e) }

            // Create texture from canvas and preserve orientation/wrap from original map if present
            const newTex = new THREE.CanvasTexture(canvas)
            newTex.encoding = THREE.sRGBEncoding
            // preserve flipY/wrap from existing map if available
            try {
              if (targetMesh.material && targetMesh.material.map) {
                newTex.flipY = !!targetMesh.material.map.flipY
                newTex.wrapS = targetMesh.material.map.wrapS
                newTex.wrapT = targetMesh.material.map.wrapT
              } else {
                newTex.flipY = false
              }
            } catch (e) { newTex.flipY = false }
            newTex.needsUpdate = true

            // If the mesh already has a material that supports maps, write into that material.map
            const existingMat = targetMesh.material
            try {
              // Support multi-material meshes by normalizing to an array
              const mats = Array.isArray(existingMat) ? existingMat : [existingMat]
              let assignedAny = false
              mats.forEach((m, idx) => {
                if (!m) return
                if (!(m.isMeshStandardMaterial || m.isMeshPhysicalMaterial || m.isMeshPhongMaterial || m.isMeshLambertMaterial)) return
                try { if (!paintedMaterials.has(targetMesh.uuid)) paintedMaterials.set(targetMesh.uuid, Array.isArray(targetMesh.material) ? targetMesh.material.slice() : targetMesh.material) } catch (e) {}
                try {
                  m.map = newTex
                  try { m.map.encoding = THREE.sRGBEncoding } catch (e) {}
                  try { m.map.needsUpdate = true } catch (e) {}
                  m.side = THREE.DoubleSide
                  m.transparent = true
                  m.alphaTest = 0.01
                  m.depthWrite = true
                  m.needsUpdate = true
                  assignedAny = true
                  console.log('Assigned painted map to material index', idx, 'of mesh', targetMesh.name || targetMesh.uuid)
                } catch (e) { console.warn('assign to sub-material failed', idx, e) }
              })

              if (assignedAny) {
                console.log('Painted into existing material.map for', targetMesh.name || targetMesh.uuid)
                return true
              }
            } catch (e) { console.warn('existing material detection failed', e) }

            // If assignment failed, try toggling flipY and retry once (some glTF maps require flipY=false)
            try {
              newTex.flipY = !newTex.flipY
              newTex.needsUpdate = true
              const tryAssign = (m) => {
                try {
                  m.map = newTex
                  try { m.map.encoding = THREE.sRGBEncoding } catch (e) {}
                  try { m.map.needsUpdate = true } catch (e) {}
                  m.side = THREE.DoubleSide
                  m.transparent = true
                  m.alphaTest = 0.01
                  m.depthWrite = true
                  m.needsUpdate = true
                  return true
                } catch (e) { return false }
              }
              if (Array.isArray(existingMat)) {
                for (let i = 0; i < existingMat.length; i++) {
                  if (tryAssign(existingMat[i])) {
                    console.log('Assigned painted map after flipY toggle to material index', i)
                    return true
                  }
                }
              } else if (existingMat) {
                if (tryAssign(existingMat)) {
                  console.log('Assigned painted map after flipY toggle to single material')
                  return true
                }
              }
            } catch (e) { /* ignore flip fallback errors */ }

            // Otherwise, create a MeshStandardMaterial with the painted canvas
            try {
              const newMat = new THREE.MeshStandardMaterial({ map: newTex, side: THREE.DoubleSide })
              try { if (!paintedMaterials.has(targetMesh.uuid)) paintedMaterials.set(targetMesh.uuid, targetMesh.material) } catch (e) {}
              targetMesh.material = newMat
              console.log('Replaced material with MeshStandardMaterial for painted mesh', targetMesh.name || targetMesh.uuid)
              return true
            } catch (e) {
              console.warn('Failed to create new MeshStandardMaterial for painted texture', e)
              // fallback to basic material
              try {
                const basicMat = new THREE.MeshBasicMaterial({ map: newTex, side: THREE.DoubleSide, transparent: true })
                if (!paintedMaterials.has(targetMesh.uuid)) paintedMaterials.set(targetMesh.uuid, targetMesh.material)
                targetMesh.material = basicMat
                console.log('Fallback: Applied basic painted material', targetMesh.name || targetMesh.uuid)
                return true
              } catch (e2) { console.warn('fallback painting failed', e2) }
            }
          } catch (e) {
            console.warn('paintLogoToMeshTexture failed', e)
            return false
          }
        }

        // remove previous decal if exists, but preserve its orientation so we can keep it stable
        let preservedQuat = null
        if (decalMesh) {
          try { preservedQuat = decalMesh.quaternion.clone() } catch (e) { preservedQuat = null }
          if (decalMesh.parent) decalMesh.parent.remove(decalMesh)
          try { decalMesh.geometry.dispose(); decalMesh.material.dispose() } catch(e){}
          decalMesh = null
        }

        // helper: create decal on mesh using a raycast to get the surface normal
          function createDecalOnMesh(mesh, texture, preservedQuat) {
            try {
              if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox()
              const bbox = mesh.geometry.boundingBox

              // Compute a local point inside the bbox (center Z) and map user offsets into bbox space
              const posX = THREE.MathUtils.lerp(bbox.min.x, bbox.max.x, 0.5 + config.logoPosition.x)
              let posY = THREE.MathUtils.lerp(bbox.min.y, bbox.max.y, 0.5 + config.logoPosition.y)
              const neckThresholdY = bbox.max.y - (bbox.max.y - bbox.min.y) * 0.18
              posY = Math.min(posY, neckThresholdY)
              const posZ = THREE.MathUtils.lerp(bbox.min.z, bbox.max.z, 0.5)
              const localPos = new THREE.Vector3(posX, posY, posZ)

              // convert to world position and project to NDC for raycasting
              mesh.updateMatrixWorld(true)
              const worldPos = localPos.clone()
              mesh.localToWorld(worldPos)
              // debug: show where we projected the local point into world
              try { if (window.DEBUG) { console.log('project target worldPos', worldPos.toArray()); _addDebugSphereAtWorld(worldPos, 0x00ff00, 5000) } } catch(e){}
              const ndc = worldPos.clone().project(camera)
              if (window.DEBUG) console.log('ndc', ndc.x.toFixed(3), ndc.y.toFixed(3), ndc.z.toFixed(3))

              // Raycast from camera through that NDC point
              const raycaster = new THREE.Raycaster()
              raycaster.setFromCamera({ x: ndc.x, y: ndc.y }, camera)
              let intersects = raycaster.intersectObject(mesh, true)

              let point, normalWorld
              if (intersects && intersects.length > 0) {
                console.log('raycast primary hit count', intersects.length, 'hit object', intersects[0].object.name || intersects[0].object.uuid, 'distance', intersects[0].distance)
                point = intersects[0].point.clone()
                normalWorld = intersects[0].face.normal.clone().transformDirection(mesh.matrixWorld).normalize()
                // If intersection provides UV coordinates, attempt to paint into the mesh texture directly
                try {
                  const uv = intersects[0].uv
                  if (uv) {
                    // load the image element from texture.image
                    const img = texture.image
                    if (img) {
                      // increase size factor so the painted logo is visible by default
                      const painted = paintLogoToMeshTexture(mesh, img, uv, 0.6 * config.logoSize)
                      if (painted) {
                        console.log('Painted logo into mesh texture via UV')
                        try {
                          // Create a small overlay for immediate visual feedback, attached to jersey
                          const aspect = (texture.image && texture.image.width && texture.image.height) ? (texture.image.height / texture.image.width) : 1
                          const w = 0.25 * config.logoSize
                          const h = w * aspect
                          const overlayGeo = new THREE.PlaneGeometry(w, h)
                          const overlayMat = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide })
                          const overlay = new THREE.Mesh(overlayGeo, overlayMat)
                          // place overlay at hit point with a tiny offset along normal
                          const overlayPos = (typeof point !== 'undefined' && point) ? point.clone() : worldPos.clone()
                          try { overlayPos.add((normalWorld || new THREE.Vector3(0,1,0)).clone().multiplyScalar(0.01)) } catch (e) {}
                          overlay.position.copy(overlayPos)
                          // align to surface normal
                          try { if (normalWorld) overlay.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), normalWorld) } catch (e) {}
                          overlay.frustumCulled = false
                          overlay.renderOrder = 99999
                          try { overlay.userData.isOverlay = true } catch (e) {}
                          // preserve world transform when parenting to jersey
                          if (jersey) { scene.add(overlay); jersey.attach(overlay) } else { scene.add(overlay) }
                          try { logoMesh = overlay; logoMesh.name = 'logoMesh' } catch (e) {}
                        } catch (e) { console.warn('overlay creation failed', e) }
                        return
                      }
                    }
                  }
                } catch (e) { /* ignore */ }
              } else {
                // Fallback 1: cast a ray from the camera towards the worldPos
                const dirToPos = worldPos.clone().sub(camera.position).normalize()
                raycaster.set(camera.position, dirToPos)
                intersects = raycaster.intersectObject(mesh, true)
                if (intersects && intersects.length > 0) {
                  console.log('raycast camera->pos hit count', intersects.length, 'hit object', intersects[0].object.name || intersects[0].object.uuid, 'distance', intersects[0].distance)
                  point = intersects[0].point.clone()
                  normalWorld = intersects[0].face.normal.clone().transformDirection(mesh.matrixWorld).normalize()
                } else {
                  // Fallback 2: cast a ray downward from above the worldPos (useful if mesh is above ground)
                  const upOffset = new THREE.Vector3(0, Math.max(1.0, (camera.position.y - worldPos.y) * 0.9), 0)
                  const above = worldPos.clone().add(upOffset)
                  const downDir = new THREE.Vector3(0, -1, 0)
                  raycaster.set(above, downDir)
                  intersects = raycaster.intersectObject(mesh, true)
                  if (intersects && intersects.length > 0) {
                    console.log('raycast downward hit count', intersects.length, 'hit object', intersects[0].object.name || intersects[0].object.uuid, 'distance', intersects[0].distance)
                    point = intersects[0].point.clone()
                    normalWorld = intersects[0].face.normal.clone().transformDirection(mesh.matrixWorld).normalize()
                  } else {
                    // Fallback 3: grid-scan across bbox local XY to find a hit by projecting multiple sample points
                    console.log('Grid-scan fallback: sampling bbox for a hit')
                    const sampleGrid = 7
                    let found = false
                    const center = new THREE.Vector3()
                    bbox.getCenter(center)
                    const size = new THREE.Vector3().subVectors(bbox.max, bbox.min)
                    const stepX = size.x / (sampleGrid - 1)
                    const stepY = size.y / (sampleGrid - 1)
                        for (let i = 0; i < sampleGrid && !found; i++) {
                      for (let j = 0; j < sampleGrid && !found; j++) {
                        const localSample = new THREE.Vector3(bbox.min.x + i * stepX, bbox.min.y + j * stepY, posZ)
                        const worldSample = localSample.clone()
                        mesh.localToWorld(worldSample)
                            if (window.DEBUG) _addDebugSphereAtWorld(worldSample, 0x0000ff, 3000)
                        const ndcSample = worldSample.clone().project(camera)
                        raycaster.setFromCamera({ x: ndcSample.x, y: ndcSample.y }, camera)
                        const hits = raycaster.intersectObject(mesh, true)
                        if (hits && hits.length > 0) {
                          point = hits[0].point.clone()
                          normalWorld = hits[0].face.normal.clone().transformDirection(mesh.matrixWorld).normalize()
                          found = true
                          console.log('Grid-scan found hit at', i, j)
                        }
                      }
                    }
                    if (!found) {
                      console.warn('All raycast fallbacks failed; attempting vertex-snap fallback')
                      try {
                        const geom = mesh.geometry
                        if (geom && geom.attributes && geom.attributes.position) {
                          // find closest vertex in local space to localPos
                          const posAttr = geom.attributes.position
                          let closestIdx = -1
                          let closestDist2 = Infinity
                          const v = new THREE.Vector3()
                          for (let vi = 0; vi < posAttr.count; vi++) {
                            v.fromBufferAttribute(posAttr, vi)
                            const d2 = v.distanceToSquared(localPos)
                            if (d2 < closestDist2) { closestDist2 = d2; closestIdx = vi }
                          }
                          if (closestIdx >= 0) {
                            // get world position of that vertex
                            const vLocal = new THREE.Vector3().fromBufferAttribute(posAttr, closestIdx)
                            const vWorld = vLocal.clone(); mesh.localToWorld(vWorld)
                            point = vWorld.clone()
                            // try to get normal from vertex normals if available
                            if (geom.attributes.normal) {
                              const n = new THREE.Vector3().fromBufferAttribute(geom.attributes.normal, closestIdx)
                              normalWorld = n.clone().transformDirection(mesh.matrixWorld).normalize()
                            } else {
                              // fallback: estimate normal toward camera
                              const est = point.clone().sub(camera.position).normalize()
                              normalWorld = est
                            }
                            // offset slightly along normal
                            point.add(normalWorld.clone().multiplyScalar(0.01))
                            console.log('Vertex-snap used idx', closestIdx, 'point', point.toArray())
                          } else {
                            console.warn('vertex-snap failed: no vertex found; placing at bbox center')
                            const centerLocal = new THREE.Vector3(); bbox.getCenter(centerLocal)
                            const centerWorld = centerLocal.clone(); mesh.localToWorld(centerWorld)
                            let frontNormal = centerWorld.clone().sub(camera.position)
                            if (frontNormal.lengthSq() < 1e-6) frontNormal.set(0,0,1)
                            frontNormal.normalize()
                            normalWorld = frontNormal
                            point = centerWorld.clone().add(frontNormal.clone().multiplyScalar(0.02))
                          }
                        } else {
                          // last fallback: bbox center
                          const centerLocal = new THREE.Vector3(); bbox.getCenter(centerLocal)
                          const centerWorld = centerLocal.clone(); mesh.localToWorld(centerWorld)
                          let frontNormal = centerWorld.clone().sub(camera.position)
                          if (frontNormal.lengthSq() < 1e-6) frontNormal.set(0,0,1)
                          frontNormal.normalize()
                          normalWorld = frontNormal
                          point = centerWorld.clone().add(frontNormal.clone().multiplyScalar(0.02))
                        }
                      } catch (e) {
                        console.warn('vertex-snap fallback failed', e)
                        const centerLocal = new THREE.Vector3(); bbox.getCenter(centerLocal)
                        const centerWorld = centerLocal.clone(); mesh.localToWorld(centerWorld)
                        let frontNormal = centerWorld.clone().sub(camera.position)
                        if (frontNormal.lengthSq() < 1e-6) frontNormal.set(0,0,1)
                        frontNormal.normalize()
                        normalWorld = frontNormal
                        point = centerWorld.clone().add(frontNormal.clone().multiplyScalar(0.02))
                      }
                    }
                  }
                }
              }

              // Debug: show computed positions for diagnosis when enabled
              try {
                if (window.DEBUG) {
                  console.log('localPos', localPos.toArray())
                  console.log('worldPos', worldPos.toArray())
                  if (typeof point !== 'undefined' && point) console.log('point', point.toArray())
                  if (typeof normalWorld !== 'undefined' && normalWorld) console.log('normalWorld', normalWorld.toArray())
                  // draw debug spheres
                  try { if (point) _addDebugSphereAtWorld(point, 0xff00ff, 5000) } catch (e) {}
                  try { _addDebugSphereAtWorld(worldPos, 0x00ff00, 5000) } catch (e) {}
                }
              } catch (e) { console.warn('debug logging failed', e) }


              // orientation: rotate decal's +Z to align with the surface normal
              const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normalWorld)
              const euler = new THREE.Euler().setFromQuaternion(quat)

              const decalSize = new THREE.Vector3(0.4 * config.logoSize, 0.4 * config.logoSize, 0.4)
              const decalGeometry = new THREE.DecalGeometry(mesh, point, euler, decalSize)
              const decalMaterial = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthTest: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, side: THREE.FrontSide })

              decalMesh = new THREE.Mesh(decalGeometry, decalMaterial)
              // If a preserved orientation was provided, apply it so the decal keeps a stable rotation
              try { if (preservedQuat) decalMesh.quaternion.copy(preservedQuat) } catch (e) {}

              // If DecalGeometry produced no positions (some meshes/UVs or transforms can cause empty geometry),
              // fall back to attaching a small textured plane in mesh-local coordinates so the logo is visible.
              let decalHasPositions = false
              try {
                decalHasPositions = !!(decalGeometry && decalGeometry.attributes && decalGeometry.attributes.position && decalGeometry.attributes.position.count > 0)
              } catch (e) { decalHasPositions = false }

                if (decalHasPositions) {
                  if (jersey) jersey.add(decalMesh)
                } else {
                console.warn('DecalGeometry empty — using mesh-local plane fallback')
                try {
                  // Dispose the empty decal mesh
                  try { decalMesh.geometry.dispose(); decalMesh.material.dispose() } catch (e) {}

                  // Compute plane size (attempt to preserve aspect ratio) — increase base size for visibility
                  let w = 0.5 * config.logoSize
                  let h = w
                  try {
                    if (texture && texture.image && texture.image.width && texture.image.height) {
                      const aspect = texture.image.height / texture.image.width
                      h = w * aspect
                    }
                  } catch (e) {}

                  const planeGeo = new THREE.PlaneGeometry(w, h)
                  const planeMat = new THREE.MeshBasicMaterial({ map: texture, transparent: true, side: THREE.FrontSide, depthTest: true, polygonOffset: true, polygonOffsetFactor: -4 })
                  const plane = new THREE.Mesh(planeGeo, planeMat)

                  // Place the plane in mesh-local coordinates at localPos and orient by localNormal
                  // Ensure we have a localNormal (face normal in local space) or approximate it
                  let localNormal = null
                  try {
                    // If we had intersection faces earlier they were in local space; try to read one
                    if (typeof intersects !== 'undefined' && intersects && intersects.length > 0 && intersects[0].face) {
                      localNormal = intersects[0].face.normal.clone().normalize()
                    }
                  } catch (e) { localNormal = null }

                  if (!localNormal) {
                    // Approximate local normal from localPos vs bbox center
                    const c = new THREE.Vector3(); bbox.getCenter(c)
                    localNormal = localPos.clone().sub(c)
                    if (localNormal.lengthSq() < 1e-6) localNormal.set(0, 0, 1)
                    localNormal.normalize()
                  }

                  // Compute a world-space attachment point and offset it along the world-space normal,
                  // then convert back into mesh-local coordinates for a robust placement that respects
                  // mesh.world transforms.
                  const worldAttach = localPos.clone()
                  mesh.localToWorld(worldAttach)
                  // Prefer precomputed world normal if available
                  let worldNormalForPlane = null
                  try { if (typeof normalWorld !== 'undefined' && normalWorld) worldNormalForPlane = normalWorld.clone() } catch (e) { worldNormalForPlane = null }
                  if (!worldNormalForPlane) worldNormalForPlane = localNormal.clone().transformDirection(mesh.matrixWorld).normalize()

                  worldAttach.add(worldNormalForPlane.clone().multiplyScalar(0.02))
                  const localAttach = worldAttach.clone()
                  mesh.worldToLocal(localAttach)
                  plane.position.copy(localAttach)
                  // Ensure it's always rendered and not culled
                  plane.frustumCulled = false
                  plane.renderOrder = 999
                  // If a preserved orientation exists, use it; otherwise orient by localNormal
                  if (preservedQuat) {
                    plane.setRotationFromQuaternion(preservedQuat)
                  } else {
                    const planeQuat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), localNormal)
                    plane.setRotationFromQuaternion(planeQuat)
                  }

                  // Attach plane to the jersey root using world-space placement so parent transforms are handled
                  try {
                    // compute world-space attachment point and quaternion
                    const worldAttach = localPos.clone(); mesh.localToWorld(worldAttach)
                    let worldNormalForPlane = null
                    try { if (typeof normalWorld !== 'undefined' && normalWorld) worldNormalForPlane = normalWorld.clone() } catch (e) { worldNormalForPlane = null }
                    if (!worldNormalForPlane) worldNormalForPlane = localNormal.clone().transformDirection(mesh.matrixWorld).normalize()
                    const worldQuat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), worldNormalForPlane)

                    // place plane in world, then attach to jersey to preserve transform in jersey-local space
                    plane.position.copy(worldAttach)
                    plane.quaternion.copy(worldQuat)
                    scene.add(plane)
                    if (jersey) jersey.attach(plane)
                    console.log('plane attached to jersey at world', worldAttach.toArray())
                    decalMesh = plane
                  } catch (e) {
                    // fallback to mesh add if something goes wrong
                    mesh.add(plane)
                    decalMesh = plane
                    console.warn('attached plane directly to mesh as fallback', e)
                  }
                } catch (e) {
                  console.error('mesh-local plane fallback failed', e)
                }
              }
            } catch (err) {
              console.error('createDecalOnMesh failed', err)
            }
          }

          // Choose target mesh: prefer a body mesh on the requested side (front/back).
          // For `front` choose the mesh with the largest world-Z (closest to camera when jersey faces front).
          let targetMesh = null
          if (bodyMeshes && bodyMeshes.length > 0) {
            const candidates = []
            bodyMeshes.forEach(m => {
              try {
                if (!m.geometry.boundingBox) m.geometry.computeBoundingBox()
                const b = m.geometry.boundingBox
                const size = new THREE.Vector3().subVectors(b.max, b.min)
                const vol = size.x * size.y * size.z
                const center = new THREE.Vector3(); b.getCenter(center); m.localToWorld(center)
                candidates.push({ mesh: m, vol, center })
              } catch (e) { /* ignore */ }
            })

            if (candidates.length) {
              if (config.logoPlacement === 'front') {
                candidates.sort((a, b) => b.center.z - a.center.z)
              } else if (config.logoPlacement === 'back') {
                candidates.sort((a, b) => a.center.z - b.center.z)
              } else {
                candidates.sort((a, b) => b.vol - a.vol)
              }
              targetMesh = candidates[0].mesh
            }
          } else if (jersey) {
            jersey.traverse((c) => { if (!targetMesh && c.isMesh) targetMesh = c })
          }

        if (!targetMesh) {
          console.warn('No target mesh found for decal projection')
        } else {
          console.log('Using mesh for decal projection:', targetMesh.name || '(unnamed)')
          // create decal and add a small helper sphere at the decal point so the user can see placement
          const prevDecal = decalMesh
          createDecalOnMesh(targetMesh, texture, preservedQuat)
          if (decalMesh) {
            // mark decal position with a small helper
            try {
              const marker = new THREE.Mesh(new THREE.SphereGeometry(0.01, 8, 8), new THREE.MeshBasicMaterial({ color: 0xffff00 }))
              // place marker at decal mesh position if available
              marker.position.copy(decalMesh.position || new THREE.Vector3())
              marker.name = 'decal-marker'
              if (jersey) jersey.add(marker)
              // remove marker after a few seconds
              setTimeout(() => { try { if (marker.parent) marker.parent.remove(marker) } catch(e){} }, 3000)
            } catch (e) { console.warn('Could not add decal marker', e) }
          }
          // Ensure the visible logo pointer is set so updateElementsVisibility can hide/show it
          try { if (decalMesh) { logoMesh = decalMesh; logoMesh.name = 'logoMesh' } } catch(e) {}
        }

        updateElementsVisibility()
      })
    }

    // Update visibility based on current view
    updateElementsVisibility()
  }

  // Update jersey rotation based on current view
  function updateJerseyRotation() {
    // Do not rotate jersey automatically on view change to keep both sides visible
    // User can rotate freely with orbit controls
    // This fixes the issue where back logo is not visible in front view
    return
  }

  // Update elements visibility based on current view
  function updateElementsVisibility() {
    if (frontNumberMesh) {
      frontNumberMesh.visible = config.currentView === "front"
    }

    if (backNameMesh) {
      backNameMesh.visible = config.currentView === "back"
    }

    if (backNumberMesh) {
      backNumberMesh.visible = config.currentView === "back"
    }

    if (logoMesh) {
      // Make logo always visible regardless of current view
      logoMesh.visible = true
    }

    // Update UI panels
    if (config.currentView === "front") {
      frontOptions.style.display = "block"
      backOptions.style.display = "none"
      frontViewBtn.classList.add("bg-blue-600", "text-white")
      frontViewBtn.classList.remove("bg-gray-200", "text-gray-600")
      backViewBtn.classList.add("bg-gray-200", "text-gray-600")
      backViewBtn.classList.remove("bg-blue-600", "text-white")
    } else {
      frontOptions.style.display = "none"
      backOptions.style.display = "block"
      frontViewBtn.classList.add("bg-gray-200", "text-gray-600")
      frontViewBtn.classList.remove("bg-blue-600", "text-white")
      backViewBtn.classList.add("bg-blue-600", "text-white")
      backViewBtn.classList.remove("bg-gray-200", "text-gray-600")
    }
  }

  // Handle window resize
  function onWindowResize() {
    camera.aspect = canvasContainer.clientWidth / canvasContainer.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight)
  }

  // Animation loop
  function animate() {
    requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }

  // Multi-view download function
  async function downloadMultiViewDesign() {
    // Store original camera position and rotation
    const originalPosition = camera.position.clone()
    const originalRotation = jersey ? jersey.rotation.clone() : new THREE.Euler()
    const originalControlsEnabled = controls.enabled

    // Disable controls during capture
    controls.enabled = false

    // Define the views to capture
    const views = [
      { name: "front", position: [0, 0, 2.5], rotation: 0 },
      { name: "angle", position: [1.5, 0, 2], rotation: -Math.PI / 2},
      { name: "back", position: [0, 0, 2.5], rotation: Math.PI },
    ]

    // Create a canvas for the final layout
    const finalCanvas = document.createElement("canvas")
    const ctx = finalCanvas.getContext("2d")

    // Set canvas size for 3 views side by side
    finalCanvas.width = 1920 // 640 * 3
    finalCanvas.height = 640

    // Capture each view
    for (let i = 0; i < views.length; i++) {
      const view = views[i]

      // Set jersey rotation based on view
      if (jersey) {
        jersey.rotation.y = view.rotation
      }

      // Position camera for this view
      camera.position.set(view.position[0], view.position[1], view.position[2])

      // Update visibility of elements based on view
      if (frontNumberMesh) frontNumberMesh.visible = view.name !== "back"
      if (backNameMesh) backNameMesh.visible = view.name === "back"
      if (backNumberMesh) backNumberMesh.visible = view.name === "back"
      if (logoMesh) {
        if (view.name === "front" || view.name === "angle") {
          logoMesh.visible = config.logoPlacement === "front"
        } else {
          logoMesh.visible = config.logoPlacement === "back"
        }
      }

      // Render the scene
      renderer.render(scene, camera)

      // Get the image data
      const imageData = renderer.domElement.toDataURL("image/png")

      // Load the image
      const img = new Image()
      img.crossOrigin = "anonymous"
      await new Promise((resolve) => {
        img.onload = resolve
        img.src = imageData
      })

      // Draw the image to the final canvas
      ctx.drawImage(img, i * 640, 0, 640, 640)
    }

    // Restore original camera position and controls
    camera.position.copy(originalPosition)
    if (jersey) jersey.rotation.copy(originalRotation)
    controls.enabled = originalControlsEnabled

    // Download the combined image
    const link = document.createElement("a")
    link.download = "jersey-design.png"
    link.href = finalCanvas.toDataURL("image/png")
    link.click()
  }

  // Event listeners for UI controls
  if (jerseyTypeSelect) jerseyTypeSelect.addEventListener("change", function () {
    config.jerseyType = this.value

    // Update sleeve visibility based on jersey type
    sleeveMeshes.forEach(mesh => {
      mesh.visible = config.jerseyType !== "sleeveless";
    });
    applySleeveColor(); // Re-apply to ensure visibility affects color
  })

  if (frontViewBtn) frontViewBtn.addEventListener("click", () => {
    config.currentView = "front"
    updateJerseyRotation()
    updateElementsVisibility()
  })

  if (backViewBtn) backViewBtn.addEventListener("click", () => {
    config.currentView = "back"
    updateJerseyRotation()
    updateElementsVisibility()
  })

  if (primaryColorInput) primaryColorInput.addEventListener("input", function () {
    config.primaryColor = this.value
    applyBodyColor();
  })

  if (secondaryColorInput) secondaryColorInput.addEventListener("input", function () {
    config.secondaryColor = this.value
    applySleeveColor();
  })

  if (patternSelect) patternSelect.addEventListener("change", function () {
    config.pattern = this.value
    // Apply pattern to jersey (implementation depends on available patterns)
  })

  if (frontNumberInput) frontNumberInput.addEventListener("input", function () {
    config.frontNumber = this.value
    createTextElements()
  })

  if (backNameInput) backNameInput.addEventListener("input", function () {
    config.backName = this.value
    createTextElements()
  })

  if (backNumberInput) backNumberInput.addEventListener("input", function () {
    config.backNumber = this.value
    createTextElements()
  })

  if (textColorInput) textColorInput.addEventListener("input", function () {
    config.textColor = this.value
    createTextElements() // Recreate text elements with new color
  })

  if (logoUpload) logoUpload.addEventListener("change", (e) => {
    console.log("Logo upload change event triggered")
    if (e.target.files && e.target.files[0]) {
      const reader = new FileReader()
      reader.onload = (event) => {
        console.log("Logo file read as data URL")
            // store data URL and let createTextElements handle decal projection
            config.logo = event.target.result
            logoOptions.style.display = "block"
            // createTextElements will load the texture and project it as a decal
            createTextElements()
      }
      reader.readAsDataURL(e.target.files[0])
    }
  })

  if (logoSizeInput) logoSizeInput.addEventListener("input", function () {
    config.logoSize = Number.parseFloat(this.value)
    createTextElements() // Recreate logo with new size
  })

  if (logoPlacementSelect) logoPlacementSelect.addEventListener("change", function () {
    config.logoPlacement = this.value
    createTextElements()
  })

  // Number sliders removed; users drag numbers directly
  if (backNameXSlider) backNameXSlider.addEventListener("input", function () {
    config.backNamePosition.x = Number.parseFloat(this.value) - 0.5
    if (backNameMesh) {
      backNameMesh.position.x = config.backNamePosition.x
    }
  })

  if (backNameYSlider) backNameYSlider.addEventListener("input", function () {
    config.backNamePosition.y = Number.parseFloat(this.value) - 0.5
    if (backNameMesh) {
      backNameMesh.position.y = config.backNamePosition.y
    }
  })

  // Back number sliders removed; use drag

  if (logoXSlider) logoXSlider.addEventListener("input", function () {
    let newX = Number.parseFloat(this.value)
    // Clamp x to slider min/max from HTML (0.25 to 0.75)
    newX = Math.max(0.25, Math.min(0.75, newX))
    config.logoPosition.x = newX - 0.5
    this.value = newX
    createTextElements(); // Recreate decal with new position
  })

  if (logoYSlider) logoYSlider.addEventListener("input", function () {
    let newY = Number.parseFloat(this.value)
    // Clamp y to slider min/max from HTML (0.2 to 0.8)
    newY = Math.max(0.2, Math.min(0.8, newY))
    config.logoPosition.y = newY - 0.5
    this.value = newY
    createTextElements(); // Recreate decal with new position
  })

  if (resetViewBtn) resetViewBtn.addEventListener("click", () => {
    camera.position.set(0, 0, 2)
    controls.reset()
  })

  // Toggle dragging via button
  if (toggleDragBtn) {
    toggleDragBtn.addEventListener("click", () => {
      dragEnabled = !dragEnabled
      // Update button label and style
      if (dragEnabled) {
        toggleDragBtn.textContent = "Disable Drag"
        toggleDragBtn.classList.remove("bg-blue-600", "hover:bg-blue-700")
        toggleDragBtn.classList.add("bg-green-600", "hover:bg-green-700")
        // Disable orbit controls while drag mode is enabled
        if (controls) {
          controls.enabled = false
          if (typeof controls.enableRotate !== 'undefined') controls.enableRotate = false
          if (typeof controls.enablePan !== 'undefined') controls.enablePan = false
        }
        // Visual cue
        if (renderer && renderer.domElement) renderer.domElement.style.cursor = 'grab'
      } else {
        toggleDragBtn.textContent = "Enable Drag"
        toggleDragBtn.classList.remove("bg-green-600", "hover:bg-green-700")
        toggleDragBtn.classList.add("bg-blue-600", "hover:bg-blue-700")
        // Re-enable orbit controls when drag mode is disabled
        if (controls) {
          controls.enabled = true
          if (typeof controls.enableRotate !== 'undefined') controls.enableRotate = true
          if (typeof controls.enablePan !== 'undefined') controls.enablePan = true
        }
        if (renderer && renderer.domElement) renderer.domElement.style.cursor = 'default'
      }
    })
  }

  // Helper: pick target body mesh for a side
  function getBodyMeshForSide(side) {
    const candidates = []
    const pushCandidate = (m) => {
      try {
        if (!m.geometry) return
        if (!m.geometry.boundingBox) m.geometry.computeBoundingBox()
        const bb = m.geometry.boundingBox
        const size = new THREE.Vector3(); bb.getSize(size)
        const vol = Math.max(0.0001, size.x * size.y * size.z)
        const center = new THREE.Vector3(); bb.getCenter(center); m.localToWorld(center)
        candidates.push({ mesh: m, center, vol })
      } catch (e) { /* ignore */ }
    }
    if (bodyMeshes && bodyMeshes.length) bodyMeshes.forEach(pushCandidate)
    if (!candidates.length && jersey) jersey.traverse(obj => { if (obj.isMesh) pushCandidate(obj) })
    if (!candidates.length) return null
    candidates.sort((a, b) => {
      const zCmp = side === 'front' ? (b.center.z - a.center.z) : (a.center.z - b.center.z)
      return zCmp !== 0 ? zCmp : (b.vol - a.vol)
    })
    return candidates[0].mesh
  }

  // Enable dragging of number planes across the jersey surface
  function enableNumberDrag() {
    if (!renderer || !renderer.domElement) return
    const el = renderer.domElement

    function toNDC(e) {
      const rect = el.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width
      const y = (e.clientY - rect.top) / rect.height
      dragState.mouse.set(x * 2 - 1, -(y * 2 - 1))
    }

    function onPointerDown(e) {
      // If drag mode is enabled, block OrbitControls from handling this event
      if (dragEnabled) { try { e.stopPropagation() } catch {} }
      if (!dragEnabled) return
      toNDC(e)
      const picks = []
      if (frontNumberMesh && frontNumberMesh.visible !== false) picks.push(frontNumberMesh)
      if (backNumberMesh && backNumberMesh.visible !== false) picks.push(backNumberMesh)
      dragState.raycaster.setFromCamera(dragState.mouse, camera)
      const hits = dragState.raycaster.intersectObjects(picks, true)
      if (hits && hits.length) {
        let obj = hits[0].object
        while (obj && obj.parent && obj.parent !== scene && obj !== frontNumberMesh && obj !== backNumberMesh) obj = obj.parent
        dragState.target = (obj === frontNumberMesh || obj === backNumberMesh) ? obj : hits[0].object
        dragState.side = (dragState.target === frontNumberMesh) ? 'front' : 'back'
        dragState.isDragging = true
        // Disable orbit controls during drag
        if (controls) controls.enabled = false
        try { el.setPointerCapture(e.pointerId) } catch {}
        e.preventDefault()
      } else {
        // If user clicked on jersey surface, place the visible number there and start drag
        const activeSide = (frontNumberMesh && frontNumberMesh.visible !== false) ? 'front' : ((backNumberMesh && backNumberMesh.visible !== false) ? 'back' : null)
        if (!activeSide) return
        const targetMesh = getBodyMeshForSide(activeSide)
        if (!targetMesh) return
        const jerseyHits = dragState.raycaster.intersectObject(targetMesh, true)
        if (jerseyHits && jerseyHits.length) {
          const p = jerseyHits[0].point
          const n = jerseyHits[0].face ? jerseyHits[0].face.normal.clone().transformDirection(targetMesh.matrixWorld).normalize() : new THREE.Vector3(0, 0, activeSide === 'front' ? 1 : -1)
          const attachPos = p.clone().add(n.clone().multiplyScalar(0.01))
          const targetPlane = activeSide === 'front' ? frontNumberMesh : backNumberMesh
          if (!targetPlane) return
          targetPlane.position.copy(attachPos)
          const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), n)
          targetPlane.quaternion.copy(quat)
          const wp = attachPos
          if (activeSide === 'front') {
            config.frontNumberWorldPos = { x: wp.x, y: wp.y, z: wp.z }
          } else {
            config.backNumberWorldPos = { x: wp.x, y: wp.y, z: wp.z }
          }
          // Begin drag from placed position
          dragState.target = targetPlane
          dragState.side = activeSide
          dragState.isDragging = true
          if (controls) controls.enabled = false
          try { el.setPointerCapture(e.pointerId) } catch {}
          e.preventDefault()
        }
      }
    }

    function onPointerMove(e) {
      if (!dragState.isDragging || !dragState.target) return
      toNDC(e)
      const targetMesh = getBodyMeshForSide(dragState.side)
      if (!targetMesh) return
      dragState.raycaster.setFromCamera(dragState.mouse, camera)
      const hits = dragState.raycaster.intersectObject(targetMesh, true)
      if (hits && hits.length) {
        const p = hits[0].point
        const n = hits[0].face ? hits[0].face.normal.clone().transformDirection(targetMesh.matrixWorld).normalize() : new THREE.Vector3(0, 0, dragState.side === 'front' ? 1 : -1)
        const attachPos = p.clone().add(n.clone().multiplyScalar(0.01))
        dragState.target.position.copy(attachPos)
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), n)
        dragState.target.quaternion.copy(quat)
        const wp = attachPos
        if (dragState.side === 'front') {
          config.frontNumberWorldPos = { x: wp.x, y: wp.y, z: wp.z }
        } else {
          config.backNumberWorldPos = { x: wp.x, y: wp.y, z: wp.z }
        }
      }
    }

    function onPointerUp(e) {
      dragState.isDragging = false
      dragState.target = null
      dragState.side = null
      // Re-enable controls
      if (controls) {
        controls.enabled = !dragEnabled
        if (typeof controls.enableRotate !== 'undefined') controls.enableRotate = !dragEnabled
        if (typeof controls.enablePan !== 'undefined') controls.enablePan = !dragEnabled
      }
      try { el.releasePointerCapture(e.pointerId) } catch {}
    }

    // Use capture to intercept before OrbitControls listeners
    el.addEventListener('pointerdown', onPointerDown, { passive: false, capture: true })
    el.addEventListener('pointermove', onPointerMove, { passive: false, capture: true })
    el.addEventListener('pointerup', onPointerUp, { passive: false, capture: true })
    el.addEventListener('pointerleave', onPointerUp, { passive: false, capture: true })
  }
  if (clearAllBtn) clearAllBtn.addEventListener("click", () => {
    // Reset text inputs
    frontNumberInput.value = ""
    backNameInput.value = ""
    backNumberInput.value = ""

    // Reset config values
    config.frontNumber = ""
    config.backName = ""
    config.backNumber = ""
    config.logo = null
    config.logoPlacement = "front"

    // Reset positions
    config.backNamePosition = { x: 0, y: 0.2 }
    config.logoPosition = { x: 0, y: 0.35 }

    // Reset sliders
    backNameXSlider.value = 0.5
    backNameYSlider.value = 0.7
    logoXSlider.value = 0.5
    logoYSlider.value = 0.85
    logoPlacementSelect.value = "front"

    // Clear logo upload
    logoUpload.value = ""
    logoOptions.style.display = "none"

    // Restore any painted materials back to originals
    try { restorePaintedMaterials() } catch (e) { console.warn('restorePaintedMaterials call failed', e) }

    // Update 3D elements
    createTextElements()
  })

  function restorePaintedMaterials() {
    try {
      paintedMaterials.forEach((mat, uuid) => {
        const mesh = scene.getObjectByProperty('uuid', uuid)
        if (mesh) mesh.material = mat
      })
      paintedMaterials.clear()
    } catch (e) { console.warn('restorePaintedMaterials failed', e) }
  }

  if (downloadDesignBtn) downloadDesignBtn.addEventListener("click", () => {
    downloadMultiViewDesign()
  })

  // Function to apply body color to body meshes
  function applyBodyColor() {
    bodyMeshes.forEach(mesh => {
      try {
        // don't override if we've painted a logo into this mesh
        if (paintedMaterials.has(mesh.uuid)) {
          console.log('applyBodyColor: skipping painted mesh', mesh.name || mesh.uuid)
          return
        }

        // If material is already a standard material, just update its color
        if (mesh.material && mesh.material.isMeshStandardMaterial) {
          mesh.material.color.set(config.primaryColor)
          mesh.material.needsUpdate = true
        } else {
          // preserve any existing map if present
          const existingMap = (mesh.material && mesh.material.map) ? mesh.material.map : null
          const mat = new THREE.MeshStandardMaterial({ color: config.primaryColor })
          if (existingMap) mat.map = existingMap
          mesh.material = mat
        }
      } catch (e) {
        console.warn('applyBodyColor failed for mesh', mesh, e)
      }
    });
  }

  // Function to apply sleeve color to sleeve meshes (only if visible)
  function applySleeveColor() {
    sleeveMeshes.forEach(mesh => {
      try {
        // don't override painted meshes
        if (paintedMaterials.has(mesh.uuid)) {
          console.log('applySleeveColor: skipping painted mesh', mesh.name || mesh.uuid)
          return
        }

        if (config.jerseyType !== "sleeveless") {
          // Always assign a fresh material so sleeves do not share body material
          const existingMap = (mesh.material && mesh.material.map) ? mesh.material.map : null
          const newMat = new THREE.MeshStandardMaterial({ color: config.secondaryColor, side: THREE.DoubleSide })
          if (existingMap) newMat.map = existingMap
          mesh.material = newMat
        }
      } catch (e) { console.warn('applySleeveColor failed for mesh', mesh, e) }
    });
  }

  // Initialize the scene
  initScene()
  // Enable dragging after scene init
  enableNumberDrag()
})