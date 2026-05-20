<template>
  <div class="optimization-page">
    <!-- 顶部操作栏 -->
    <el-card class="action-bar">
      <div class="action-bar-content">
        <div class="action-left">
          <el-select v-model="selectedEnvId" placeholder="选择环境" style="width: 200px">
            <el-option
              v-for="env in envs"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </div>
        <div class="action-right">
          <el-button type="success" @click="evaluateEnv" :loading="evaluating" :disabled="!selectedEnvId">
            评估环境
          </el-button>
          <el-button type="primary" @click="showCreateTaskDialog = true" :disabled="!selectedEnvId">
            智能优化
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>评估结果</span>
          </template>

          <div v-if="evaluation" class="evaluation-result">
            <div style="text-align: right; margin-bottom: 10px;">
              <el-button size="small" type="danger" @click="deleteEvaluation">删除评估</el-button>
            </div>
            <div ref="radarChartRef" style="height: 300px;"></div>
            <div class="total-score">
              <span>总分:</span>
              <span class="score">{{ evaluation.total_score }}</span>
            </div>
            <div class="suggestions">
              <h4>优化建议</h4>
              <ul>
                <li v-for="(suggestion, index) in evaluation.suggestions" :key="index">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
          </div>
          <el-empty v-else description="请选择环境进行评估" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>优化历史</span>
          </template>

          <el-table :data="optimizationTasks" style="width: 100%">
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getTaskStatusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="current_iteration" label="进度">
              <template #default="{ row }">
                {{ row.current_iteration }}/{{ row.max_iterations }}
              </template>
            </el-table-column>
            <el-table-column prop="best_score" label="最优分数" />
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button size="small" @click="viewTask(row)">查看</el-button>
                <el-button
                  v-if="row.status === 'running'"
                  size="small"
                  type="danger"
                  @click="stopTask(row)"
                >
                  停止
                </el-button>
                <el-button
                  v-if="row.status !== 'running'"
                  size="small"
                  type="danger"
                  @click="deleteTask(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="optimizationTasks.length === 0" description="暂无优化任务" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreateTaskDialog" title="智能优化" width="600px">
      <el-tabs v-model="optimizeMode">
        <el-tab-pane label="全自动优化" name="auto">
          <el-alert type="success" :closable="false" show-icon style="margin-bottom: 20px;">
            <template #title>智能优化</template>
            <div style="margin-top: 10px;">
              系统将自动分析当前环境配置，根据评估分数智能调整参数，寻找最优配置。无需手动设置参数范围。
            </div>
          </el-alert>
          <el-form :model="taskForm" label-width="120px">
            <el-form-item label="迭代次数">
              <el-input-number v-model="taskForm.max_iterations" :min="5" :max="50" />
              <span style="margin-left: 10px; color: #666;">建议 10-20 次</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="手动配置" name="manual">
          <el-form :model="taskForm" label-width="120px">
            <el-form-item label="最大迭代次数">
              <el-input-number v-model="taskForm.max_iterations" :min="1" :max="100" />
            </el-form-item>

            <el-divider content-position="left">要优化的环境参数</el-divider>
            <el-form-item label="风速范围">
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.wind_speed[0]" :min="0" :max="50" placeholder="最小值" />
              </el-col>
              <el-col :span="4" style="text-align: center">~</el-col>
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.wind_speed[1]" :min="0" :max="50" placeholder="最大值" />
              </el-col>
            </el-form-item>
            <el-form-item label="障碍物数量范围">
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.obstacle_count[0]" :min="0" :max="50" placeholder="最小值" />
              </el-col>
              <el-col :span="4" style="text-align: center">~</el-col>
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.obstacle_count[1]" :min="0" :max="50" placeholder="最大值" />
              </el-col>
            </el-form-item>
            <el-form-item label="风向范围">
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.wind_direction[0]" :min="0" :max="360" placeholder="最小值" />
              </el-col>
              <el-col :span="4" style="text-align: center">~</el-col>
              <el-col :span="10">
                <el-input-number v-model="taskForm.param_space.wind_direction[1]" :min="0" :max="360" placeholder="最大值" />
              </el-col>
            </el-form-item>

            <el-divider content-position="left">评估维度权重</el-divider>
            <el-form-item label="多样性权重">
              <el-slider v-model="taskForm.weights.diversity" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            <el-form-item label="挑战性权重">
              <el-slider v-model="taskForm.weights.challenge" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            <el-form-item label="真实性权重">
              <el-slider v-model="taskForm.weights.realism" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            <el-form-item label="有效性权重">
              <el-slider v-model="taskForm.weights.effectiveness" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="showCreateTaskDialog = false">取消</el-button>
        <el-button v-if="optimizeMode === 'auto'" type="primary" @click="autoOptimize" :loading="optimizing">
          开始优化
        </el-button>
        <el-button v-else type="primary" @click="createTask">
          创建任务
        </el-button>
      </template>
    </el-dialog>

    <!-- 任务详情弹窗 -->
    <el-dialog v-model="showTaskDetail" title="优化任务详情" width="600px">
      <template v-if="selectedTask">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="任务ID">{{ selectedTask.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getTaskStatusType(selectedTask.status)">{{ selectedTask.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">{{ selectedTask.current_iteration }}/{{ selectedTask.max_iterations }}</el-descriptions-item>
          <el-descriptions-item label="最优分数">{{ selectedTask.best_score }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedTask.created_at }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedTask.best_params" style="margin-top: 20px;">
          <h4>最优参数</h4>
          <el-table :data="Object.entries(selectedTask.best_params).map(([key, value]) => ({ param: key, value }))" border size="small">
            <el-table-column prop="param" label="参数名" />
            <el-table-column prop="value" label="值" />
          </el-table>
        </div>

        <div v-if="selectedTask.param_space" style="margin-top: 20px;">
          <h4>参数空间</h4>
          <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px;">{{ JSON.stringify(selectedTask.param_space, null, 2) }}</pre>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const radarChartRef = ref()
const evaluation = ref<any>(null)
const optimizationTasks = ref<any[]>([])
const evaluating = ref(false)
const optimizing = ref(false)
const showCreateTaskDialog = ref(false)
const envs = ref<any[]>([])
const selectedEnvId = ref('')
const optimizeMode = ref('auto')
const showTaskDetail = ref(false)
const selectedTask = ref<any>(null)

const taskForm = ref({
  max_iterations: 10,
  param_space: {
    wind_speed: [0, 50],
    obstacle_count: [0, 50],
    wind_direction: [0, 360],
  },
  weights: {
    diversity: 0.25,
    challenge: 0.25,
    realism: 0.25,
    effectiveness: 0.25,
  }
})

const getTaskStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

onMounted(async () => {
  await loadEnvs()
  await loadOptimizationTasks()
})

const loadEnvs = async () => {
  if (!projectStore.currentProject) return
  const response = await api.get('/api/envs', {
    params: { project_id: projectStore.currentProject.id }
  })
  envs.value = response.data.data.filter((e: any) => e.status === 'active')
}

const evaluateEnv = async () => {
  if (!selectedEnvId.value) {
    ElMessage.warning('请先选择环境')
    return
  }

  evaluating.value = true
  try {
    await api.post(`/api/envs/${selectedEnvId.value}/evaluate`, {})
    ElMessage.success('评估任务已提交')
    setTimeout(async () => {
      await loadEvaluation(selectedEnvId.value)
    }, 2000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '评估失败')
  } finally {
    evaluating.value = false
  }
}

const loadEvaluation = async (envId: string) => {
  try {
    const response = await api.get(`/api/envs/${envId}/evaluations`)
    if (response.data.data && response.data.data.length > 0) {
      evaluation.value = response.data.data[0]
      await nextTick()
      initRadarChart()
    } else {
      evaluation.value = null
    }
  } catch (error) {
    console.error('Load evaluation error')
  }
}

const initRadarChart = () => {
  if (!radarChartRef.value || !evaluation.value) return

  const chart = echarts.init(radarChartRef.value)
  chart.setOption({
    title: { text: '环境质量评估', left: 'center' },
    radar: {
      indicator: [
        { name: '多样性', max: 100 },
        { name: '挑战性', max: 100 },
        { name: '真实性', max: 100 },
        { name: '有效性', max: 100 },
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          evaluation.value.diversity_score,
          evaluation.value.challenge_score,
          evaluation.value.realism_score,
          evaluation.value.effectiveness_score,
        ],
        name: '评估分数'
      }]
    }]
  })
}

