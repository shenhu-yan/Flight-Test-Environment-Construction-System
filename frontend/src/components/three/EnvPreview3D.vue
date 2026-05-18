<template>
  <div class="preview-3d" ref="containerRef">
    <canvas ref="canvasRef"></canvas>
    <div class="layer-toggle">
      <div class="layer-title">图层控制</div>
      <el-switch v-model="layers.terrain" active-text="地形" size="small" @change="toggleLayer('terrain')" />
      <el-switch v-model="layers.obstacles" active-text="障碍物" size="small" @change="toggleLayer('obstacles')" />
      <el-switch v-model="layers.waypoints" active-text="航点" size="small" @change="toggleLayer('waypoints')" />
      <el-switch v-model="layers.weather" active-text="天气" size="small" @change="toggleLayer('weather')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, reactive } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

interface SceneData {
  terrain?: { elevation?: number[][]; size?: number; resolution?: number }
  obstacles?: Array<{ type: string; position: number[]; scale?: number[] }>
  waypoints?: Array<{ position: number[]; order?: number; id?: string }>
  wind?: { speed: number; direction: number; particles?: Array<{ position: number[] }> }
  runway?: { position: number[]; length: number; width: number; heading?: number }
}

const props = withDefaults(defineProps<{
  config?: any
  sceneData?: SceneData
}>(), {
  config: null,
  sceneData: () => ({})
})

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationId: number

const layers = reactive({
  terrain: true,
  obstacles: true,
  waypoints: true,
  weather: true
})

const layerGroups: Record<string, THREE.Group> = {}

function toggleLayer(name: string) {
  if (layerGroups[name]) {
    layerGroups[name].visible = layers[name as keyof typeof layers]
  }
}

function initScene() {
  if (!canvasRef.value || !containerRef.value) return

  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  camera = new THREE.PerspectiveCamera(60, w / h, 1, 10000)
  camera.position.set(500, 400, 500)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(window.devicePixelRatio)

  controls = new OrbitControls(camera, canvasRef.value)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.maxPolarAngle = Math.PI / 2.1

  // Lighting
  scene.add(new THREE.AmbientLight(0x404060, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(300, 500, 200)
  scene.add(dirLight)

  // Grid helper
  const grid = new THREE.GridHelper(2000, 40, 0x333355, 0x222244)
  scene.add(grid)

  // Create layer groups
  layerGroups.terrain = new THREE.Group()
  layerGroups.obstacles = new THREE.Group()
  layerGroups.waypoints = new THREE.Group()
  layerGroups.weather = new THREE.Group()
  Object.values(layerGroups).forEach(g => scene.add(g))

  buildScene()
  animate()
}

function buildScene() {
  buildTerrain()
  buildObstacles()
  buildWaypoints()
  buildWind()
  buildRunway()
}

function buildTerrain() {
  const group = layerGroups.terrain
  if (!group) return
  group.clear()

  const sd = props.sceneData
  const cfg = props.config
  const size = sd?.terrain?.size || 2000
  const segments = 64
  const geometry = new THREE.PlaneGeometry(size, size, segments, segments)
  geometry.rotateX(-Math.PI / 2)

  const positions = geometry.attributes.position
  const elevMin = cfg?.terrain?.elevation_min ?? 0
  const elevMax = cfg?.terrain?.elevation_max ?? 100

  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i)
    const z = positions.getZ(i)
    // Use sceneData elevation if available, else generate from config
    if (sd?.terrain?.elevation) {
      const grid = sd.terrain.elevation
      const res = sd.terrain.resolution || grid.length
      const gi = Math.floor(((x / size) + 0.5) * (res - 1))
      const gj = Math.floor(((z / size) + 0.5) * (res - 1))
      const row = Math.max(0, Math.min(grid.length - 1, gj))
      const col = Math.max(0, Math.min((grid[0]?.length || 1) - 1, gi))
      positions.setY(i, (grid[row]?.[col] ?? 0) * 0.5)
    } else {
      const height = elevMin + Math.random() * (elevMax - elevMin) *
        (Math.sin(x * 0.005) * 0.5 + Math.cos(z * 0.003) * 0.5 + 0.5)
      positions.setY(i, height * 0.5)
    }
  }
  geometry.computeVertexNormals()

  // Vertex coloring based on height
  const colors = new Float32Array(positions.count * 3)
  for (let i = 0; i < positions.count; i++) {
    const y = positions.getY(i)
    const t = Math.max(0, Math.min(1, (y - elevMin * 0.25) / ((elevMax - elevMin) * 0.5 + 0.01)))
    colors[i * 3] = 0.2 + t * 0.1
    colors[i * 3 + 1] = 0.5 - t * 0.3
    colors[i * 3 + 2] = 0.2
  }
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.MeshLambertMaterial({ vertexColors: true })
  const mesh = new THREE.Mesh(geometry, material)
  group.add(mesh)
}

