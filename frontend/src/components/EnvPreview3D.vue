<template>
  <div class="preview-container" ref="containerRef">
    <div class="layer-controls">
      <el-checkbox v-model="showTerrain" @change="toggleLayer('terrain')">地形</el-checkbox>
      <el-checkbox v-model="showObstacles" @change="toggleLayer('obstacles')">障碍物</el-checkbox>
      <el-checkbox v-model="showWaypoints" @change="toggleLayer('waypoints')">航路</el-checkbox>
      <el-checkbox v-model="showWind" @change="toggleLayer('wind')">风场</el-checkbox>
    </div>
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps<{
  sceneData: any
}>()

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationId: number

const showTerrain = ref(true)
const showObstacles = ref(true)
const showWaypoints = ref(true)
const showWind = ref(true)

const layers: Record<string, THREE.Group> = {}

onMounted(() => {
  initScene()
  if (props.sceneData) {
    renderScene(props.sceneData)
  }
  animate()
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  renderer?.dispose()
})

watch(() => props.sceneData, (newData) => {
  if (newData) {
    clearScene()
    renderScene(newData)
  }
})

const initScene = () => {
  if (!canvasRef.value || !containerRef.value) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x87ceeb)

  camera = new THREE.PerspectiveCamera(
    75,
    containerRef.value.clientWidth / containerRef.value.clientHeight,
    0.1,
    10000
  )
  camera.position.set(200, 200, 200)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true })
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(100, 100, 50)
  scene.add(directionalLight)
}

const clearScene = () => {
  Object.values(layers).forEach(group => {
    scene.remove(group)
  })
  Object.keys(layers).forEach(key => {
    delete layers[key]
  })
}

const renderScene = (data: any) => {
  if (data.terrain) {
    renderTerrain(data.terrain)
  }
  if (data.obstacles) {
    renderObstacles(data.obstacles)
  }
  if (data.waypoints) {
    renderWaypoints(data.waypoints)
  }
  if (data.wind) {
    renderWind(data.wind)
  }
  if (data.runway) {
    renderRunway(data.runway)
  }
}

const renderTerrain = (terrain: any) => {
  const group = new THREE.Group()
  const { grid_size, elevation } = terrain

  const geometry = new THREE.PlaneGeometry(
    grid_size[0] * 10,
    grid_size[1] * 10,
    grid_size[0] - 1,
    grid_size[1] - 1
  )

  const positions = geometry.attributes.position.array as Float32Array
  for (let i = 0; i < elevation.length; i++) {
    for (let j = 0; j < elevation[i].length; j++) {
      const index = i * grid_size[0] + j
      positions[index * 3 + 2] = elevation[i][j] / 10
    }
  }
  geometry.computeVertexNormals()

  const material = new THREE.MeshLambertMaterial({
    color: 0x228b22,
    side: THREE.DoubleSide,
  })

  const mesh = new THREE.Mesh(geometry, material)
  mesh.rotation.x = -Math.PI / 2
  group.add(mesh)

  layers['terrain'] = group
  scene.add(group)
}

const renderObstacles = (obstacles: any[]) => {
  const group = new THREE.Group()

  obstacles.forEach(obstacle => {
    let geometry: THREE.BufferGeometry
    const material = new THREE.MeshLambertMaterial({ color: 0x8b4513 })

    if (obstacle.type === 'building') {
      geometry = new THREE.BoxGeometry(
        obstacle.size?.[0] || 10,
        obstacle.size?.[2] || 20,
        obstacle.size?.[1] || 10
      )
    } else {
      geometry = new THREE.ConeGeometry(
        obstacle.radius || 10,
        obstacle.height || 30,
        8
      )
    }

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(
      obstacle.position[0] - 250,
      (obstacle.position[2] || 0) + (obstacle.size?.[2] || 20) / 2,
      obstacle.position[1] - 250
    )
    group.add(mesh)
  })

  layers['obstacles'] = group
  scene.add(group)
}

const renderWaypoints = (waypoints: any[]) => {
  const group = new THREE.Group()

  const sortedWaypoints = [...waypoints].sort((a, b) => a.order - b.order)

  if (sortedWaypoints.length > 1) {
    const points: THREE.Vector3[] = sortedWaypoints.map(wp =>
      new THREE.Vector3(wp.position[0] - 250, wp.position[2], wp.position[1] - 250)
    )
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points)
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 })
    const line = new THREE.Line(lineGeometry, lineMaterial)
    group.add(line)
  }

  sortedWaypoints.forEach(wp => {
    const sphereGeometry = new THREE.SphereGeometry(5, 16, 16)
    const sphereMaterial = new THREE.MeshBasicMaterial({ color: 0xff4444 })
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial)
    sphere.position.set(wp.position[0] - 250, wp.position[2], wp.position[1] - 250)
    group.add(sphere)
  })

  layers['waypoints'] = group
  scene.add(group)
}

const renderWind = (wind: any) => {
  const group = new THREE.Group()
  const particleCount = 100
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(particleCount * 3)

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 500
    positions[i * 3 + 1] = Math.random() * 100 + 50
    positions[i * 3 + 2] = (Math.random() - 0.5) * 500
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

  const material = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 3,
    transparent: true,
    opacity: 0.6,
  })

  const particles = new THREE.Points(geometry, material)
  group.add(particles)

  layers['wind'] = group
  scene.add(group)
}

const renderRunway = (runway: any) => {
  const group = new THREE.Group()

  const geometry = new THREE.PlaneGeometry(runway.width, runway.length)
  const material = new THREE.MeshLambertMaterial({
    color: 0x333333,
    side: THREE.DoubleSide,
  })

  const mesh = new THREE.Mesh(geometry, material)
  mesh.rotation.x = -Math.PI / 2
  mesh.rotation.z = (runway.heading * Math.PI) / 180
  mesh.position.set(
    runway.position[0] - 250,
    runway.position[2] + 0.1,
    runway.position[1] - 250
  )
  group.add(mesh)

  layers['runway'] = group
  scene.add(group)
}

const toggleLayer = (layerName: string) => {
  const layer = layers[layerName]
  if (layer) {
    layer.visible = !layer.visible
  }
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  controls?.update()
  renderer?.render(scene, camera)
}
</script>

<style scoped>
.preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

canvas {
  width: 100%;
  height: 100%;
}

.layer-controls {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
</style>
