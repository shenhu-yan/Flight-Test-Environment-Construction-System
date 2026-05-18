<template>
  <div class="optimization">
    <div class="page-header">
      <h1 class="page-title">优化中心</h1>
      <p class="page-desc">环境参数多维评估与自动优化</p>
    </div>

    <!-- Top: Radar Chart + Scores -->
    <div class="opt-top">
      <div class="radar-section">
        <el-card shadow="never">
          <template #header><span>环境评估雷达图</span></template>
          <v-chart class="radar-chart" :option="radarOption" autoresize />
        </el-card>
      </div>
      <div class="score-section">
        <el-card shadow="never">
          <template #header><span>综合评分</span></template>
          <div class="score-display">
            <div class="total-score">{{ totalScore.toFixed(1) }}</div>
            <div class="score-label">/ 100</div>
          </div>
          <div class="score-breakdown">
            <div class="score-item">
              <span class="score-name">多样性</span>
              <el-progress :percentage="scores.diversity" :color="'#0066cc'" />
            </div>
            <div class="score-item">
              <span class="score-name">挑战性</span>
              <el-progress :percentage="scores.challenge" :color="'#ff9500'" />
            </div>
            <div class="score-item">
              <span class="score-name">真实性</span>
              <el-progress :percentage="scores.realism" :color="'#34c759'" />
            </div>
            <div class="score-item">
              <span class="score-name">有效性</span>
              <el-progress :percentage="scores.effectiveness" :color="'#af52de'" />
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Middle: Task Table -->
    <div class="opt-middle">
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>优化任务</span>
            <el-button type="primary" size="small" @click="showCreateTask = true">
              <el-icon><Plus /></el-icon> 创建任务
            </el-button>
          </div>
        </template>
        <el-table :data="tasks" stripe v-loading="loadingTasks">
          <el-table-column prop="id" label="任务ID" width="120" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><StatusTag :status="row.status" /></template>
          </el-table-column>
          <el-table-column prop="current_iteration" label="当前迭代" width="100" />
          <el-table-column prop="max_iterations" label="总迭代" width="100" />
          <el-table-column prop="best_score" label="最佳分数" width="120">
            <template #default="{ row }">{{ row.best_score?.toFixed(2) || '-' }}</template>
          </el-table-column>
          <el-table-column label="进度" min-width="160">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.round((row.current_iteration / row.max_iterations) * 100)"
                :status="row.status === 'completed' ? 'success' : row.status === 'running' ? undefined : 'exception'"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button v-if="row.status === 'running'" type="danger" size="small" @click="handleStop(row)">
                停止
              </el-button>
              <el-button size="small" @click="viewReport(row)">报告</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Bottom: Report Comparison -->
    <div class="opt-bottom">
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>优化前后对比</span>
            <el-select v-model="selectedReportId" placeholder="选择报告" style="width: 300px" @change="loadReport" filterable>
              <el-option
                v-for="r in reports"
                :key="r.id"
                :label="`${r.task_id} - ${formatDate(r.created_at)}`"
                :value="r.id"
              />
            </el-select>
          </div>
        </template>
        <v-chart v-if="report" class="compare-chart" :option="compareOption" autoresize />
        <el-empty v-else description="暂无对比数据，请选择报告" :image-size="60" />
      </el-card>
    </div>

    <!-- Create Task Dialog -->
    <el-dialog v-model="showCreateTask" title="创建优化任务" width="520px" destroy-on-close>
      <el-form :model="taskForm" label-position="top">
        <el-form-item label="最大迭代次数">
          <el-input-number v-model="taskForm.max_iterations" :min="10" :max="10000" :step="10" />
        </el-form-item>
        <el-form-item>
          <template #label>
            <span>评估权重 (总计: {{ weightSum }}%)</span>
          </template>
          <div class="weight-inputs">
            <div class="weight-item">
              <span>多样性</span>
              <el-slider v-model="taskForm.weights.diversity" :min="0" :max="100" show-input :disabled="weightLocked" />
            </div>
            <div class="weight-item">
              <span>挑战性</span>
              <el-slider v-model="taskForm.weights.challenge" :min="0" :max="100" show-input :disabled="weightLocked" />
            </div>
            <div class="weight-item">
              <span>真实性</span>
              <el-slider v-model="taskForm.weights.realism" :min="0" :max="100" show-input :disabled="weightLocked" />
            </div>
            <div class="weight-item">
              <span>有效性</span>
              <el-slider v-model="taskForm.weights.effectiveness" :min="0" :max="100" show-input :disabled="weightLocked" />
            </div>
          </div>
          <div v-if="weightSum !== 100" style="margin-top:8px;color:var(--danger);font-size:12px">
            权重总计需为 100%，当前: {{ weightSum }}%
          </div>
        </el-form-item>
        <el-form-item label="参数搜索空间">
          <div class="param-space-inputs">
            <div class="param-item">
              <span>风速 (m/s)</span>
              <el-input v-model="taskForm.param_space.wind_speed" placeholder="例: [0, 50]" />
            </div>
            <div class="param-item">
              <span>风向 (°)</span>
              <el-input v-model="taskForm.param_space.wind_direction" placeholder="例: [0, 360]" />
            </div>
            <div class="param-item">
              <span>障碍物数</span>
              <el-input v-model="taskForm.param_space.obstacle_count" placeholder="例: [0, 100]" />
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTask = false">取消</el-button>
        <el-button
          type="primary"
          :loading="creatingTask"
          :disabled="weightSum !== 100"
          @click="handleCreateTask"
        >创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, BarChart } from 'echarts/charts'
