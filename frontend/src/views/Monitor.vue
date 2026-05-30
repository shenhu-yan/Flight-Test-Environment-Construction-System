<template>
  <div class="monitor-page">
    <el-row :gutter="20">
      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span>训练指标实时监控</span>
                <el-select v-model="selectedEnvId" placeholder="选择环境" style="margin-left: 20px; width: 200px" @change="onEnvChange">
                  <el-option
                    v-for="env in envs"
                    :key="env.id"
                    :label="env.name"
                    :value="env.id"
                  />
                </el-select>
              </div>
              <el-tag :type="wsConnected ? 'success' : 'danger'" size="small">
                {{ wsConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </template>
          <div ref="chartRef" style="height: 400px;"></div>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>环境参数</span>
          </template>
          <el-descriptions :column="2" border v-if="currentEnv">
            <el-descriptions-item label="地形类型">{{ currentEnv.config?.terrain?.type }}</el-descriptions-item>
            <el-descriptions-item label="风速">{{ currentEnv.config?.atmosphere?.wind_speed }} m/s</el-descriptions-item>
            <el-descriptions-item label="风向">{{ currentEnv.config?.atmosphere?.wind_direction }}°</el-descriptions-item>
            <el-descriptions-item label="能见度">{{ currentEnv.config?.atmosphere?.visibility }} m</el-descriptions-item>
            <el-descriptions-item label="机型">{{ currentEnv.config?.aircraft?.model }}</el-descriptions-item>
            <el-descriptions-item label="质量">{{ currentEnv.config?.aircraft?.mass }} kg</el-descriptions-item>
            <el-descriptions-item label="障碍物数量">{{ currentEnv.config?.obstacles?.count }}</el-descriptions-item>
            <el-descriptions-item label="障碍物密度">{{ currentEnv.config?.obstacles?.density }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="请选择环境" />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card>
          <template #header>
            <span>手动调整</span>
          </template>
          <el-form v-if="currentEnv" label-position="top" size="small">
            <el-form-item label="风速 (m/s)">
              <el-slider v-model="adjustForm.wind_speed" :min="0" :max="50" :step="1" show-input input-size="small" />
            </el-form-item>
            <el-form-item label="风向 (°)">
              <el-slider v-model="adjustForm.wind_direction" :min="0" :max="360" :step="10" show-input input-size="small" />
            </el-form-item>
            <el-form-item label="障碍物数量">
              <el-input-number v-model="adjustForm.obstacle_count" :min="0" :max="50" />
            </el-form-item>
            <el-form-item label="着陆区宽度 (m)">
              <el-slider v-model="adjustForm.landing_width" :min="20" :max="300" :step="10" show-input input-size="small" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitAdjust" :disabled="!selectedEnvId">应用调整</el-button>
            </el-form-item>
          </el-form>
          <el-empty v-else description="请选择环境" />
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>调整历史</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in adjustmentHistory"
              :key="item.id"
              :timestamp="item.created_at"
              placement="top"
            >
              <el-card shadow="never">
                <div>{{ item.trigger_type === 'auto' ? '自动调整' : '手动调整' }}</div>
                <div class="history-reason">{{ item.reason }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="adjustmentHistory.length === 0" description="暂无调整记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const chartRef = ref()
const chart = ref<echarts.ECharts | null>(null)
const wsConnected = ref(false)
const currentEnv = ref<any>(null)
const envs = ref<any[]>([])

// 手动调整表单
const adjustForm = ref({
  wind_speed: 5,
  wind_direction: 90,
  obstacle_count: 0,
  landing_width: 100,
})

const submitAdjust = async () => {
  if (!selectedEnvId.value) return
  try {
    await api.post(`/api/envs/${selectedEnvId.value}/adjust`, {
      params: {
        'atmosphere.wind_speed': adjustForm.value.wind_speed,
        'atmosphere.wind_direction': adjustForm.value.wind_direction,
        'obstacles.count': adjustForm.value.obstacle_count,
        'landing.width': adjustForm.value.landing_width,
      },
      reason: '手动调整'
    })
    ElMessage.success('调整已应用')
    await loadAdjustmentHistory(selectedEnvId.value)
    // 刷新环境参数显示
    const envResp = await api.get(`/api/envs/${selectedEnvId.value}`)
    currentEnv.value = envResp.data.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '调整失败')
  }
}
const selectedEnvId = ref('')
const adjustmentHistory = ref<any[]>([])

const metricData = {
  steps: [] as number[],
  rewards: [] as number[],
  successRates: [] as number[],
  convergenceSpeeds: [] as number[]
}

let ws: WebSocket | null = null
let metricsRefreshInterval: number | null = null

onMounted(async () => {
  await loadEnvs()
  await nextTick()
  initChart()
  connectWebSocket()
  // 定时刷新训练指标
  metricsRefreshInterval = window.setInterval(async () => {
    if (selectedEnvId.value) {
      await loadTrainingMetrics(selectedEnvId.value)
    }
  }, 2000)  // 每2秒刷新一次
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (chart.value) {
    chart.value.dispose()
  }
  if (metricsRefreshInterval) {
    clearInterval(metricsRefreshInterval)
  }
})

const loadEnvs = async () => {
  if (!projectStore.currentProject) return
  const response = await api.get('/api/envs', {
    params: { project_id: projectStore.currentProject.id }
  })
  envs.value = response.data.data
}

const onEnvChange = async (envId: string) => {
  try {
    // 加载环境详情
    const envResponse = await api.get(`/api/envs/${envId}`)
    currentEnv.value = envResponse.data.data

    // 填充手动调整表单
    const cfg = currentEnv.value?.config
    if (cfg) {
      adjustForm.value.wind_speed = cfg.atmosphere?.wind_speed ?? 5
      adjustForm.value.wind_direction = cfg.atmosphere?.wind_direction ?? 90
      adjustForm.value.obstacle_count = cfg.obstacles?.count ?? 0
      adjustForm.value.landing_width = cfg.landing?.width ?? 100
    }

    // 加载历史训练指标
    await loadTrainingMetrics(envId)

    // 加载调整历史
    await loadAdjustmentHistory(envId)
  } catch (error) {
    currentEnv.value = null
  }
}

const loadTrainingMetrics = async (envId: string) => {
  try {
    const response = await api.get(`/api/envs/${envId}/metrics`, {
      params: { limit: 1000 }
    })
    const metrics = response.data.data

    // 清空旧数据
    metricData.steps = []
    metricData.rewards = []
    metricData.successRates = []
    metricData.convergenceSpeeds = []

    // 填充新数据
    metrics.forEach((m: any) => {
      metricData.steps.push(m.step)
      metricData.rewards.push(m.episode_reward || 0)
      metricData.successRates.push(m.success_rate || 0)
      metricData.convergenceSpeeds.push(m.convergence_speed || 0)
    })

    // 更新图表
    updateChartFromData()
  } catch (error) {
    console.error('Failed to load training metrics:', error)
  }
}

const movingAverage = (data: number[], window: number): number[] => {
  return data.map((_, i) => {
    const start = Math.max(0, i - window + 1)
    const slice = data.slice(start, i + 1)
    return slice.reduce((a, b) => a + b, 0) / slice.length
  })
}

const updateChartFromData = () => {
  if (!chart.value) return

  const smoothedRewards = movingAverage(metricData.rewards, 10)

  chart.value.setOption({
    xAxis: { data: metricData.steps },
    series: [
      { data: metricData.rewards },
      { data: smoothedRewards },
      { data: metricData.successRates },
      { data: metricData.convergenceSpeeds }
    ]
  })
}

const initChart = () => {
  if (!chartRef.value) return
  chart.value = echarts.init(chartRef.value)
  chart.value.setOption({
    title: { text: '训练指标曲线' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['奖励值(原始)', '奖励值(平滑)', '成功率', '收敛速度'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: [
      { type: 'value', name: '奖励值', position: 'left' },
      { type: 'value', name: '成功率/收敛速度', position: 'right', max: 1 }
    ],
    series: [
      {
        name: '奖励值(原始)',
        type: 'line',
        yAxisIndex: 0,
        data: [],
        smooth: false,
        lineStyle: { opacity: 0.3 },
        itemStyle: { opacity: 0.3 },
        symbol: 'none'
      },
      {
        name: '奖励值(平滑)',
        type: 'line',
        yAxisIndex: 0,
        data: [],
        smooth: true,
        lineStyle: { width: 3 }
      },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true
      },
      {
        name: '收敛速度',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true
      }
    ]
  })
}

const connectWebSocket = () => {
  const token = authStore.token
  if (!token) return

  ws = new WebSocket(`ws://localhost:8000/ws/frontend?token=${token}`)

  ws.onopen = () => {
    wsConnected.value = true
    if (projectStore.currentProject) {
      ws?.send(JSON.stringify({
        type: 'subscribe',
        project_id: projectStore.currentProject.id
      }))
    }
  }

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    if (message.type === 'metric_broadcast') {
      updateChart(message.data)
    }
  }

  ws.onclose = () => {
    wsConnected.value = false
    setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = () => {
    wsConnected.value = false
  }
}

const updateChart = (data: any) => {
  const metrics = data.metrics
  const step = metrics.step || 0

  metricData.steps.push(step)
  metricData.rewards.push(metrics.episode_reward || 0)
  metricData.successRates.push(metrics.success_rate || 0)
  metricData.convergenceSpeeds.push(metrics.convergence_speed || 0)

  if (metricData.steps.length > 100) {
    metricData.steps.shift()
    metricData.rewards.shift()
    metricData.successRates.shift()
    metricData.convergenceSpeeds.shift()
  }

  chart.value?.setOption({
    xAxis: { data: metricData.steps },
    series: [
      { data: metricData.rewards },
      { data: movingAverage(metricData.rewards, 10) },
      { data: metricData.successRates },
      { data: metricData.convergenceSpeeds }
    ]
  })
}

const loadAdjustmentHistory = async (envId: string) => {
  try {
    const response = await api.get(`/api/envs/${envId}/adjustment-history`)
    adjustmentHistory.value = response.data.data || []
  } catch (error) {
    adjustmentHistory.value = []
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.history-reason {
  color: #666;
  font-size: 12px;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