function buildObstacles() {
  const group = layerGroups.obstacles
  if (!group) return
  group.clear()

  const obstacles = props.sceneData?.obstacles || []
  const cfg = props.config?.obstacles
  const count = obstacles.length || cfg?.count || 0
  if (!count) return

  const colorMap: Record<string, number> = {
    building: 0x5566aa,
    power_tower: 0x888888,
    tree: 0x228833,
    mountain: 0x665544,
    bird: 0xff6644,
    drone: 0xffaa00,
  }

  const types = cfg?.types || ['building', 'tree', 'mountain']

  for (let i = 0; i < count; i++) {
    let pos: number[], type: string, scale: number[]
    if (obstacles[i]) {
      pos = obstacles[i].position
      type = obstacles[i].type
      scale = obstacles[i].scale || [1, 1, 1]
    } else {
      type = types[i % types.length]
      pos = [(Math.random() - 0.5) * 1600, 0, (Math.random() - 0.5) * 1600]
      scale = [1, 1, 1]
    }

    const color = colorMap[type] || 0x888888
    let mesh: THREE.Mesh

    if (type === 'tree' || type === 'mountain') {
      const radius = type === 'mountain' ? 60 : 15
      const height = type === 'mountain' ? 120 : 40
      const cone = new THREE.ConeGeometry(radius, height, 6)
      const mat = new THREE.MeshLambertMaterial({ color })
      mesh = new THREE.Mesh(cone, mat)
      mesh.position.set(pos[0], (type === 'mountain' ? 60 : 20) * scale[1], pos[2])
      mesh.scale.set(scale[0], scale[1], scale[2])
    } else {
      const box = new THREE.BoxGeometry(
        (20 + Math.random() * 30) * scale[0],
        (30 + Math.random() * 80) * scale[1],
        (20 + Math.random() * 30) * scale[2]
      )
      const mat = new THREE.MeshLambertMaterial({ color })
      mesh = new THREE.Mesh(box, mat)
      mesh.position.set(pos[0], ((30 + Math.random() * 80) * scale[1]) / 2, pos[2])
    }
    group.add(mesh)
  }
}

function buildWaypoints() {
  const group = layerGroups.waypoints
  if (!group) return
  group.clear()

  const waypoints = props.sceneData?.waypoints || props.config?.waypoints || []
  if (!waypoints.length) return

  const sorted = [...waypoints].sort((a, b) => (a.order || 0) - (b.order || 0))
  const points: THREE.Vector3[] = []

  sorted.forEach((wp, _idx) => {
    const posArr = wp.position
    const pos = new THREE.Vector3(posArr[0], posArr[1], posArr[2])
    points.push(pos)

    // Sphere at waypoint
    const sphere = new THREE.SphereGeometry(8, 12, 12)
    const mat = new THREE.MeshLambertMaterial({ color: 0x0066cc })
    const mesh = new THREE.Mesh(sphere, mat)
    mesh.position.copy(pos)
    group.add(mesh)

    // Arrow to next waypoint
    if (_idx < sorted.length - 1) {
      const nextPos = new THREE.Vector3(
        sorted[_idx + 1].position[0],
        sorted[_idx + 1].position[1],
        sorted[_idx + 1].position[2]
      )
      const dir = new THREE.Vector3().subVectors(nextPos, pos).normalize()
      const arrow = new THREE.ArrowHelper(dir, pos, 30, 0x0066cc, 10, 6)
      group.add(arrow)
    }
  })

  // Line connecting waypoints
  if (points.length > 1) {
    const lineGeo = new THREE.BufferGeometry().setFromPoints(points)
    const lineMat = new THREE.LineBasicMaterial({ color: 0x0066cc, linewidth: 2 })
    const line = new THREE.Line(lineGeo, lineMat)
    group.add(line)
  }
}