const loadOptimizationTasks = async () => {
  if (!projectStore.currentProject) return
  const response = await api.get('/api/optimization-tasks', {
    params: { project_id: projectStore.currentProject.id }
  })
  optimizationTasks.value = response.data.data
}

const createTask = async () => {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }

  try {
    await api.post('/api/optimization-tasks', {
      project_id: projectStore.currentProject.id,
      max_iterations: taskForm.value.max_iterations,
      param_space: taskForm.value.param_space,
      weights: taskForm.value.weights,
    })

    showCreateTaskDialog.value = false
    ElMessage.success('优化任务已创建')
    await loadOptimizationTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  }
}

const autoOptimize = async () => {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }

  optimizing.value = true
  try {
    await api.post('/api/optimization-tasks/auto', {
      project_id: projectStore.currentProject.id,
      max_iterations: taskForm.value.max_iterations,
    })

    showCreateTaskDialog.value = false
    ElMessage.success('智能优化已启动，系统将自动寻找最优配置')
    await loadOptimizationTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '优化失败')
  } finally {
    optimizing.value = false
  }
}

const viewTask = async (task: any) => {
  try {
    const response = await api.get(`/api/optimization-tasks/${task.id}`)
    selectedTask.value = response.data.data
    showTaskDetail.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取任务详情失败')
  }
}

const stopTask = async (task: any) => {
  try {
    await api.post(`/api/optimization-tasks/${task.id}/stop`)
    ElMessage.success('任务已停止')
    await loadOptimizationTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '停止失败')
  }
}

const deleteTask = async (task: any) => {
  try {
    await api.delete(`/api/optimization-tasks/${task.id}`)
    ElMessage.success('任务已删除')
    await loadOptimizationTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const deleteEvaluation = async () => {
  if (!evaluation.value || !selectedEnvId.value) return
  try {
    await api.delete(`/api/envs/${selectedEnvId.value}/evaluations/${evaluation.value.id}`)
    ElMessage.success('评估已删除')
    evaluation.value = null
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-bar {
  margin-bottom: 20px;
}

.action-bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  align-items: center;
}

.action-right {
  display: flex;
  gap: 10px;
}

.total-score {
  text-align: center;
  margin: 20px 0;
  font-size: 18px;
}

.score {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-left: 10px;
}

.suggestions {
  margin-top: 20px;
}

.suggestions h4 {
  margin-bottom: 10px;
}

.suggestions ul {
  padding-left: 20px;
}

.suggestions li {
  margin-bottom: 5px;
  color: #666;
}

.auto-optimize-info {
  margin-bottom: 20px;
}
</style>
