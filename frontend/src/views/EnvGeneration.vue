<template>
  <div class="env-generation">
    <div class="gen-header">
      <div>
        <h1 class="page-title">环境生成</h1>
        <p class="page-desc">配置参数并预览三维飞行环境</p>
      </div>
      <div class="gen-actions">
        <el-select v-model="selectedTemplateId" placeholder="选择模板" clearable style="width:180px">
          <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          <el-icon><VideoPlay /></el-icon> 生成环境
        </el-button>
        <el-button :loading="batchGenerating" @click="handleBatchGenerate">
          <el-icon><Grid /></el-icon> 批量生成
        </el-button>
      </div>
    </div>

    <div class="gen-body">
      <div class="gen-left">
        <EnvConfigPanel :config="config" />
      </div>
      <div class="gen-right">
        <EnvPreview3D :config="config" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '../stores/project'
import { createEnv, batchGenerateEnv } from '../api/envs'
import { getTemplates } from '../api/templates'
import EnvConfigPanel from '../components/env/EnvConfigPanel.vue'
import EnvPreview3D from '../components/three/EnvPreview3D.vue'
import type { EnvConfig, Template } from '../types'

const projectStore = useProjectStore()
const templates = ref<Template[]>([])
const selectedTemplateId = ref('')
const generating = ref(false)
const batchGenerating = ref(false)

const config = reactive<EnvConfig>({
  terrain: { type: 'plain', elevation_min: 0, elevation_max: 500, resolution: 10 },
  weather: { wind_speed: 5, wind_direction: 0, visibility: 10 },
  flight_dynamics: { aircraft_model: 'Cessna 172', mass: 1100, wingspan: 11 },
  rewards: {
    reward_items: [
      { name: '航点到达', coefficient: 1.0 },
      { name: '任务完成', coefficient: 2.0 }
    ],
    penalty_items: [
      { name: '碰撞', coefficient: 0.5 },
      { name: '偏离航线', coefficient: 0.3 }
    ]
  },
  obstacles: { count: 10, types: ['building', 'tree', 'power_tower'], density: 0.3 },
  waypoints: [
    { id: 'wp_1', position: [0, 100, 0], order: 1 },
    { id: 'wp_2', position: [300, 150, 200], order: 2 },
    { id: 'wp_3', position: [600, 100, 400], order: 3 },
    { id: 'wp_4', position: [300, 80, 600], order: 4 }
  ]
})

async function loadTemplates() {
  try {
    const res = await getTemplates()
    const data = res.data.data
    templates.value = Array.isArray(data) ? data : (Array.isArray(res.data) ? res.data : [])
  } catch {}
}

async function handleGenerate() {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }
  generating.value = true
  try {
    await createEnv(projectStore.currentProject.id, {
      name: `环境_${Date.now()}`,
      config: JSON.parse(JSON.stringify(config)),
      template_id: selectedTemplateId.value || undefined
    })
    ElMessage.success('环境生成成功')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '生成失败')
  } finally { generating.value = false }
}

async function handleBatchGenerate() {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }
  try {
    const { value: count } = await ElMessageBox.prompt('请输入批量生成数量', '批量生成', {
      inputPattern: /^[1-9]\d*$/,
      inputErrorMessage: '请输入正整数',
      inputValue: '5'
    })
    batchGenerating.value = true
    await batchGenerateEnv(projectStore.currentProject.id, {
      count: parseInt(count),
      config: JSON.parse(JSON.stringify(config))
    })
    ElMessage.success(`已生成 ${count} 个环境`)
  } catch {}
  finally { batchGenerating.value = false }
}

onMounted(loadTemplates)
</script>

<style scoped>
.env-generation {
  height: calc(100vh - var(--nav-height) - var(--status-bar-height) - 48px);
  display: flex;
  flex-direction: column;
}
.gen-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}
.gen-actions {
  display: flex;
  gap: 8px;
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
.gen-body {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}
.gen-left {
  width: 40%;
  overflow-y: auto;
  border-right: 1px solid var(--border-light);
  padding-right: 16px;
}
.gen-right {
  width: 60%;
  border-radius: 12px;
  overflow: hidden;
  background: #1a1a2e;
}
</style>
