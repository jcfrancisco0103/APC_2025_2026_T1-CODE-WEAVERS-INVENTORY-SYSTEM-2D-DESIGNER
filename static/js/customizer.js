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
    frontNumberPosition: { x: 0, y: 0, z: 0.05 },
    backNamePosition: { x: 0, y: 0.2, z: 0.05 },
    backNumberPosition: { x: 0, y: 0, z: 0.05 },
    logoPosition: { x: 0, y: 0, z: 0.05 },
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
  const clearAllBtn = document.getElementById("clear-all")
  const downloadDesignBtn = document.getElementById("download-design")

  // AI Features DOM elements
  const aiEnabledCheckbox = document.getElementById("ai-enabled")
  const aiControls = document.getElementById("ai-controls")
  const aiGenerationTypeSelect = document.getElementById("ai-generation-type")
  const aiCreativitySlider = document.getElementById("ai-creativity")
  const generateAiDesignBtn = document.getElementById("generate-ai-design")

  // Selection Mode DOM elements
  const selectionModeCheckbox = document.getElementById("selection-mode")
  const selectionInstructions = document.getElementById("selection-instructions")

// Position sliders
const frontNumberXSlider = document.getElementById("front-number-x")
const frontNumberYSlider = document.getElementById("front-number-y")
const frontNumberZSlider = document.getElementById("front-number-z")
const backNameXSlider = document.getElementById("back-name-x")
const backNameYSlider = document.getElementById("back-name-y")
const backNameZSlider = document.getElementById("back-name-z")
const backNumberXSlider = document.getElementById("back-number-x")
const backNumberYSlider = document.getElementById("back-number-y")
const backNumberZSlider = document.getElementById("back-number-z")
const logoXSlider = document.getElementById("logo-x")
const logoYSlider = document.getElementById("logo-y")
const logoZSlider = document.getElementById("logo-z")

  // Initialize Three.js scene
  function initScene() {
    // Create scene
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0x1a202c)

    // Create camera
    camera = new THREE.PerspectiveCamera(50, canvasContainer.clientWidth / canvasContainer.clientHeight, 0.1, 1000)
    camera.position.z = 2

    // Create renderer with enhanced visual quality
    renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      preserveDrawingBuffer: true,
      alpha: true,
      powerPreference: "high-performance"
    })
    renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    // Enhanced color space and tone mapping for realistic visuals
    try { 
      renderer.outputEncoding = THREE.sRGBEncoding 
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.2
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
      renderer.physicallyCorrectLights = true
    } catch (e) {}
    canvasContainer.appendChild(renderer.domElement)

    // Enhanced lighting setup for realistic visuals
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6)
    scene.add(ambientLight)

    // Primary directional light with shadows
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2)
    directionalLight.position.set(5, 10, 5)
    directionalLight.castShadow = true
    directionalLight.shadow.mapSize.width = 2048
    directionalLight.shadow.mapSize.height = 2048
    directionalLight.shadow.camera.near = 0.5
    directionalLight.shadow.camera.far = 50
    directionalLight.shadow.camera.left = -10
    directionalLight.shadow.camera.right = 10
    directionalLight.shadow.camera.top = 10
    directionalLight.shadow.camera.bottom = -10
    scene.add(directionalLight)
    
    // Secondary fill light for better illumination
    const fillLight = new THREE.DirectionalLight(0x87CEEB, 0.4)
    fillLight.position.set(-5, 5, -5)
    scene.add(fillLight)
    
    // Rim light for enhanced depth
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.3)
    rimLight.position.set(0, -5, -10)
    scene.add(rimLight)

    // Add grid helper
    gridHelper = new THREE.GridHelper(10, 10, 0x888888, 0x444444)
    gridHelper.position.y = -1
    scene.add(gridHelper)

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
    const modelPath = "/static/jersey_customizer/models/t_shirt.gltf"

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
      jersey.position.set(0, -1.4, 0.3)

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
        depthTest: true,
        depthWrite: true,
        alphaTest: 0.1
      })

      frontNumberMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(frontNumberMesh)
      // Position relative to jersey with increased z-offset to prevent bleeding
      frontNumberMesh.position.set(config.frontNumberPosition.x, config.frontNumberPosition.y, config.frontNumberPosition.z)
      frontNumberMesh.rotation.y = Math.PI // Ensure it faces forward
      // Ensure proper alignment for selection outline
      frontNumberMesh.userData.isTextElement = true
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
        depthTest: true,
        depthWrite: true,
        alphaTest: 0.1
      })

      backNameMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(backNameMesh)
      // Position relative to jersey with increased z-offset to prevent bleeding
      backNameMesh.position.set(config.backNamePosition.x, config.backNamePosition.y, config.backNamePosition.z)
      // Ensure proper alignment for selection outline
      backNameMesh.userData.isTextElement = true
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
        depthTest: true,
        depthWrite: true,
        alphaTest: 0.1
      })

      backNumberMesh = new THREE.Mesh(geometry, material)
      // Attach to jersey so it moves with it
      jersey.add(backNumberMesh)
      // Position relative to jersey with increased z-offset to prevent bleeding
      backNumberMesh.position.set(config.backNumberPosition.x, config.backNumberPosition.y, config.backNumberPosition.z)
      // Ensure proper alignment for selection outline
      backNumberMesh.userData.isTextElement = true
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
              const posZ = THREE.MathUtils.lerp(bbox.min.z, bbox.max.z, 0.5) + config.logoPosition.z
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
  jerseyTypeSelect.addEventListener("change", function () {
    config.jerseyType = this.value

    // Update sleeve visibility based on jersey type
    sleeveMeshes.forEach(mesh => {
      mesh.visible = config.jerseyType !== "sleeveless";
    });
    applySleeveColor(); // Re-apply to ensure visibility affects color
  })

  frontViewBtn.addEventListener("click", () => {
    config.currentView = "front"
    updateJerseyRotation()
    updateElementsVisibility()
  })

  backViewBtn.addEventListener("click", () => {
    config.currentView = "back"
    updateJerseyRotation()
    updateElementsVisibility()
  })

  primaryColorInput.addEventListener("input", function () {
    config.primaryColor = this.value
    applyBodyColor();
  })

  secondaryColorInput.addEventListener("input", function () {
    config.secondaryColor = this.value
    applySleeveColor();
  })

  patternSelect.addEventListener("change", function () {
    config.pattern = this.value
    applyPattern(this.value)
  })

  // Apply pattern function
  function applyPattern(pattern) {
    if (!jersey) return
    
    // Remove existing pattern materials and restore original colors
    bodyMeshes.forEach(mesh => {
      if (mesh.userData.originalMaterial) {
        mesh.material = mesh.userData.originalMaterial.clone()
        delete mesh.userData.originalMaterial
      }
    })
    sleeveMeshes.forEach(mesh => {
      if (mesh.userData.originalMaterial) {
        mesh.material = mesh.userData.originalMaterial.clone()
        delete mesh.userData.originalMaterial
      }
    })
    
    // Apply new pattern based on selection
    switch(pattern) {
      case 'stripes':
        applyStripesPattern()
        break
      case 'dots':
        applyDotsPattern()
        break
      case 'geometric':
        applyGeometricPattern()
        break
      case 'gradient':
        applyGradientPattern()
        break
      case 'none':
      default:
        // Keep original colors without pattern
        applyBodyColor()
        applySleeveColor()
        break
    }
  }

  // Pattern application functions
  function applyStripesPattern() {
    // Create striped texture
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    const ctx = canvas.getContext('2d')
    
    // Draw stripes
    ctx.fillStyle = config.primaryColor
    ctx.fillRect(0, 0, 256, 256)
    ctx.fillStyle = config.secondaryColor
    for (let i = 0; i < 256; i += 32) {
      ctx.fillRect(0, i, 256, 16)
    }
    
    const texture = new THREE.CanvasTexture(canvas)
    texture.wrapS = THREE.RepeatWrapping
    texture.wrapT = THREE.RepeatWrapping
    texture.repeat.set(2, 2)
    
    applyPatternTexture(texture)
  }

  function applyDotsPattern() {
    // Create dotted texture
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    const ctx = canvas.getContext('2d')
    
    // Draw dots
    ctx.fillStyle = config.primaryColor
    ctx.fillRect(0, 0, 256, 256)
    ctx.fillStyle = config.secondaryColor
    for (let x = 16; x < 256; x += 32) {
      for (let y = 16; y < 256; y += 32) {
        ctx.beginPath()
        ctx.arc(x, y, 8, 0, Math.PI * 2)
        ctx.fill()
      }
    }
    
    const texture = new THREE.CanvasTexture(canvas)
    texture.wrapS = THREE.RepeatWrapping
    texture.wrapT = THREE.RepeatWrapping
    texture.repeat.set(3, 3)
    
    applyPatternTexture(texture)
  }

  function applyGeometricPattern() {
    // Create geometric texture
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    const ctx = canvas.getContext('2d')
    
    // Draw geometric pattern
    ctx.fillStyle = config.primaryColor
    ctx.fillRect(0, 0, 256, 256)
    ctx.fillStyle = config.secondaryColor
    for (let x = 0; x < 256; x += 64) {
      for (let y = 0; y < 256; y += 64) {
        ctx.fillRect(x + 16, y + 16, 32, 32)
      }
    }
    
    const texture = new THREE.CanvasTexture(canvas)
    texture.wrapS = THREE.RepeatWrapping
    texture.wrapT = THREE.RepeatWrapping
    texture.repeat.set(2, 2)
    
    applyPatternTexture(texture)
  }

  function applyGradientPattern() {
    // Create high-resolution gradient texture for better quality
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 512
    const ctx = canvas.getContext('2d')
    
    // Enhanced gradient with multiple options
    const gradientType = config.gradientType || 'linear' // linear, radial, diagonal
    const gradientDirection = config.gradientDirection || 'horizontal' // horizontal, vertical, diagonal
    
    let gradient
    
    switch(gradientType) {
      case 'radial':
        // Radial gradient from center
        gradient = ctx.createRadialGradient(256, 256, 0, 256, 256, 256)
        break
      case 'diagonal':
        // Diagonal gradient
        gradient = ctx.createLinearGradient(0, 0, 512, 512)
        break
      case 'linear':
      default:
        // Linear gradient based on direction
        switch(gradientDirection) {
          case 'vertical':
            gradient = ctx.createLinearGradient(0, 0, 0, 512)
            break
          case 'diagonal':
            gradient = ctx.createLinearGradient(0, 0, 512, 512)
            break
          case 'horizontal':
          default:
            gradient = ctx.createLinearGradient(0, 0, 512, 0)
            break
        }
        break
    }
    
    // Enhanced color stops for smoother transitions
    gradient.addColorStop(0, config.primaryColor)
    gradient.addColorStop(0.25, blendColors(config.primaryColor, config.secondaryColor, 0.25))
    gradient.addColorStop(0.5, blendColors(config.primaryColor, config.secondaryColor, 0.5))
    gradient.addColorStop(0.75, blendColors(config.primaryColor, config.secondaryColor, 0.75))
    gradient.addColorStop(1, config.secondaryColor)
    
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, 512, 512)
    
    // Create texture with enhanced properties
    const texture = new THREE.CanvasTexture(canvas)
    texture.wrapS = THREE.RepeatWrapping
    texture.wrapT = THREE.RepeatWrapping
    texture.repeat.set(1, 1)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.generateMipmaps = true
    texture.needsUpdate = true
    
    applyPatternTexture(texture)
  }
  
  // Helper function to blend colors for smoother gradients
  function blendColors(color1, color2, ratio) {
    // Convert hex colors to RGB
    const hex1 = color1.replace('#', '')
    const hex2 = color2.replace('#', '')
    
    const r1 = parseInt(hex1.substr(0, 2), 16)
    const g1 = parseInt(hex1.substr(2, 2), 16)
    const b1 = parseInt(hex1.substr(4, 2), 16)
    
    const r2 = parseInt(hex2.substr(0, 2), 16)
    const g2 = parseInt(hex2.substr(2, 2), 16)
    const b2 = parseInt(hex2.substr(4, 2), 16)
    
    // Blend the colors
    const r = Math.round(r1 + (r2 - r1) * ratio)
    const g = Math.round(g1 + (g2 - g1) * ratio)
    const b = Math.round(b1 + (b2 - b1) * ratio)
    
    // Convert back to hex
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }

  function applyPatternTexture(texture) {
    // Apply pattern to body meshes
    bodyMeshes.forEach(mesh => {
      // Store original material if not already stored
      if (!mesh.userData.originalMaterial) {
        mesh.userData.originalMaterial = mesh.material.clone()
      }
      
      // Create new material with pattern texture
      const material = new THREE.MeshStandardMaterial({
        map: texture,
        roughness: 0.8,
        metalness: 0.1,
        envMapIntensity: 0.5,
        normalScale: new THREE.Vector2(0.5, 0.5)
      })
      
      mesh.material = material
    })
    
    // Apply pattern to sleeve meshes if visible
    if (config.jerseyType !== "sleeveless") {
      sleeveMeshes.forEach(mesh => {
        // Store original material if not already stored
        if (!mesh.userData.originalMaterial) {
          mesh.userData.originalMaterial = mesh.material.clone()
        }
        
        // Create new material with pattern texture
        const material = new THREE.MeshStandardMaterial({
          map: texture,
          roughness: 0.8,
          metalness: 0.1,
          envMapIntensity: 0.5,
          normalScale: new THREE.Vector2(0.5, 0.5),
          side: THREE.DoubleSide
        })
        
        mesh.material = material
      })
    }
  }

  frontNumberInput.addEventListener("input", function () {
    config.frontNumber = this.value
    createTextElements()
  })

  backNameInput.addEventListener("input", function () {
    config.backName = this.value
    createTextElements()
  })

  backNumberInput.addEventListener("input", function () {
    config.backNumber = this.value
    createTextElements()
  })

  textColorInput.addEventListener("input", function () {
    config.textColor = this.value
    createTextElements() // Recreate text elements with new color
  })

  logoUpload.addEventListener("change", (e) => {
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

  logoSizeInput.addEventListener("input", function () {
    config.logoSize = Number.parseFloat(this.value)
    createTextElements() // Recreate logo with new size
  })

  logoPlacementSelect.addEventListener("change", function () {
    config.logoPlacement = this.value
    createTextElements()
  })

  // Position slider event listeners
  frontNumberXSlider.addEventListener("input", function () {
    config.frontNumberPosition.x = Number.parseFloat(this.value) - 0.5
    if (frontNumberMesh) {
      frontNumberMesh.position.x = config.frontNumberPosition.x
    }
  })

  frontNumberYSlider.addEventListener("input", function () {
    config.frontNumberPosition.y = Number.parseFloat(this.value) - 0.5
    if (frontNumberMesh) {
      frontNumberMesh.position.y = config.frontNumberPosition.y
    }
  })

  backNameXSlider.addEventListener("input", function () {
    config.backNamePosition.x = Number.parseFloat(this.value) - 0.5
    if (backNameMesh) {
      backNameMesh.position.x = config.backNamePosition.x
    }
  })

  backNameYSlider.addEventListener("input", function () {
    config.backNamePosition.y = Number.parseFloat(this.value) - 0.5
    if (backNameMesh) {
      backNameMesh.position.y = config.backNamePosition.y
    }
  })

  backNumberXSlider.addEventListener("input", function () {
    config.backNumberPosition.x = Number.parseFloat(this.value) - 0.5
    if (backNumberMesh) {
      backNumberMesh.position.x = config.backNumberPosition.x
    }
  })

  backNumberYSlider.addEventListener("input", function () {
    config.backNumberPosition.y = Number.parseFloat(this.value) - 0.5
    if (backNumberMesh) {
      backNumberMesh.position.y = config.backNumberPosition.y
    }
  })

  frontNumberZSlider.addEventListener("input", function () {
    config.frontNumberPosition.z = Number.parseFloat(this.value)
    if (frontNumberMesh) {
      frontNumberMesh.position.z = config.frontNumberPosition.z
    }
  })

  backNameZSlider.addEventListener("input", function () {
    config.backNamePosition.z = Number.parseFloat(this.value)
    if (backNameMesh) {
      backNameMesh.position.z = config.backNamePosition.z
    }
  })

  backNumberZSlider.addEventListener("input", function () {
    config.backNumberPosition.z = Number.parseFloat(this.value)
    if (backNumberMesh) {
      backNumberMesh.position.z = config.backNumberPosition.z
    }
  })

  logoXSlider.addEventListener("input", function () {
    let newX = Number.parseFloat(this.value)
    // Clamp x to slider min/max from HTML (0.25 to 0.75)
    newX = Math.max(0.25, Math.min(0.75, newX))
    config.logoPosition.x = newX - 0.5
    this.value = newX
    createTextElements(); // Recreate decal with new position
  })

  logoYSlider.addEventListener("input", function () {
    let newY = Number.parseFloat(this.value)
    // Clamp y to slider min/max from HTML (0.2 to 0.8)
    newY = Math.max(0.2, Math.min(0.8, newY))
    config.logoPosition.y = newY - 0.5
    this.value = newY
    createTextElements(); // Recreate decal with new position
  })

  logoZSlider.addEventListener("input", function () {
    let newZ = Number.parseFloat(this.value)
    // Clamp z to slider min/max from HTML (0.01 to 2.0)
    newZ = Math.max(0.01, Math.min(2.0, newZ))
    config.logoPosition.z = newZ
    this.value = newZ
    createTextElements(); // Recreate decal with new position
  })

  resetViewBtn.addEventListener("click", () => {
    camera.position.set(0, 0, 2)
    controls.reset()
  })

  clearAllBtn.addEventListener("click", () => {
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
    config.frontNumberPosition = { x: 0, y: 0 }
    config.backNamePosition = { x: 0, y: 0.2 }
    config.backNumberPosition = { x: 0, y: 0 }
    config.logoPosition = { x: 0, y: 0.35 }

    // Reset sliders
    frontNumberXSlider.value = 0.5
    frontNumberYSlider.value = 0.5
    backNameXSlider.value = 0.5
    backNameYSlider.value = 0.7
    backNumberXSlider.value = 0.5
    backNumberYSlider.value = 0.5
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

  downloadDesignBtn.addEventListener("click", () => {
    downloadMultiViewDesign()
  })

  // AI Features Event Listeners
  aiEnabledCheckbox.addEventListener("change", function() {
    if (this.checked) {
      aiControls.style.display = "block"
    } else {
      aiControls.style.display = "none"
    }
  })

  generateAiDesignBtn.addEventListener("click", function() {
    const generationType = aiGenerationTypeSelect.value
    const creativityLevel = parseInt(aiCreativitySlider.value)
    generateAIDesign(generationType, creativityLevel)
  })

  // Selection Mode Event Listeners
  selectionModeCheckbox.addEventListener("change", function() {
    selectionMode = this.checked
    if (selectionMode) {
      selectionInstructions.style.display = "block"
      // Disable orbit controls when selection mode is active
      if (controls) controls.enabled = false
    } else {
      selectionInstructions.style.display = "none"
      selectedElement = null
      clearElementSelection()
      // Re-enable orbit controls
      if (controls) controls.enabled = true
    }
  })

  // Event listeners will be added after initScene() is called

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
          // Enhanced material with realistic properties
          const mat = new THREE.MeshStandardMaterial({ 
            color: config.primaryColor,
            roughness: 0.7,
            metalness: 0.1,
            envMapIntensity: 0.5,
            normalScale: new THREE.Vector2(0.5, 0.5)
          })
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
          // Enhanced sleeve material with realistic properties
          const newMat = new THREE.MeshStandardMaterial({ 
            color: config.secondaryColor, 
            side: THREE.DoubleSide,
            roughness: 0.7,
            metalness: 0.1,
            envMapIntensity: 0.5,
            normalScale: new THREE.Vector2(0.5, 0.5)
          })
          if (existingMap) newMat.map = existingMap
          mesh.material = newMat
        }
      } catch (e) { console.warn('applySleeveColor failed for mesh', mesh, e) }
    });
  }

  // Initialize the scene
  initScene()

  // Add event listeners after renderer is initialized
  if (renderer && renderer.domElement) {
    // Mouse click event for selection mode
    renderer.domElement.addEventListener('click', onMouseClick, false)
  }

  // Keyboard event listeners for WASD controls
  document.addEventListener('keydown', onKeyDown, false)

  // AI Design Generation Function
  function generateAIDesign(generationType, creativityLevel) {
    console.log(`Generating AI design: ${generationType} with creativity level ${creativityLevel}`)
    
    switch(generationType) {
      case 'color-scheme':
        generateSmartColorScheme(creativityLevel)
        break
      case 'pattern-match':
        generatePatternMatch(creativityLevel)
        break
      case 'team-style':
        generateTeamStyle(creativityLevel)
        break
      case 'random-design':
        generateRandomDesign(creativityLevel)
        break
    }
  }

  function generateSmartColorScheme(creativityLevel) {
    const colorSchemes = [
      { primary: '#FF6B6B', secondary: '#4ECDC4' }, // Coral & Teal
      { primary: '#45B7D1', secondary: '#96CEB4' }, // Sky Blue & Mint
      { primary: '#F7DC6F', secondary: '#BB8FCE' }, // Yellow & Purple
      { primary: '#58D68D', secondary: '#F8C471' }, // Green & Orange
      { primary: '#EC7063', secondary: '#85C1E9' }  // Red & Light Blue
    ]
    
    const scheme = colorSchemes[Math.floor(Math.random() * colorSchemes.length)]
    
    // Apply colors with some randomization based on creativity level
    if (creativityLevel > 5) {
      // Higher creativity - more variation
      const hueShift = (Math.random() - 0.5) * (creativityLevel * 10)
      scheme.primary = adjustHue(scheme.primary, hueShift)
      scheme.secondary = adjustHue(scheme.secondary, hueShift)
    }
    
    primaryColorInput.value = scheme.primary
    secondaryColorInput.value = scheme.secondary
    config.primaryColor = scheme.primary
    config.secondaryColor = scheme.secondary
    
    applyBodyColor()
    applySleeveColor()
  }

  function generatePatternMatch(creativityLevel) {
    const patterns = ['stripes', 'dots', 'geometric', 'gradient']
    const randomPattern = patterns[Math.floor(Math.random() * patterns.length)]
    
    if (patternSelect) {
      // Find matching option in select
      for (let option of patternSelect.options) {
        if (option.value.toLowerCase().includes(randomPattern)) {
          patternSelect.value = option.value
          config.pattern = option.value
          break
        }
      }
    }
  }

  function generateTeamStyle(creativityLevel) {
    // Generate team-like combinations
    const teamColors = [
      { primary: '#1E3A8A', secondary: '#FFFFFF' }, // Navy & White
      { primary: '#DC2626', secondary: '#FBBF24' }, // Red & Gold
      { primary: '#059669', secondary: '#FFFFFF' }, // Green & White
      { primary: '#7C2D12', secondary: '#FED7AA' }, // Brown & Cream
      { primary: '#1F2937', secondary: '#F59E0B' }  // Dark Gray & Orange
    ]
    
    const teamStyle = teamColors[Math.floor(Math.random() * teamColors.length)]
    
    primaryColorInput.value = teamStyle.primary
    secondaryColorInput.value = teamStyle.secondary
    config.primaryColor = teamStyle.primary
    config.secondaryColor = teamStyle.secondary
    
    // Add team number and name
    if (creativityLevel > 7) {
      frontNumberInput.value = Math.floor(Math.random() * 99) + 1
      backNameInput.value = 'PLAYER'
      backNumberInput.value = Math.floor(Math.random() * 99) + 1
      
      config.frontNumber = frontNumberInput.value
      config.backName = backNameInput.value
      config.backNumber = backNumberInput.value
    }
    
    applyBodyColor()
    applySleeveColor()
    createTextElements()
  }

  function generateRandomDesign(creativityLevel) {
    // Generate completely random design
    const randomPrimary = `#${Math.floor(Math.random()*16777215).toString(16).padStart(6, '0')}`
    const randomSecondary = `#${Math.floor(Math.random()*16777215).toString(16).padStart(6, '0')}`
    
    primaryColorInput.value = randomPrimary
    secondaryColorInput.value = randomSecondary
    config.primaryColor = randomPrimary
    config.secondaryColor = randomSecondary
    
    if (creativityLevel > 5) {
      frontNumberInput.value = Math.floor(Math.random() * 99) + 1
      config.frontNumber = frontNumberInput.value
    }
    
    if (creativityLevel > 7) {
      const names = ['ACE', 'STAR', 'PRO', 'HERO', 'CHAMP']
      backNameInput.value = names[Math.floor(Math.random() * names.length)]
      backNumberInput.value = Math.floor(Math.random() * 99) + 1
      
      config.backName = backNameInput.value
      config.backNumber = backNumberInput.value
    }
    
    applyBodyColor()
    applySleeveColor()
    createTextElements()
  }

  function adjustHue(hexColor, hueShift) {
    // Convert hex to HSL, adjust hue, convert back
    const r = parseInt(hexColor.slice(1, 3), 16) / 255
    const g = parseInt(hexColor.slice(3, 5), 16) / 255
    const b = parseInt(hexColor.slice(5, 7), 16) / 255
    
    const max = Math.max(r, g, b)
    const min = Math.min(r, g, b)
    let h, s, l = (max + min) / 2
    
    if (max === min) {
      h = s = 0
    } else {
      const d = max - min
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break
        case g: h = (b - r) / d + 2; break
        case b: h = (r - g) / d + 4; break
      }
      h /= 6
    }
    
    h = (h + hueShift / 360) % 1
    if (h < 0) h += 1
    
    // Convert back to RGB
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1
      if (t > 1) t -= 1
      if (t < 1/6) return p + (q - p) * 6 * t
      if (t < 1/2) return q
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
      return p
    }
    
    let newR, newG, newB
    if (s === 0) {
      newR = newG = newB = l
    } else {
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s
      const p = 2 * l - q
      newR = hue2rgb(p, q, h + 1/3)
      newG = hue2rgb(p, q, h)
      newB = hue2rgb(p, q, h - 1/3)
    }
    
    return `#${Math.round(newR * 255).toString(16).padStart(2, '0')}${Math.round(newG * 255).toString(16).padStart(2, '0')}${Math.round(newB * 255).toString(16).padStart(2, '0')}`
  }

  // Selection Mode Functions
  function onMouseClick(event) {
    if (!selectionMode) return
    
    // Calculate mouse position in normalized device coordinates
    const rect = renderer.domElement.getBoundingClientRect()
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
    
    // Update the picking ray with the camera and mouse position
    raycaster.setFromCamera(mouse, camera)
    
    // Calculate objects intersecting the picking ray
    const selectableObjects = []
    if (frontNumberMesh && frontNumberMesh.visible) selectableObjects.push(frontNumberMesh)
    if (backNameMesh && backNameMesh.visible) selectableObjects.push(backNameMesh)
    if (backNumberMesh && backNumberMesh.visible) selectableObjects.push(backNumberMesh)
    
    const intersects = raycaster.intersectObjects(selectableObjects)
    
    if (intersects.length > 0) {
      // Select the clicked element
      selectedElement = intersects[0].object
      highlightSelectedElement()
    } else {
      // Deselect if clicking on empty space
      selectedElement = null
      clearElementSelection()
    }
  }

  function onKeyDown(event) {
    if (!selectionMode || !selectedElement) return
    
    const moveDistance = 0.02
    let moved = false
    
    switch(event.code) {
      case 'KeyW':
        selectedElement.position.y += moveDistance
        moved = true
        break
      case 'KeyS':
        selectedElement.position.y -= moveDistance
        moved = true
        break
      case 'KeyA':
        selectedElement.position.x -= moveDistance
        moved = true
        break
      case 'KeyD':
        selectedElement.position.x += moveDistance
        moved = true
        break
    }
    
    if (moved) {
      event.preventDefault()
      updateConfigFromElementPosition()
    }
  }

  function highlightSelectedElement() {
    // Clear previous highlights
    clearElementSelection()
    
    if (selectedElement) {
      // Add green outline material
      const outlineMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ff00,
        side: THREE.BackSide,
        transparent: true,
        opacity: 0.4, // Increased opacity for better visibility
        depthTest: false, // Ensure outline is always visible
        depthWrite: false
      })
      
      // Create outline mesh
      const outlineGeometry = selectedElement.geometry.clone()
      const outlineMesh = new THREE.Mesh(outlineGeometry, outlineMaterial)
      outlineMesh.position.copy(selectedElement.position)
      // Ensure outline is perfectly aligned with the numerical element
      outlineMesh.rotation.copy(selectedElement.rotation)
      outlineMesh.scale.multiplyScalar(1.05) // Reduced scale for tighter alignment
      outlineMesh.name = 'selection-outline'
      
      scene.add(outlineMesh)
    }
  }

  function clearElementSelection() {
    // Remove selection outline
    const outline = scene.getObjectByName('selection-outline')
    if (outline) {
      scene.remove(outline)
    }
  }

  function updateConfigFromElementPosition() {
    if (!selectedElement) return
    
    // Update config based on which element is selected
    if (selectedElement === frontNumberMesh) {
      config.frontNumberPosition.x = selectedElement.position.x
      config.frontNumberPosition.y = selectedElement.position.y
      config.frontNumberPosition.z = selectedElement.position.z
    } else if (selectedElement === backNameMesh) {
      config.backNamePosition.x = selectedElement.position.x
      config.backNamePosition.y = selectedElement.position.y
      config.backNamePosition.z = selectedElement.position.z
    } else if (selectedElement === backNumberMesh) {
      config.backNumberPosition.x = selectedElement.position.x
      config.backNumberPosition.y = selectedElement.position.y
      config.backNumberPosition.z = selectedElement.position.z
    } else if (selectedElement === logoMesh || selectedElement === decalMesh) {
      // For logo/decal, we need to convert world position back to relative position
      // This is a simplified approach - in practice, you might need more complex conversion
      config.logoPosition.z = selectedElement.position.z
    }
  }

  // Color preset functionality for enhanced visual appeal
  function initializeColorPresets() {
    // Body color presets
    const colorPresets = document.querySelectorAll('.color-preset')
    colorPresets.forEach(preset => {
      preset.addEventListener('click', function() {
        const color = this.getAttribute('data-color')
        primaryColorInput.value = color
        config.primaryColor = color
        applyBodyColor()
      })
    })

    // Sleeve color presets
    const sleeveColorPresets = document.querySelectorAll('.sleeve-color-preset')
    sleeveColorPresets.forEach(preset => {
      preset.addEventListener('click', function() {
        const color = this.getAttribute('data-color')
        secondaryColorInput.value = color
        config.secondaryColor = color
        applySleeveColor()
      })
    })
  }

  // Professional color scheme combinations
  function applyProfessionalColorScheme(scheme) {
    const professionalSchemes = {
      'classic': { primary: '#1A237E', secondary: '#FFFFFF' }, // Navy & White
      'vibrant': { primary: '#FF1744', secondary: '#FFD600' }, // Red & Gold
      'modern': { primary: '#37474F', secondary: '#00C853' }, // Gray & Green
      'elegant': { primary: '#4A148C', secondary: '#E1BEE7' }, // Purple & Light Purple
      'bold': { primary: '#FF6B35', secondary: '#004E89' }, // Orange & Blue
      'sporty': { primary: '#00C853', secondary: '#212121' }, // Green & Black
      'premium': { primary: '#B71C1C', secondary: '#F57F17' }, // Crimson & Gold
      'dynamic': { primary: '#7C4DFF', secondary: '#FF5722' }  // Purple & Orange
    }

    if (professionalSchemes[scheme]) {
      const colors = professionalSchemes[scheme]
      primaryColorInput.value = colors.primary
      secondaryColorInput.value = colors.secondary
      config.primaryColor = colors.primary
      config.secondaryColor = colors.secondary
      applyBodyColor()
      applySleeveColor()
    }
  }

  // Initialize professional color scheme presets
  function initializeProfessionalSchemes() {
    const schemePresets = document.querySelectorAll('.scheme-preset')
    schemePresets.forEach(preset => {
      preset.addEventListener('click', function() {
        const scheme = this.getAttribute('data-scheme')
        applyProfessionalColorScheme(scheme)
      })
    })
  }

  // Initialize color presets and professional schemes
  initializeColorPresets()
  initializeProfessionalSchemes()
})

// Selection mode variables
let selectionMode = false
let selectedElement = null
let raycaster = new THREE.Raycaster()
let mouse = new THREE.Vector2()