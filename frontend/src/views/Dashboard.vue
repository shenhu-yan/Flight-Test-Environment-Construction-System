<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">环境管理</h1>
        <p class="page-desc">管理和查看所有飞行试验环境</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建环境
      </el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="envs.length === 0" class="empty-state">
      <el-empty description="暂无环境，点击上方按钮创建">
        <el-button type="primary" @click="showCreateDialog = true">创建第一个环境</el-button>
      </el-empty>
    </div>

    <div v-else class="env-grid">
      <EnvCard
        v-for="env in envs"
        :key="env.id"
        :env="env"
        @click="openDetail(env)"
      />
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建环境" width="500px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="环境名称" required>
          <el-input v-model="createForm.name" placeholder="输入环境名称" />
        </el-form-item>
        <el-form-item label="关联任务">
          <el-select v-model="createForm.task_id" placeholder="可选" clearable style="width:100%">
            <el-option v-for="t in tasks" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="使用模板">
          <el-select v-model="createForm.template_id" placeholder="可选" clearable style="width:100%">
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <EnvDetail
      v-model="showDetail"
      :env="selectedEnv"
      @adjust="handleAdjust"
      @evaluate="handleEvaluate"
      @export="handleExport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../stores/project'
import { getEnvs, createEnv, exportEnv, evaluateEnv } from '../api/envs'
import { getTasks } from '../api/tasks'
import { getTemplates } from '../api/templates'
import EnvCard from '../components/env/EnvCard.vue'
import EnvDetail from '../components/env/EnvDetail.vue'
import type { FlightEnv, Task, Template, EnvConfig } from '../types'

const projectStore = useProjectStore()
const envs = ref<FlightEnv[]>([])
const tasks = ref<Task[]>([])
const templates = ref<Template[]>([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const showDetail = ref(false)
const selectedEnv = ref<FlightEnv | null>(null)

const createForm = ref({
  name: '',
  task_id: '',
  template_id: ''
})

function defaultConfig(): EnvConfig {
  return {
    terrain: { type: 'plain', elevation_min: 0, elevation_max: 500, resolution: 10 },
    weather: { wind_speed: 5, wind_direction: 0, visibility: 10 },
    flight_dynamics: { aircraft_model: 'Cessna 172', mass: 1100, wingspan: 11 },
    rewards: { reward_items: [{ name: 'completion', coefficient: 1.0 }], penalty_items: [{ name: 'collision', coefficient: 0.5 }] },
    obstacles: { count: 5, types: ['building', 'tree'], density: 0.3 },
    waypoints: [{ id: 'wp_1', position: [0, 100, 0], order: 1 }, { id: 'wp_2', position: [500, 100, 500], order: 2 }]
  }
}

async function loadEnvs() {
  if (!projectStore.currentProject) return
  loading.value = true
  try {
    const res = await getEnvs(projectStore.currentProject.id, { page: 1, page_size: 50 })
    const data = res.data.data
    envs.value = Array.isArray(data) ? data : (data?.data || [])
  } catch { envs.value = [] }
  finally { loading.value = false }
}

async function loadMeta() {
  if (!projectStore.currentProject) return
  try {
    const [tasksRes, templatesRes] = await Promise.all([
      getTasks(projectStore.currentProject.id),
      getTemplates()
    ])
    const td = tasksRes.data.data
    tasks.value = Array.isArray(td) ? td : (td?.data || [])
    const tmd = templatesRes.data.data
    templates.value = Array.isArray(tmd) ? tmd : (Array.isArray(templatesRes.data) ? templatesRes.data : [])
  } catch {}
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入环境名称')
    return
  }
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }
  creating.value = true
  try {
    await createEnv(projectStore.currentProject.id, {
      name: createForm.value.name,
      config: defaultConfig(),
      template_id: createForm.value.template_id || undefined,
      task_id: createForm.value.task_id || undefined
    })
    ElMessage.success('环境创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', task_id: '', template_id: '' }
    await loadEnvs()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  } finally { creating.value = false }
}

function openDetail(env: FlightEnv) {
  selectedEnv.value = env
  showDetail.value = true
}

function handleAdjust(env: FlightEnv) {
  ElMessage.info('调整功能请前往环境生成页面')
}

async function handleEvaluate(env: FlightEnv) {
  try {
    const res = await evaluateEnv(env.id)
    ElMessage.success('评估完成')
  } catch { ElMessage.error('评估失败') }
}

async function handleExport(env: FlightEnv) {
  try {
    const res = await exportEnv(env.id)
    const blob = new Blob([JSON.stringify(res.data)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${env.name}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch { ElMessage.error('导出失败') }
}

onMounted(() => {
  loadEnvs()
  loadMeta()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.03em;
  margin: 0 0 4px;
}
.page-desc {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}
.env-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.loading-state, .empty-state {
  padding: 60px 0;
}
</style>
