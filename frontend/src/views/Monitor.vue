<template>
  <div class="monitor">
    <div class="page-header">
      <h1 class="page-title">训练监控</h1>
      <p class="page-desc">实时监控训练进度和环境参数调整</p>
    </div>

    <!-- Environment Selector + Status -->
    <div class="monitor-toolbar">
      <el-select
        v-model="selectedEnvId"
        placeholder="选择环境"
        filterable
        style="width: 300px"
        @change="handleEnvSelect"
      >
        <el-option
          v-for="env in envs"
          :key="env.id"
          :label="env.name"
          :value="env.id"
        />
      </el-select>
      <div class="ws-status">
        <span class="ws-dot" :class="{ connected: connected }"></span>
        <span>{{ connected ? 'WebSocket 已连接' : 'WebSocket 未连接' }}</span>
      </div>
    </div>

    <!-- Top: Real-time Chart -->
    <div class="monitor-top">
      <el-card shadow="never">
        <template #header><span>训练指标趋势</span></template>
        <v-chart class="chart" :option="chartOption" autoresize />
      </el-card>
    </div>

    <!-- Middle: Env Params + Adjust / History -->
    <div class="monitor-bottom">
      <div class="bottom-left">
        <el-card shadow="never">
          <template #header><span>当前环境参数</span></template>
          <el-descriptions :column="2" border size="small" v-if="selectedEnv">
            <el-descriptions-item label="风速">{{ selectedEnv.config?.weather?.wind_speed }} m/s</el-descriptions-item>
            <el-descriptions-item label="风向">{{ selectedEnv.config?.weather?.wind_direction }}°</el-descriptions-item>
            <el-descriptions-item label="能见度">{{ selectedEnv.config?.weather?.visibility }} km</el-descriptions-item>
            <el-descriptions-item label="地形">{{ selectedEnv.config?.terrain?.type }}</el-descriptions-item>
            <el-descriptions-item label="地形高度范围">{{ selectedEnv.config?.terrain?.elevation_min }}-{{ selectedEnv.config?.terrain?.elevation_max }}m</el-descriptions-item>
            <el-descriptions-item label="障碍物数">{{ selectedEnv.config?.obstacles?.count }}</el-descriptions-item>
            <el-descriptions-item label="航点数">{{ selectedEnv.config?.waypoints?.length }}</el-descriptions-item>
            <el-descriptions-item label="状态"><StatusTag :status="selectedEnv.status" /></el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="请先选择环境" :image-size="60" />
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header><span>手动调整</span></template>
          <el-form label-position="top" size="default" v-if="selectedEnv">
            <el-form-item label="风速 (m/s)">
              <el-slider v-model="adjustForm.wind_speed" :min="0" :max="50" show-input />
            </el-form-item>
            <el-form-item label="风向 (°)">
              <el-slider v-model="adjustForm.wind_direction" :min="0" :max="360" show-input />
            </el-form-item>
            <el-form-item label="能见度 (km)">
              <el-slider v-model="adjustForm.visibility" :min="0.1" :max="50" :step="0.1" show-input />
            </el-form-item>
            <el-form-item label="障碍物数">
              <el-input-number v-model="adjustForm.obstacle_count" :min="0" :max="200" />
            </el-form-item>
            <el-form-item label="调整原因">
              <el-input v-model="adjustForm.reason" type="textarea" placeholder="说明调整原因" />
            </el-form-item>
            <el-button type="primary" :loading="adjusting" @click="handleAdjust">应用调整</el-button>
          </el-form>
          <el-empty v-else description="请先选择环境" :image-size="60" />
        </el-card>
      </div>

      <div class="bottom-right">
        <el-card shadow="never" class="history-card">
          <template #header><span>调整历史</span></template>
          <el-timeline v-if="adjustHistory.length">
            <el-timeline-item
              v-for="item in adjustHistory"
              :key="item.id"
              :timestamp="formatDate(item.created_at)"
              placement="top"
            >
              <div class="history-item">
                <span class="history-type">
                  <el-tag :type="item.trigger_type === 'auto' ? 'warning' : 'info'" size="small">
                    {{ item.trigger_type === 'auto' ? '自动' : '手动' }}
                  </el-tag>
                </span>
                <span class="history-operator">{{ item.operator }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无调整历史" :image-size="60" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { useProjectStore } from '../stores/project'
import { getEnvs, adjustEnv, getAdjustmentHistory } from '../api/envs'
import { getTrainingMetrics } from '../api/logs'
import { useWebSocket } from '../composables/useWebSocket'
import { getWsUrl } from '../api/websocket'
import StatusTag from '../components/common/StatusTag.vue'
import type { FlightEnv, AdjustmentHistory, TrainingMetric } from '../types'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const projectStore = useProjectStore()
const envs = ref<FlightEnv[]>([])
const selectedEnv = ref<FlightEnv | null>(null)
const selectedEnvId = ref('')
const metrics = ref<TrainingMetric[]>([])
const adjustHistory = ref<AdjustmentHistory[]>([])
const adjusting = ref(false)

const adjustForm = reactive({
  wind_speed: 5,
  wind_direction: 0,
  visibility: 10,
  obstacle_count: 10,
  reason: ''
})

const { connected, send } = useWebSocket(getWsUrl('/ws/frontend'), (data) => {
  if (data.type === 'metric' && selectedEnv.value && data.env_id === selectedEnv.value.id) {
    metrics.value.push(data as TrainingMetric)
    if (metrics.value.length > 300) metrics.value.shift()
  }
})

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['episode_reward', 'success_rate', 'convergence_speed'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: metrics.value.map(m => m.step.toString()),
    name: 'Step'
  },
  yAxis: [
    { type: 'value', name: 'Reward' },
    { type: 'value', name: 'Rate (%)', max: 100 }
  ],
  series: [
    {
      name: 'episode_reward',
      type: 'line',
      data: metrics.value.map(m => m.episode_reward),
      smooth: true,
      color: '#0066cc'
    },
    {
      name: 'success_rate',
      type: 'line',
      yAxisIndex: 1,
      data: metrics.value.map(m => m.success_rate * 100),
      smooth: true,
      color: '#34c759'
    },
    {
      name: 'convergence_speed',
      type: 'line',
      yAxisIndex: 1,
      data: metrics.value.map(m => m.convergence_speed * 100),
      smooth: true,
      color: '#ff9500'
    }
  ]
}))

