<template>
  <div class="envs-page">
    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>环境配置</span>
              <div>
                <el-button @click="uploadConfig">上传配置文件</el-button>
                <el-button type="primary" @click="generateEnv" :loading="generating">
                  生成环境
                </el-button>
              </div>
            </div>
          </template>

          <el-form :model="config" label-width="120px">
            <el-divider content-position="left">基本信息</el-divider>
            <el-form-item label="环境名称">
              <el-input v-model="envName" placeholder="请输入环境名称" />
            </el-form-item>

            <el-divider content-position="left">模板选择</el-divider>
            <el-form-item label="选择模板">
              <el-select v-model="selectedTemplateId" placeholder="选择模板" @change="onTemplateChange" value-key="id">
                <el-option
                  v-for="template in templates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">地形配置</el-divider>
            <el-form-item label="地形类型">
              <el-select v-model="config.terrain.type">
                <el-option label="平坦" value="flat" />
                <el-option label="丘陵" value="hilly" />
                <el-option label="山地" value="mountainous" />
              </el-select>
            </el-form-item>
            <el-form-item label="海拔范围">
              <el-slider
                v-model="elevationRange"
                range
                :min="0"
                :max="2000"
                @change="onElevationChange"
              />
            </el-form-item>
            <el-form-item label="分辨率">
              <el-input-number v-model="config.terrain.resolution" :min="0.1" :max="10" :step="0.1" />
            </el-form-item>

            <el-divider content-position="left">气象配置</el-divider>
            <el-form-item label="风速 (m/s)">
              <el-slider v-model="config.atmosphere.wind_speed" :min="0" :max="50" :step="1" show-input />
            </el-form-item>
            <el-form-item label="风向 (度)">
              <el-slider v-model="config.atmosphere.wind_direction" :min="0" :max="360" :step="1" show-input />
            </el-form-item>
            <el-form-item label="能见度 (m)">
              <el-input-number v-model="config.atmosphere.visibility" :min="100" :max="100000" :step="100" />
            </el-form-item>

            <el-divider content-position="left">飞行力学</el-divider>
            <el-form-item label="机型">
              <el-select v-model="config.aircraft.model">
                <el-option label="Cessna 172" value="c172x" />
                <el-option label="F-16" value="f16" />
              </el-select>
            </el-form-item>
            <el-form-item label="质量 (kg)">
              <el-input-number v-model="config.aircraft.mass" :min="100" :max="100000" :step="10" />
            </el-form-item>
            <el-form-item label="翼展 (m)">
              <el-input-number v-model="config.aircraft.wingspan" :min="1" :max="100" :step="0.5" />
            </el-form-item>

            <el-divider content-position="left">奖励函数</el-divider>
            <el-form-item label="奖励项">
              <div v-for="(item, index) in config.reward.items" :key="index" class="reward-item">
                <el-input v-model="item.name" placeholder="奖励名称" style="width: 150px" />
                <el-input-number v-model="item.coefficient" :step="0.1" style="width: 120px; margin-left: 10px" />
                <el-button type="danger" size="small" style="margin-left: 10px" @click="removeRewardItem(index)">删除</el-button>
              </div>
              <el-button type="primary" plain @click="addRewardItem">添加奖励项</el-button>
            </el-form-item>

            <el-divider content-position="left">惩罚项</el-divider>
            <el-form-item label="惩罚项">
              <div v-for="(item, index) in config.reward.penalties" :key="index" class="reward-item">
                <el-input v-model="item.name" placeholder="惩罚名称" style="width: 150px" />
                <el-input-number v-model="item.coefficient" :step="0.1" :max="0" style="width: 120px; margin-left: 10px" />
                <el-button type="danger" size="small" style="margin-left: 10px" @click="removePenaltyItem(index)">删除</el-button>
              </div>
              <el-button type="warning" plain @click="addPenaltyItem">添加惩罚项</el-button>
            </el-form-item>

            <el-divider content-position="left">障碍物</el-divider>
            <el-form-item label="障碍物数量">
              <el-slider v-model="config.obstacles.count" :min="0" :max="50" :step="1" show-input />
            </el-form-item>
            <el-form-item label="障碍物密度">
              <el-slider v-model="config.obstacles.density" :min="0" :max="1" :step="0.01" show-input />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="preview-card">
          <template #header>
            <span>三维预览</span>
          </template>
          <EnvPreview3D v-if="sceneData" :sceneData="sceneData" />
          <el-empty v-else description="生成环境后可预览3D场景" />
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>环境列表</span>
          </template>
          <div class="env-list">
            <div v-for="env in envs" :key="env.id" class="env-item" @click="selectEnv(env)">
              <div class="env-info">
                <div class="env-name">{{ env.name }}</div>
                <el-tag :type="getStatusType(env.status)" size="small">{{ env.status }}</el-tag>
              </div>
              <div class="env-actions">
                <el-button
                  v-if="env.status === 'active' && (!trainingEnvId || trainingEnvId !== env.id)"
                  type="success"
                  size="small"
                  @click.stop="startTraining(env)"
                >
                  开始训练
                </el-button>
                <el-button
                  v-if="env.status === 'active' && (!trainingEnvId || trainingEnvId !== env.id)"
                  type="primary"
                  size="small"
                  @click.stop="startTrainAndOptimize(env)"
                >
                  训练+优化
                </el-button>
                <el-button
                  v-if="trainingEnvId === env.id && isTraining"
                  type="danger"
                  size="small"
                  @click.stop="stopTraining"
                >
                  停止训练
                </el-button>
                <span v-if="trainingEnvId === env.id && isTraining" class="training-progress">
                  {{ trainingProgress }}%
                </span>
                <span v-if="optTaskId && trainingEnvId === env.id" class="opt-progress">
                  优化: {{ optProgress }}
                </span>
                <el-button
                  size="small"
                  @click.stop="exportEnvJson(env)"
                >
                  导出
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click.stop="deleteEnv(env)"
                >
                  删除
                </el-button>
              </div>
            </div>
            <el-empty v-if="envs.length === 0" description="暂无环境" />
          </div>
        </el-card>

        <!-- 优化迭代详情 -->
        <el-card v-if="optRounds.length > 0" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>优化迭代过程</span>
              <el-tag :type="optProgress.includes('完成') ? 'success' : 'warning'" size="small">
                {{ optProgress }}
              </el-tag>
            </div>
          </template>
          <el-table :data="optRounds" size="small" stripe>
            <el-table-column prop="round" label="轮次" width="60" />
            <el-table-column label="训练奖励" width="100">
              <template #default="{ row }">
                <span :style="{ color: row.reward > 0 ? '#67c23a' : '#f56c6c' }">
                  {{ row.reward?.toFixed(0) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="成功率" width="80">
              <template #default="{ row }">
                {{ (row.sr * 100).toFixed(0) }}%
              </template>
            </el-table-column>
            <el-table-column label="综合评分" width="80">
              <template #default="{ row }">
                <el-tag :type="row.score > 50 ? 'success' : row.score > 30 ? 'warning' : 'danger'" size="small">
                  {{ row.score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="趋势">
              <template #default="{ row, $index }">
                <span v-if="$index > 0">
                  {{ row.score > optRounds[$index - 1].score ? '↑' : row.score < optRounds[$index - 1].score ? '↓' : '→' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <input
      ref="fileInput"
      type="file"
      accept=".json,.xml"
      style="display: none"
      @change="onFileUpload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import EnvPreview3D from '@/components/EnvPreview3D.vue'

const projectStore = useProjectStore()
const templates = ref<any[]>([])
const envs = ref<any[]>([])
const selectedTemplateId = ref<string>('')
const generating = ref(false)
const fileInput = ref<HTMLInputElement>()
const sceneData = ref<any>(null)
const envName = ref('')

// 训练相关
const trainingEnvId = ref<string>('')
const isTraining = ref(false)
const trainingProgress = ref(0)
let trainingPollInterval: number | null = null

// 优化相关
const optTaskId = ref<string>('')
const optProgress = ref('')
const optRounds = ref<any[]>([])
let optPollInterval: number | null = null

const elevationRange = ref([0, 100])

interface RewardItem {
  name: string
  coefficient: number
}

interface PenaltyItem {
  name: string
  coefficient: number
}

interface Config {
  terrain: {
    type: string
    elevation_min: number
    elevation_max: number
    resolution: number
  }
  atmosphere: {
    wind_speed: number
    wind_direction: number
    visibility: number
  }
  aircraft: {
    model: string
    mass: number
    wingspan: number
  }
  reward: {
    items: RewardItem[]
    penalties: PenaltyItem[]
  }
  obstacles: {
    count: number
    types: string[]
    density: number
  }
  waypoints: any[]
}

const config = ref<Config>({
  terrain: {
    type: 'flat',
    elevation_min: 0,
    elevation_max: 100,
    resolution: 1.0
  },
  atmosphere: {
    wind_speed: 5,
    wind_direction: 90,
    visibility: 10000
  },
  aircraft: {
    model: 'c172x',
    mass: 1043,
    wingspan: 11.0
  },
  reward: {
    items: [{ name: 'altitude_reward', coefficient: 1.0 }],
    penalties: []
  },
  obstacles: {
    count: 0,
    types: [],
    density: 0.0
  },
  waypoints: []
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    generating: 'warning',
    active: 'success',
    deprecated: 'info',
    error: 'danger'
  }
  return map[status] || 'info'
}

onMounted(async () => {
  await loadTemplates()
  await loadEnvs()
  // 恢复训练状态：检查是否有正在进行的训练
  await restoreTrainingState()
})

const restoreTrainingState = async () => {
  for (const env of envs.value) {
    try {
      const resp = await api.get(`/api/envs/${env.id}/training-status`)
      const data = resp.data.data
      if (data && data.status === 'running') {
        trainingEnvId.value = env.id
        isTraining.value = true
        trainingProgress.value = Math.min(100, Math.round(data.current_step / data.max_steps * 100))
        // 恢复轮询
        trainingPollInterval = window.setInterval(async () => {
          await checkTrainingStatus(env.id)
        }, 1000)
        break
      }
    } catch (e) {
      // ignore
    }
  }
}

onUnmounted(() => {
  if (trainingPollInterval) {
    clearInterval(trainingPollInterval)
    trainingPollInterval = null
  }
  if (optPollInterval) {
    clearInterval(optPollInterval)
    optPollInterval = null
  }
})

const loadTemplates = async () => {
  const response = await api.get('/api/templates')
  templates.value = response.data.data
}

const loadEnvs = async () => {
  if (!projectStore.currentProject) return
  const response = await api.get('/api/envs', {
    params: { project_id: projectStore.currentProject.id }
  })
  envs.value = response.data.data
}

const onTemplateChange = (templateId: string) => {
  const template = templates.value.find(t => t.id === templateId)
  if (template && template.config) {
    config.value = { ...config.value, ...template.config }
    elevationRange.value = [template.config.terrain?.elevation_min || 0, template.config.terrain?.elevation_max || 100]
  }
}

const onElevationChange = (value: number[]) => {
  config.value.terrain.elevation_min = value[0]
  config.value.terrain.elevation_max = value[1]
}

const addRewardItem = () => {
  config.value.reward.items.push({ name: '', coefficient: 1.0 })
}

const removeRewardItem = (index: number) => {
  config.value.reward.items.splice(index, 1)
}

const addPenaltyItem = () => {
  config.value.reward.penalties.push({ name: '', coefficient: -1.0 })
}

const removePenaltyItem = (index: number) => {
  config.value.reward.penalties.splice(index, 1)
}

const uploadConfig = () => {
  fileInput.value?.click()
}

const onFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post('/api/envs/parse-config', formData)
    config.value = response.data.data
    ElMessage.success('配置文件解析成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '配置文件解析失败')
  }

  input.value = ''
}

const generateEnv = async () => {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }

  if (!envName.value.trim()) {
    ElMessage.warning('请输入环境名称')
    return
  }

  generating.value = true
  try {
    const response = await api.post('/api/envs', {
      project_id: projectStore.currentProject.id,
      name: envName.value.trim(),
      config: config.value
    })
    const envId = response.data.data.id
    ElMessage.success('环境生成任务已提交')
    envName.value = ''

    await loadEnvs()

    const previewResponse = await api.get(`/api/envs/${envId}/preview`)
    sceneData.value = previewResponse.data.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '环境生成失败')
  } finally {
    generating.value = false
  }
}

const selectEnv = async (env: any) => {
  try {
    const response = await api.get(`/api/envs/${env.id}/preview`)
    sceneData.value = response.data.data
  } catch (error) {
    sceneData.value = null
  }
}

const deleteEnv = async (env: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 "${env.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await api.delete(`/api/envs/${env.id}`)
    ElMessage.success('环境已删除')
    await loadEnvs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const exportEnvJson = async (env: any) => {
  try {
    const response = await api.get(`/api/envs/${env.id}/export-json`, {
      responseType: 'blob'
    })
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${env.name}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导出失败')
  }
}

const startTraining = async (env: any) => {
  try {
    const response = await api.post(`/api/envs/${env.id}/train`, {
      max_steps: 1000
    })
    trainingEnvId.value = env.id
    isTraining.value = true
    trainingProgress.value = 0
    ElMessage.success('训练已启动')

    // 延迟2秒后开始轮询，等线程启动
    setTimeout(() => {
      trainingPollInterval = window.setInterval(async () => {
        await checkTrainingStatus(env.id)
      }, 1000)
    }, 2000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '启动训练失败')
  }
}

const stopTraining = async () => {
  if (!trainingEnvId.value) return

  try {
    await api.post(`/api/envs/${trainingEnvId.value}/stop-training`)
    isTraining.value = false
    trainingProgress.value = 0
    ElMessage.success('训练已停止')

    if (trainingPollInterval) {
      clearInterval(trainingPollInterval)
      trainingPollInterval = null
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '停止训练失败')
  }
}

const startTrainAndOptimize = async (env: any) => {
  try {
    const response = await api.post(`/api/envs/${env.id}/train-and-optimize`, {
      n_rounds: 5
    })
    const data = response.data.data
    trainingEnvId.value = env.id
    isTraining.value = true
    trainingProgress.value = 0
    optTaskId.value = data.task_id
    optProgress.value = '运行中...'
    optRounds.value = []
    ElMessage.success('迭代式训练+优化已启动')

    // 轮询训练状态
    setTimeout(() => {
      trainingPollInterval = window.setInterval(async () => {
        await checkTrainingStatus(env.id)
      }, 1000)
    }, 2000)

    // 轮询优化状态
    setTimeout(() => {
      optPollInterval = window.setInterval(async () => {
        await checkOptStatus(data.task_id)
      }, 5000)
    }, 3000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '启动失败')
  }
}

const checkOptStatus = async (taskId: string) => {
  try {
    const response = await api.get(`/api/optimization-tasks/${taskId}`)
    const data = response.data.data
    const iter = typeof data.current_iteration === 'number' ? data.current_iteration : 0
    const roundDisplay = Math.floor(iter)
    const subPct = Math.round((iter - roundDisplay) * 100)
    const iterDisplay = subPct > 0 && roundDisplay < data.max_iterations
      ? `${roundDisplay}/${data.max_iterations} (${subPct}%)`
      : `${roundDisplay}/${data.max_iterations}`
    optProgress.value = `${iterDisplay} (最优: ${data.best_score || '-'})`

    // 更新迭代轮次详情：从 DB 读取每轮最后一条指标
    if (data.current_iteration > optRounds.value.length) {
      try {
        if (selectedEnvId.value) {
          const mr = await api.get(`/api/envs/${selectedEnvId.value}/metrics`, { params: { limit: 1000 } })
          const allMetrics = mr.data.data || []
          // 每 50 条取最后一条作为该轮代表
          const rounds: any[] = []
          for (let i = 0; i < allMetrics.length; i += 50) {
            const chunk = allMetrics.slice(i, i + 50)
            const last = chunk[chunk.length - 1]
            rounds.push({
              round: rounds.length + 1,
              step: last.step,
              reward: last.episode_reward,
              sr: last.success_rate,
              score: (last.convergence_speed * 100).toFixed(0),
            })
          }
          optRounds.value = rounds
        }
      } catch (e) { /* ignore */ }
    }

    if (data.status === 'completed') {
      optProgress.value = `完成! 最优分数: ${data.best_score}`
      ElMessage.success(`优化完成! 最优分数: ${data.best_score}`)
      if (optPollInterval) {
        clearInterval(optPollInterval)
        optPollInterval = null
      }
    } else if (data.status === 'error' || data.status === 'stopped') {
      optProgress.value = data.status === 'error' ? '出错' : '已停止'
      if (optPollInterval) {
        clearInterval(optPollInterval)
        optPollInterval = null
      }
    }
  } catch (error) {
    // ignore
  }
}

const checkTrainingStatus = async (envId: string) => {
  try {
    const response = await api.get(`/api/envs/${envId}/training-status`)
    const data = response.data.data

    if (data) {
      // 更新进度（上限100%）
      const progress = Math.min(100, Math.round(data.current_step / data.max_steps * 100))
      trainingProgress.value = progress

      if (data.status === 'completed' || data.status === 'stopped') {
        isTraining.value = false
        trainingProgress.value = 100
        if (trainingPollInterval) {
          clearInterval(trainingPollInterval)
          trainingPollInterval = null
        }
        ElMessage.success('训练已完成')
      }
    }
  } catch (error) {
    // 忽略错误
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reward-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.env-list {
  max-height: 200px;
  overflow-y: auto;
}

.env-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.env-item:hover {
  background: #f5f5f5;
}

.env-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.env-name {
  font-weight: 500;
}

.env-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.training-progress {
  font-size: 12px;
  color: #67c23a;
  font-weight: bold;
}

.opt-progress {
  font-size: 12px;
  color: #409eff;
  font-weight: bold;
}

.preview-card {
  height: 500px;
}
</style>