import { RadarComponent, GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { useProjectStore } from '../stores/project'
import {
  getOptimizationTasks,
  createOptimizationTask,
  stopOptimizationTask,
  getOptimizationReport,
  getOptimizationReports
} from '../api/optimization'
import { evaluateEnv } from '../api/optimization'
import StatusTag from '../components/common/StatusTag.vue'
import type { OptimizationTask, OptimizationReport } from '../types'

use([CanvasRenderer, RadarChart, BarChart, RadarComponent, GridComponent, TooltipComponent, LegendComponent])

const projectStore = useProjectStore()
const tasks = ref<OptimizationTask[]>([])
const reports = ref<OptimizationReport[]>([])
const report = ref<OptimizationReport | null>(null)
const selectedReportId = ref('')
const showCreateTask = ref(false)
const creatingTask = ref(false)
const loadingTasks = ref(false)

const scores = reactive({
  diversity: 72,
  challenge: 65,
  realism: 80,
  effectiveness: 70
})
const totalScore = computed(() => (scores.diversity + scores.challenge + scores.realism + scores.effectiveness) / 4)

const weightLocked = ref(false)

const taskForm = reactive({
  max_iterations: 100,
  weights: { diversity: 25, challenge: 25, realism: 25, effectiveness: 25 },
  param_space: {
    wind_speed: '[0, 50]',
    wind_direction: '[0, 360]',
    obstacle_count: '[0, 100]'
  }
})

const weightSum = computed(() =>
  taskForm.weights.diversity + taskForm.weights.challenge + taskForm.weights.realism + taskForm.weights.effectiveness
)

const radarOption = computed(() => ({
  radar: {
    indicator: [
      { name: '多样性', max: 100 },
      { name: '挑战性', max: 100 },
      { name: '真实性', max: 100 },
      { name: '有效性', max: 100 }
    ]
  },
  series: [{
    type: 'radar',
    data: [{
      value: [scores.diversity, scores.challenge, scores.realism, scores.effectiveness],
      name: '当前评估',
      areaStyle: { color: 'rgba(0,102,204,0.15)' },
      lineStyle: { color: '#0066cc', width: 2 },
      itemStyle: { color: '#0066cc' }
    }]
  }]
}))

const compareOption = computed(() => {
  if (!report.value) return {}
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['优化前', '优化后'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['多样性', '挑战性', '真实性', '有效性'] },
    yAxis: { type: 'value', max: 100 },
    series: [
      {
        name: '优化前',
        type: 'bar',
        data: [
          report.value.before_scores?.diversity || 0,
          report.value.before_scores?.challenge || 0,
          report.value.before_scores?.realism || 0,
          report.value.before_scores?.effectiveness || 0
        ],
        color: '#d2d2d7'
      },
      {
        name: '优化后',
        type: 'bar',
        data: [
          report.value.after_scores?.diversity || 0,
          report.value.after_scores?.challenge || 0,
          report.value.after_scores?.realism || 0,
          report.value.after_scores?.effectiveness || 0
        ],
        color: '#0066cc'
      }
    ]
  }
})