async function loadEnvs() {
  if (!projectStore.currentProject) return
  try {
    const res = await getEnvs(projectStore.currentProject.id)
    const data = res.data.data
    envs.value = Array.isArray(data) ? data : (data?.data || [])
    if (envs.value.length && !selectedEnv.value) {
      handleEnvSelect(envs.value[0].id)
    }
  } catch { envs.value = [] }
}

async function handleEnvSelect(envId: string) {
  selectedEnvId.value = envId
  const env = envs.value.find(e => e.id === envId)
  if (!env) return
  selectedEnv.value = env
  adjustForm.wind_speed = env.config?.weather?.wind_speed || 5
  adjustForm.wind_direction = env.config?.weather?.wind_direction || 0
  adjustForm.visibility = env.config?.weather?.visibility || 10
  adjustForm.obstacle_count = env.config?.obstacles?.count || 10
  await loadMetrics(env.id)
  await loadHistory(env.id)

  // Subscribe via WebSocket
  send({ type: 'subscribe', env_id: env.id })
}

async function loadMetrics(envId: string) {
  try {
    const res = await getTrainingMetrics(envId)
    const data = res.data.data
    metrics.value = Array.isArray(data) ? data : (data?.data || [])
  } catch { metrics.value = [] }
}

async function loadHistory(envId: string) {
  try {
    const res = await getAdjustmentHistory(envId)
    const data = res.data.data
    adjustHistory.value = Array.isArray(data) ? data : (data?.data || [])
  } catch { adjustHistory.value = [] }
}

async function handleAdjust() {
  if (!selectedEnv.value) return
  if (!adjustForm.reason) {
    ElMessage.warning('请填写调整原因')
    return
  }
  adjusting.value = true
  try {
    await adjustEnv(selectedEnv.value.id, {
      adjustments: {
        weather: {
          wind_speed: adjustForm.wind_speed,
          wind_direction: adjustForm.wind_direction,
          visibility: adjustForm.visibility
        },
        obstacles: {
          count: adjustForm.obstacle_count,
          types: selectedEnv.value.config?.obstacles?.types || [],
          density: selectedEnv.value.config?.obstacles?.density || 0.3
        }
      },
      reason: adjustForm.reason || '手动调整'
    })
    ElMessage.success('调整已应用')
    await loadHistory(selectedEnv.value.id)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '调整失败')
  } finally { adjusting.value = false }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadEnvs()
})

onUnmounted(() => {
  // WebSocket cleanup handled by composable
})
</script>

<style scoped>
.monitor { max-width: 1200px; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 28px; font-weight: 600; letter-spacing: -0.03em; margin: 0 0 4px; }
.page-desc { font-size: 15px; color: var(--text-secondary); margin: 0; }
.monitor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.ws-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}
.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  transition: background 0.3s;
}
.ws-dot.connected {
  background: var(--success);
}
.monitor-top { margin-bottom: 16px; }
.chart { width: 100%; height: 350px; }
.monitor-bottom { display: flex; gap: 16px; }
.bottom-left { flex: 1; }
.bottom-right { width: 360px; }
.history-card { max-height: 700px; overflow-y: auto; }
.history-item { display: flex; gap: 8px; align-items: center; }
.history-type { font-weight: 500; font-size: 14px; }
.history-operator { font-size: 13px; color: var(--text-secondary); }
</style>