function buildWind() {
  const group = layerGroups.weather
  if (!group) return
  group.clear()

  const windData = props.sceneData?.wind
  const windSpeed = windData?.speed ?? props.config?.weather?.wind_speed ?? 0
  const windDir = ((windData?.direction ?? props.config?.weather?.wind_direction ?? 0) * Math.PI) / 180
  const count = Math.min(Math.floor(windSpeed * 2), 100)

  if (count <= 0) return

  // Particle system for wind visualization
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)

  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 800
    positions[i * 3 + 1] = 50 + Math.random() * 200
    positions[i * 3 + 2] = (Math.random() - 0.5) * 800
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

  const material = new THREE.PointsMaterial({ color: 0x88ccff, size: 3, transparent: true, opacity: 0.6 })
  const points = new THREE.Points(geometry, material)
  group.add(points)

  // Wind direction arrow
  if (windSpeed > 0) {
    const arrowDir = new THREE.Vector3(Math.sin(windDir), 0, Math.cos(windDir)).normalize()
    const arrow = new THREE.ArrowHelper(arrowDir, new THREE.Vector3(0, 150, 0), windSpeed * 3, 0x88ccff, 20, 10)
    group.add(arrow)
  }
}

function buildRunway() {
  const runway = props.sceneData?.runway
  if (!runway) return
  const group = layerGroups.terrain
  if (!group) return

  const rLength = runway.length || 800
  const rWidth = runway.width || 30
  const heading = (runway.heading || 0) * Math.PI / 180

  const runwayGeo = new THREE.PlaneGeometry(rWidth, rLength)
  runwayGeo.rotateX(-Math.PI / 2)
  runwayGeo.rotateY(heading)
  const runwayMat = new THREE.MeshLambertMaterial({ color: 0x333344 })
  const runwayMesh = new THREE.Mesh(runwayGeo, runwayMat)
  const rp = runway.position || [0, 0, 0]
  runwayMesh.position.set(rp[0], 0.5, rp[2])
  group.add(runwayMesh)

  // Center line dashes
  for (let i = -Math.floor(rLength / 2) + 20; i <= Math.floor(rLength / 2) - 20; i += 40) {
    const dashGeo = new THREE.PlaneGeometry(1, 15)
    dashGeo.rotateX(-Math.PI / 2)
    dashGeo.rotateY(heading)
    const dashMat = new THREE.MeshBasicMaterial({ color: 0xffffff })
    const dash = new THREE.Mesh(dashGeo, dashMat)
    dash.position.set(
      rp[0] + Math.sin(heading) * i,
      0.6,
      rp[2] + Math.cos(heading) * i
    )
    group.add(dash)
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

function handleResize() {
  if (!containerRef.value) return
  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

function disposeScene() {
  if (!scene) return
  scene.traverse((obj) => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry?.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material?.dispose()
      }
    }
    if (obj instanceof THREE.Points) {
      obj.geometry?.dispose()
      obj.material?.dispose()
    }
    if (obj instanceof THREE.Line) {
      obj.geometry?.dispose()
      obj.material?.dispose()
    }
    if (obj instanceof THREE.Sprite) {
      obj.material?.dispose()
    }
  })
}

// Watch for prop changes and rebuild
watch(() => [props.config, props.sceneData], () => {
  if (scene) {
    buildScene()
  }
}, { deep: true })

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', handleResize)
  disposeScene()
  controls?.dispose()
  renderer?.dispose()
})
</script>

<style scoped>
.preview-3d {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}
.preview-3d canvas {
  width: 100%;
  height: 100%;
  display: block;
}
.layer-toggle {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}
.layer-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
</style>