async function loadTasks() {
  if (!projectStore.currentProject) return
  loadingTasks.value = true
  try {
    const res = await getOptimizationTasks(projectStore.currentProject.id)
    tasks.value = res.data.data || []
  } catch { tasks.value = [] }
  finally { loadingTasks.value = false }
}

async function loadReports() {
  if (!projectStore.currentProject) return
  try {
    const res = await getOptimizationReports(projectStore.currentProject.id)
    reports.value = res.data.data || []
  } catch { reports.value = [] }
}

async function loadReport() {
  if (!selectedReportId.value) return
  try {
    const task = tasks.value.find(t => t.id === selectedReportId.value || t.report_id === selectedReportId.value)
    if (task) {
      const res = await getOptimizationReport(task.id)
      report.value = res.data.data || null
    } else {
      // Try loading report directly by matching task IDs
      for (const t of tasks.value) {
        try {
          const res = await getOptimizationReport(t.id)
          if (res.data.data?.id === selectedReportId.value) {
            report.value = res.data.data
            return
          }
        } catch {}
      }
    }
  } catch { ElMessage.error('获取报告失败') }
}

async function handleCreateTask() {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }
  if (weightSum.value !== 100) {
    ElMessage.warning('权重总计需为 100%')
    return
  }
  creatingTask.value = true
  try {
    // Parse param_space from text inputs
    const paramSpace: Record<string, number[]> = {}
    for (const [key, val] of Object.entries(taskForm.param_space)) {
      try {
        paramSpace[key] = JSON.parse(val as string)
      } catch {
        ElMessage.error(`参数 "${key}" 格式错误，请使用 [min, max] 格式`)
        creatingTask.value = false
        return
      }
    }

    const normalizedWeights: Record<string, number> = {}
    for (const [k, v] of Object.entries(taskForm.weights)) {
      normalizedWeights[k] = v / 100
    }

    await createOptimizationTask(projectStore.currentProject.id, {
      param_space: paramSpace,
      weights: normalizedWeights,
      max_iterations: taskForm.max_iterations
    })
    ElMessage.success('任务创建成功')
    showCreateTask.value = false
    await loadTasks()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  } finally { creatingTask.value = false }
}

async function handleStop(task: OptimizationTask) {
  try {
    await stopOptimizationTask(task.id)
    ElMessage.success('任务已停止')
    await loadTasks()
  } catch { ElMessage.error('停止失败') }
}

async function viewReport(task: OptimizationTask) {
  try {
    const res = await getOptimizationReport(task.id)
    report.value = res.data.data || null
  } catch { ElMessage.error('获取报告失败') }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTasks()
  loadReports()
})
</script>

<style scoped>
.optimization { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 28px; font-weight: 600; letter-spacing: -0.03em; margin: 0 0 4px; }
.page-desc { font-size: 15px; color: var(--text-secondary); margin: 0; }
.opt-top { display: flex; gap: 16px; margin-bottom: 16px; }
.radar-section { flex: 1; }
.score-section { width: 320px; }
.radar-chart { width: 100%; height: 300px; }
.score-display { text-align: center; padding: 20px 0 16px; }
.total-score { font-size: 48px; font-weight: 700; letter-spacing: -0.04em; color: var(--primary); }
.score-label { font-size: 16px; color: var(--text-muted); }
.score-breakdown { display: flex; flex-direction: column; gap: 12px; }
.score-item { display: flex; align-items: center; gap: 12px; }
.score-name { font-size: 13px; min-width: 50px; color: var(--text-secondary); }
.opt-middle { margin-bottom: 16px; }
.compare-chart { width: 100%; height: 300px; }
.weight-inputs { display: flex; flex-direction: column; gap: 12px; width: 100%; }
.weight-item { display: flex; align-items: center; gap: 12px; }
.weight-item span { min-width: 50px; font-size: 13px; }
.weight-item .el-slider { flex: 1; }
.param-space-inputs { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.param-item { display: flex; align-items: center; gap: 12px; }
.param-item span { min-width: 80px; font-size: 13px; }
.param-item .el-input { flex: 1; }
</style>
