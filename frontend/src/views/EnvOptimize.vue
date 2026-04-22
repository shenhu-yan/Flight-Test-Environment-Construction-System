<template>
  <div class="env-optimize">
    <h2>环境优化</h2>

    <div class="env-selector">
      <label for="env_id">选择环境</label>
      <select id="env_id" v-model.number="selectedEnvId" @change="loadEnvironment">
        <option value="">请选择环境</option>
        <option v-for="env in environments" :key="env.id" :value="env.id">
          {{ env.env_name }} ({{ env.env_id }})
        </option>
      </select>
    </div>

    <div v-if="selectedEnvironment" class="env-details">
      <h3>环境详情</h3>
      <div class="detail-grid">
        <div class="detail-item">
          <label>环境名称:</label>
          <span>{{ selectedEnvironment.env_name }}</span>
        </div>
        <div class="detail-item">
          <label>环境ID:</label>
          <span>{{ selectedEnvironment.env_id }}</span>
        </div>
        <div class="detail-item">
          <label>项目:</label>
          <span>{{ getProjectName(selectedEnvironment.project_id) }}</span>
        </div>
        <div class="detail-item">
          <label>状态:</label>
          <span :class="['status-badge', selectedEnvironment.status]">{{ statusLabel(selectedEnvironment.status) }}</span>
        </div>
      </div>

      <div class="optimization-section">
        <h3>优化操作</h3>

        <div class="tabs">
          <button :class="['tab-button', { active: activeTab === 'evaluate' }]" @click="activeTab = 'evaluate'">环境评估</button>
          <button :class="['tab-button', { active: activeTab === 'optimize' }]" @click="activeTab = 'optimize'">环境优化</button>
          <button :class="['tab-button', { active: activeTab === 'visualization' }]" @click="activeTab = 'visualization'">可视化展示</button>
          <button :class="['tab-button', { active: activeTab === 'schedule' }]" @click="activeTab = 'schedule'">持续优化</button>
          <button :class="['tab-button', { active: activeTab === 'history' }]" @click="activeTab = 'history'">优化历史</button>
          <button :class="['tab-button', { active: activeTab === 'batch' }]" @click="activeTab = 'batch'">批量优化</button>
        </div>

        <div v-if="activeTab === 'evaluate'" class="tab-content">
          <form @submit.prevent="evaluateEnvironment">
            <div class="form-group">
              <label>性能指标（可选）</label>
              <div class="metric-grid">
                <div class="metric-item">
                  <label>奖励值</label>
                  <input type="number" v-model.number="performanceData.reward_value" min="0" max="100">
                </div>
                <div class="metric-item">
                  <label>成功率</label>
                  <input type="number" v-model.number="performanceData.success_rate" min="0" max="1" step="0.01">
                </div>
                <div class="metric-item">
                  <label>收敛速度</label>
                  <input type="number" v-model.number="performanceData.convergence_speed" min="0" max="1" step="0.01">
                </div>
                <div class="metric-item">
                  <label>泛化能力</label>
                  <input type="number" v-model.number="performanceData.generalization_score" min="0" max="1" step="0.01">
                </div>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="button primary">评估环境</button>
            </div>
          </form>

          <div v-if="evaluationResults" class="evaluation-results">
            <h4>评估结果</h4>
            <div class="eval-charts-row">
              <div class="chart-container" ref="radarChart" style="width:400px;height:350px;"></div>
              <div class="score-details">
                <div class="score-grid">
                  <div class="score-item">
                    <label>多样性:</label>
                    <div class="score-bar-wrap">
                      <div class="score-bar" :style="{ width: (evaluationResults.scores.diversity * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ evaluationResults.scores.diversity.toFixed(2) }}</span>
                  </div>
                  <div class="score-item">
                    <label>挑战性:</label>
                    <div class="score-bar-wrap">
                      <div class="score-bar challenge" :style="{ width: (evaluationResults.scores.challenge * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ evaluationResults.scores.challenge.toFixed(2) }}</span>
                  </div>
                  <div class="score-item">
                    <label>真实性:</label>
                    <div class="score-bar-wrap">
                      <div class="score-bar realism" :style="{ width: (evaluationResults.scores.realism * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ evaluationResults.scores.realism.toFixed(2) }}</span>
                  </div>
                  <div class="score-item">
                    <label>有效性:</label>
                    <div class="score-bar-wrap">
                      <div class="score-bar effectiveness" :style="{ width: (evaluationResults.scores.effectiveness * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ evaluationResults.scores.effectiveness.toFixed(2) }}</span>
                  </div>
                  <div class="score-item total">
                    <label>综合得分:</label>
                    <div class="score-bar-wrap">
                      <div class="score-bar total" :style="{ width: (evaluationResults.scores.total * 100) + '%' }"></div>
                    </div>
                    <span class="score-value total">{{ evaluationResults.scores.total.toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="evaluationResults.suggestions.length > 0" class="suggestions">
              <h5>优化建议:</h5>
              <ul>
                <li v-for="(suggestion, index) in evaluationResults.suggestions" :key="index">{{ suggestion }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'optimize'" class="tab-content">
          <form @submit.prevent="optimizeEnvironment">
            <div class="form-group">
              <label>性能指标（可选）</label>
              <div class="metric-grid">
                <div class="metric-item">
                  <label>奖励值</label>
                  <input type="number" v-model.number="performanceData.reward_value" min="0" max="100">
                </div>
                <div class="metric-item">
                  <label>成功率</label>
                  <input type="number" v-model.number="performanceData.success_rate" min="0" max="1" step="0.01">
                </div>
                <div class="metric-item">
                  <label>收敛速度</label>
                  <input type="number" v-model.number="performanceData.convergence_speed" min="0" max="1" step="0.01">
                </div>
                <div class="metric-item">
                  <label>泛化能力</label>
                  <input type="number" v-model.number="performanceData.generalization_score" min="0" max="1" step="0.01">
                </div>
              </div>
            </div>

            <div class="form-group">
              <label>自定义优化目标（权重）</label>
              <div class="goal-grid">
                <div class="goal-item">
                  <label>多样性权重</label>
                  <input type="range" v-model.number="customGoals.diversity" min="0" max="1" step="0.05">
                  <span class="range-value">{{ customGoals.diversity }}</span>
                </div>
                <div class="goal-item">
                  <label>挑战性权重</label>
                  <input type="range" v-model.number="customGoals.challenge" min="0" max="1" step="0.05">
                  <span class="range-value">{{ customGoals.challenge }}</span>
                </div>
                <div class="goal-item">
                  <label>真实性权重</label>
                  <input type="range" v-model.number="customGoals.realism" min="0" max="1" step="0.05">
                  <span class="range-value">{{ customGoals.realism }}</span>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="button primary">优化环境</button>
            </div>
          </form>

          <div v-if="optimizationResults" class="optimization-results">
            <h4>优化结果</h4>
            <div class="opt-compare">
              <div class="compare-chart" ref="compareChart" style="width:100%;height:350px;"></div>
            </div>
            <div class="verification-grid">
              <div class="verification-item">
                <label>优化前得分</label>
                <span class="big-num">{{ optimizationResults.optimization_verification.original_score.toFixed(3) }}</span>
              </div>
              <div class="verification-item">
                <label>优化后得分</label>
                <span class="big-num improved">{{ optimizationResults.optimization_verification.optimized_score.toFixed(3) }}</span>
              </div>
              <div class="verification-item">
                <label>改进幅度</label>
                <span :class="['big-num', optimizationResults.optimization_verification.improvement > 0 ? 'positive' : 'negative']">
                  {{ optimizationResults.optimization_verification.improvement_percentage.toFixed(2) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'visualization'" class="tab-content">
          <div class="viz-header">
            <h4>环境性能可视化</h4>
            <button @click="loadVisualization" class="button primary">刷新数据</button>
          </div>

          <div v-if="vizData" class="viz-content">
            <div class="viz-row">
              <div class="viz-card">
                <h5>当前评分雷达图</h5>
                <div ref="vizRadarChart" style="width:100%;height:350px;"></div>
              </div>
              <div class="viz-card">
                <h5>评分变化时间线</h5>
                <div ref="vizTimelineChart" style="width:100%;height:350px;"></div>
              </div>
            </div>
            <div class="viz-summary">
              <div class="summary-item">
                <label>优化次数</label>
                <span>{{ vizData.optimization_count }}</span>
              </div>
              <div class="summary-item">
                <label>调整次数</label>
                <span>{{ vizData.adjustment_count }}</span>
              </div>
              <div v-if="vizData.suggestions.length > 0" class="summary-suggestions">
                <h5>当前建议</h5>
                <ul>
                  <li v-for="(s, i) in vizData.suggestions" :key="i">{{ s }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-else class="empty-viz">
            <p>点击"刷新数据"加载可视化信息</p>
          </div>
        </div>

        <div v-if="activeTab === 'schedule'" class="tab-content">
          <h4>持续优化调度</h4>
          <p class="hint">设置定期自动优化，系统将按计划对环境进行评估和优化</p>

          <div v-if="scheduleInfo && scheduleInfo.scheduled" class="current-schedule">
            <h5>当前调度</h5>
            <div class="schedule-info-grid">
              <div class="schedule-info-item">
                <label>调度间隔</label>
                <span>{{ intervalLabel(scheduleInfo.interval) }}</span>
              </div>
              <div class="schedule-info-item">
                <label>状态</label>
                <span :class="['status-indicator', scheduleInfo.enabled ? 'enabled' : 'disabled']">
                  {{ scheduleInfo.enabled ? '已启用' : '已禁用' }}
                </span>
              </div>
              <div class="schedule-info-item">
                <label>上次运行</label>
                <span>{{ scheduleInfo.last_run ? formatDate(scheduleInfo.last_run) : '尚未运行' }}</span>
              </div>
              <div class="schedule-info-item">
                <label>下次运行</label>
                <span>{{ scheduleInfo.next_run ? formatDate(scheduleInfo.next_run) : '-' }}</span>
              </div>
            </div>
            <div class="schedule-actions">
              <button @click="toggleSchedule(!scheduleInfo.enabled)" class="button" :class="scheduleInfo.enabled ? 'warning' : 'primary'">
                {{ scheduleInfo.enabled ? '禁用调度' : '启用调度' }}
              </button>
              <button @click="cancelSchedule" class="button danger">删除调度</button>
            </div>
          </div>

          <form @submit.prevent="createSchedule" class="schedule-form">
            <div class="form-row">
              <div class="form-group half">
                <label>调度间隔</label>
                <select v-model="scheduleForm.interval" required>
                  <option value="hourly">每小时</option>
                  <option value="daily">每天</option>
                  <option value="weekly">每周</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>自定义优化目标（可选）</label>
              <div class="goal-grid">
                <div class="goal-item">
                  <label>多样性权重</label>
                  <input type="range" v-model.number="scheduleForm.custom_goals.diversity" min="0" max="1" step="0.05">
                  <span class="range-value">{{ scheduleForm.custom_goals.diversity }}</span>
                </div>
                <div class="goal-item">
                  <label>挑战性权重</label>
                  <input type="range" v-model.number="scheduleForm.custom_goals.challenge" min="0" max="1" step="0.05">
                  <span class="range-value">{{ scheduleForm.custom_goals.challenge }}</span>
                </div>
                <div class="goal-item">
                  <label>真实性权重</label>
                  <input type="range" v-model.number="scheduleForm.custom_goals.realism" min="0" max="1" step="0.05">
                  <span class="range-value">{{ scheduleForm.custom_goals.realism }}</span>
                </div>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="button primary">{{ scheduleInfo && scheduleInfo.scheduled ? '更新调度' : '创建调度' }}</button>
            </div>
          </form>
        </div>

        <div v-if="activeTab === 'history'" class="tab-content">
          <h4>优化历史</h4>
          <div v-if="optimizationHistory.length > 0" class="history-list">
            <div v-for="record in optimizationHistory" :key="record.id" class="history-card">
              <div class="history-header">
                <span class="history-time">{{ formatDate(record.created_at) }}</span>
                <span :class="['history-trigger', record.trigger]">{{ record.trigger === 'manual' ? '手动' : record.trigger === 'auto' ? '自动' : '批量' }}</span>
                <span class="history-optimizer">{{ record.optimizer }}</span>
              </div>
              <div class="history-scores">
                <div class="history-score-item">
                  <label>优化前</label>
                  <div class="mini-scores">
                    <span v-for="(val, key) in record.scores_before" :key="key" class="mini-score">
                      {{ scoreLabel(key) }}: {{ typeof val === 'number' ? val.toFixed(2) : val }}
                    </span>
                  </div>
                </div>
                <div class="history-score-item">
                  <label>优化后</label>
                  <div class="mini-scores">
                    <span v-for="(val, key) in record.scores_after" :key="key" class="mini-score">
                      {{ scoreLabel(key) }}: {{ typeof val === 'number' ? val.toFixed(2) : val }}
                    </span>
                  </div>
                </div>
                <div class="history-score-item">
                  <label>改进</label>
                  <span :class="['improvement-badge', record.improvement > 0 ? 'positive' : 'negative']">
                    {{ record.improvement > 0 ? '+' : '' }}{{ (record.improvement * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
              <button @click="viewHistoryDetail(record)" class="button small">查看详情</button>
            </div>
          </div>
          <div v-else class="empty-history">
            <p>暂无优化历史记录</p>
          </div>
        </div>

        <div v-if="activeTab === 'batch'" class="tab-content">
          <form @submit.prevent="batchOptimize">
            <div class="form-group">
              <label>选择环境</label>
              <div class="checkbox-group">
                <label v-for="env in environments" :key="env.id" class="checkbox-label">
                  <input type="checkbox" :value="env.id" v-model="batchEnvIds">
                  {{ env.env_name }} ({{ env.env_id }})
                </label>
              </div>
            </div>

            <div class="form-group">
              <label>自定义优化目标</label>
              <div class="goal-grid">
                <div class="goal-item">
                  <label>多样性权重</label>
                  <input type="range" v-model.number="batchCustomGoals.diversity" min="0" max="1" step="0.05">
                  <span class="range-value">{{ batchCustomGoals.diversity }}</span>
                </div>
                <div class="goal-item">
                  <label>挑战性权重</label>
                  <input type="range" v-model.number="batchCustomGoals.challenge" min="0" max="1" step="0.05">
                  <span class="range-value">{{ batchCustomGoals.challenge }}</span>
                </div>
                <div class="goal-item">
                  <label>真实性权重</label>
                  <input type="range" v-model.number="batchCustomGoals.realism" min="0" max="1" step="0.05">
                  <span class="range-value">{{ batchCustomGoals.realism }}</span>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="button primary">批量优化</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>优化详情</h3>
          <button @click="showDetailModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedRecord">
          <div class="detail-section">
            <h5>优化前配置</h5>
            <pre>{{ JSON.stringify(selectedRecord.original_config, null, 2) }}</pre>
          </div>
          <div class="detail-section">
            <h5>优化后配置</h5>
            <pre>{{ JSON.stringify(selectedRecord.optimized_config, null, 2) }}</pre>
          </div>
          <div v-if="selectedRecord.custom_goals" class="detail-section">
            <h5>自定义目标</h5>
            <pre>{{ JSON.stringify(selectedRecord.custom_goals, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'EnvOptimize',
  data() {
    return {
      environments: [],
      projects: [],
      selectedEnvId: '',
      selectedEnvironment: null,
      activeTab: 'evaluate',
      performanceData: {
        reward_value: 0,
        success_rate: 0.5,
        convergence_speed: 0.5,
        generalization_score: 0.5
      },
      customGoals: {
        diversity: 0.7,
        challenge: 0.6,
        realism: 0.7
      },
      batchEnvIds: [],
      batchCustomGoals: {
        diversity: 0.7,
        challenge: 0.6,
        realism: 0.7
      },
      evaluationResults: null,
      optimizationResults: null,
      vizData: null,
      scheduleInfo: null,
      scheduleForm: {
        interval: 'daily',
        custom_goals: { diversity: 0.7, challenge: 0.6, realism: 0.7 }
      },
      optimizationHistory: [],
      showDetailModal: false,
      selectedRecord: null,
      charts: {}
    }
  },
  mounted() {
    this.loadEnvironments()
    this.loadProjects()

    const urlParams = new URLSearchParams(window.location.search)
    const envId = urlParams.get('env_id')
    if (envId) {
      this.selectedEnvId = parseInt(envId)
      this.loadEnvironment()
    }
  },
  beforeUnmount() {
    Object.values(this.charts).forEach(c => c && c.dispose())
  },
  methods: {
    async loadEnvironments() {
      try {
        const response = await this.$axios.get('/environments')
        this.environments = response.data
      } catch (error) {
        console.error('加载环境失败:', error)
      }
    },
    async loadProjects() {
      try {
        const response = await this.$axios.get('/projects')
        this.projects = response.data
      } catch (error) {
        console.error('加载项目失败:', error)
      }
    },
    async loadEnvironment() {
      if (this.selectedEnvId) {
        try {
          const response = await this.$axios.get(`/environments/${this.selectedEnvId}`)
          this.selectedEnvironment = response.data
          this.evaluationResults = null
          this.optimizationResults = null
          this.vizData = null
          this.loadScheduleInfo()
          this.loadOptimizationHistory()
        } catch (error) {
          console.error('加载环境详情失败:', error)
        }
      } else {
        this.selectedEnvironment = null
      }
    },
    getProjectName(projectId) {
      const project = this.projects.find(p => p.id == projectId)
      return project ? project.project_name : '未知项目'
    },
    statusLabel(status) {
      const labels = { created: '已创建', running: '运行中', completed: '已完成', failed: '失败', adjusted: '已调整', optimized: '已优化' }
      return labels[status] || status
    },
    scoreLabel(key) {
      const labels = { diversity: '多样性', challenge: '挑战性', realism: '真实性', effectiveness: '有效性', total: '综合' }
      return labels[key] || key
    },
    intervalLabel(interval) {
      const labels = { hourly: '每小时', daily: '每天', weekly: '每周' }
      return labels[interval] || interval
    },
    formatDate(dateString) {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString()
    },
    initChart(refName) {
      if (this.charts[refName]) {
        this.charts[refName].dispose()
      }
      const el = this.$refs[refName]
      if (el) {
        this.charts[refName] = echarts.init(el)
        return this.charts[refName]
      }
      return null
    },
    async evaluateEnvironment() {
      try {
        const response = await this.$axios.post(`/env/${this.selectedEnvId}/evaluate`, {
          performance_data: this.performanceData
        })
        this.evaluationResults = response.data
        this.$nextTick(() => this.renderRadarChart())
      } catch (error) {
        console.error('评估环境失败:', error)
        alert(error.response?.data?.error || '评估环境失败')
      }
    },
    renderRadarChart() {
      const chart = this.initChart('radarChart')
      if (!chart || !this.evaluationResults) return
      const scores = this.evaluationResults.scores
      chart.setOption({
        tooltip: {},
        radar: {
          indicator: [
            { name: '多样性', max: 1 },
            { name: '挑战性', max: 1 },
            { name: '真实性', max: 1 },
            { name: '有效性', max: 1 }
          ],
          shape: 'circle',
          splitNumber: 5
        },
        series: [{
          type: 'radar',
          data: [{
            value: [scores.diversity, scores.challenge, scores.realism, scores.effectiveness],
            name: '环境评分',
            areaStyle: { opacity: 0.3, color: '#1a237e' },
            lineStyle: { color: '#1a237e' },
            itemStyle: { color: '#1a237e' }
          }]
        }]
      })
    },
    async optimizeEnvironment() {
      try {
        const response = await this.$axios.post(`/env/${this.selectedEnvId}/optimize`, {
          performance_data: this.performanceData,
          custom_goals: this.customGoals
        })
        this.optimizationResults = response.data
        this.$nextTick(() => this.renderCompareChart())
        this.loadEnvironment()
      } catch (error) {
        console.error('优化环境失败:', error)
        alert(error.response?.data?.error || '优化环境失败')
      }
    },
    renderCompareChart() {
      const chart = this.initChart('compareChart')
      if (!chart || !this.optimizationResults) return
      const before = this.optimizationResults.optimization_verification.original_scores
      const after = this.optimizationResults.optimization_verification.optimized_scores
      const categories = ['多样性', '挑战性', '真实性', '有效性']
      const keys = ['diversity', 'challenge', 'realism', 'effectiveness']
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['优化前', '优化后'] },
        xAxis: { type: 'category', data: categories },
        yAxis: { type: 'value', max: 1 },
        series: [
          {
            name: '优化前',
            type: 'bar',
            data: keys.map(k => before[k] || 0),
            itemStyle: { color: '#90a4ae' }
          },
          {
            name: '优化后',
            type: 'bar',
            data: keys.map(k => after[k] || 0),
            itemStyle: { color: '#1a237e' }
          }
        ]
      })
    },
    async loadVisualization() {
      try {
        const response = await this.$axios.get(`/env/${this.selectedEnvId}/visualization`)
        this.vizData = response.data
        this.$nextTick(() => {
          this.renderVizRadarChart()
          this.renderVizTimelineChart()
        })
      } catch (error) {
        console.error('加载可视化数据失败:', error)
        alert(error.response?.data?.error || '加载可视化数据失败')
      }
    },
    renderVizRadarChart() {
      const chart = this.initChart('vizRadarChart')
      if (!chart || !this.vizData) return
      const scores = this.vizData.current_scores
      chart.setOption({
        tooltip: {},
        radar: {
          indicator: [
            { name: '多样性', max: 1 },
            { name: '挑战性', max: 1 },
            { name: '真实性', max: 1 },
            { name: '有效性', max: 1 }
          ],
          shape: 'circle',
          splitNumber: 5
        },
        series: [{
          type: 'radar',
          data: [{
            value: [scores.diversity || 0, scores.challenge || 0, scores.realism || 0, scores.effectiveness || 0],
            name: '当前评分',
            areaStyle: { opacity: 0.3, color: '#4CAF50' },
            lineStyle: { color: '#4CAF50' },
            itemStyle: { color: '#4CAF50' }
          }]
        }]
      })
    },
    renderVizTimelineChart() {
      const chart = this.initChart('vizTimelineChart')
      if (!chart || !this.vizData) return
      const timeline = this.vizData.score_timeline
      const optEntries = timeline.filter(e => e.type === 'optimization')
      if (optEntries.length === 0) {
        chart.setOption({
          title: { text: '暂无优化记录', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } }
        })
        return
      }
      const times = optEntries.map(e => new Date(e.time).toLocaleString())
      const metricKeys = ['diversity', 'challenge', 'realism', 'effectiveness']
      const metricLabels = { diversity: '多样性', challenge: '挑战性', realism: '真实性', effectiveness: '有效性' }
      const colors = { diversity: '#1a237e', challenge: '#e65100', realism: '#2e7d32', effectiveness: '#6a1b9a' }
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: metricKeys.map(k => metricLabels[k]) },
        xAxis: { type: 'category', data: times },
        yAxis: { type: 'value', max: 1 },
        series: metricKeys.map(k => ({
          name: metricLabels[k],
          type: 'line',
          data: optEntries.map(e => (e.scores && e.scores[k]) || null),
          smooth: true,
          lineStyle: { color: colors[k] },
          itemStyle: { color: colors[k] }
        }))
      })
    },
    async loadScheduleInfo() {
      try {
        const response = await this.$axios.get(`/env/${this.selectedEnvId}/schedule-optimization`)
        this.scheduleInfo = response.data
      } catch (error) {
        console.error('加载调度信息失败:', error)
      }
    },
    async createSchedule() {
      try {
        await this.$axios.post(`/env/${this.selectedEnvId}/schedule-optimization`, {
          interval: this.scheduleForm.interval,
          custom_goals: this.scheduleForm.custom_goals
        })
        alert('调度设置成功')
        this.loadScheduleInfo()
      } catch (error) {
        console.error('设置调度失败:', error)
        alert(error.response?.data?.error || '设置调度失败')
      }
    },
    async toggleSchedule(enabled) {
      try {
        await this.$axios.post(`/env/${this.selectedEnvId}/schedule-optimization/toggle`, { enabled })
        this.loadScheduleInfo()
      } catch (error) {
        console.error('切换调度状态失败:', error)
        alert(error.response?.data?.error || '操作失败')
      }
    },
    async cancelSchedule() {
      if (confirm('确定要删除此调度吗？')) {
        this.scheduleInfo = null
      }
    },
    async loadOptimizationHistory() {
      try {
        const response = await this.$axios.get(`/env/${this.selectedEnvId}/optimization-history`)
        this.optimizationHistory = response.data
      } catch (error) {
        console.error('加载优化历史失败:', error)
      }
    },
    viewHistoryDetail(record) {
      this.selectedRecord = record
      this.showDetailModal = true
    },
    async batchOptimize() {
      if (this.batchEnvIds.length === 0) {
        alert('请至少选择一个环境')
        return
      }
      try {
        await this.$axios.post('/env/batch-optimize', {
          env_ids: this.batchEnvIds,
          custom_goals: this.batchCustomGoals
        })
        alert('批量优化完成')
        this.loadEnvironments()
      } catch (error) {
        console.error('批量优化失败:', error)
        alert(error.response?.data?.error || '批量优化失败')
      }
    }
  }
}
</script>

<style scoped>
.env-optimize { max-width: 1200px; margin: 0 auto; padding: 24px; }
.env-optimize h2 { margin-bottom: 20px; color: #1a237e; }
.env-selector { margin-bottom: 20px; }
.env-selector label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; }
.env-selector select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 15px; }
.env-details { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.env-details h3 { margin-bottom: 15px; color: #1a237e; }
.detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-weight: 600; color: #666; font-size: 0.85rem; }
.detail-item span { color: #333; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; width: fit-content; }
.status-badge.created { background: #e3f2fd; color: #1976D2; }
.status-badge.adjusted { background: #f3e5f5; color: #7B1FA2; }
.status-badge.optimized { background: #e0f7fa; color: #0097A7; }
.optimization-section { margin-top: 20px; }
.optimization-section h3 { margin-bottom: 15px; color: #1a237e; }
.tabs { display: flex; flex-wrap: wrap; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; gap: 4px; }
.tab-button { padding: 10px 18px; border: none; background: none; cursor: pointer; font-size: 14px; border-bottom: 3px solid transparent; transition: all 0.2s; color: #666; }
.tab-button:hover { background: #f5f5f5; }
.tab-button.active { border-bottom-color: #1a237e; color: #1a237e; font-weight: 600; }
.tab-content { padding: 20px; background: #fafafa; border-radius: 10px; }
.form-group { margin-bottom: 15px; }
.form-group > label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 15px; }
.form-group input:focus, .form-group select:focus { border-color: #1a237e; outline: none; }
.form-row { display: flex; gap: 15px; margin-bottom: 15px; }
.form-group.half { flex: 1; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
.metric-item { display: flex; flex-direction: column; gap: 4px; }
.metric-item label { font-size: 0.85rem; color: #666; }
.goal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
.goal-item { display: flex; flex-direction: column; gap: 4px; }
.goal-item label { font-size: 0.85rem; color: #666; }
.goal-item input[type="range"] { width: 100%; }
.range-value { font-weight: 600; color: #1a237e; text-align: center; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 12px; max-height: 200px; overflow-y: auto; padding: 10px; background: white; border-radius: 6px; border: 1px solid #ddd; }
.checkbox-label { display: flex; align-items: center; gap: 5px; font-weight: normal; cursor: pointer; font-size: 0.9rem; }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.button { padding: 8px 18px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
.button.primary { background: #1a237e; color: white; }
.button.primary:hover { background: #283593; }
.button.warning { background: #f57c00; color: white; }
.button.warning:hover { background: #e65100; }
.button.danger { background: #d32f2f; color: white; }
.button.danger:hover { background: #b71c1c; }
.button.small { padding: 4px 12px; font-size: 12px; background: #e8eaf6; color: #1a237e; }

.evaluation-results { margin-top: 20px; padding: 20px; background: white; border-radius: 10px; border: 1px solid #e0e0e0; }
.evaluation-results h4 { margin-bottom: 15px; color: #1a237e; }
.eval-charts-row { display: flex; gap: 20px; flex-wrap: wrap; }
.chart-container { flex-shrink: 0; }
.score-details { flex: 1; min-width: 300px; }
.score-grid { display: flex; flex-direction: column; gap: 12px; }
.score-item { display: flex; align-items: center; gap: 10px; }
.score-item label { min-width: 80px; font-size: 0.9rem; color: #666; font-weight: 500; }
.score-bar-wrap { flex: 1; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
.score-bar { height: 100%; background: #1a237e; border-radius: 10px; transition: width 0.5s; }
.score-bar.challenge { background: #e65100; }
.score-bar.realism { background: #2e7d32; }
.score-bar.effectiveness { background: #6a1b9a; }
.score-bar.total { background: #1a237e; }
.score-value { font-weight: 700; color: #333; min-width: 40px; }
.score-value.total { color: #1a237e; font-size: 1.1rem; }
.suggestions { margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }
.suggestions h5 { margin-bottom: 10px; color: #333; }
.suggestions ul { list-style: disc; padding-left: 20px; }
.suggestions li { margin-bottom: 5px; color: #666; font-size: 0.9rem; }

.optimization-results { margin-top: 20px; padding: 20px; background: white; border-radius: 10px; border: 1px solid #e0e0e0; }
.optimization-results h4 { margin-bottom: 15px; color: #1a237e; }
.verification-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 15px; }
.verification-item { padding: 15px; background: #f5f5f5; border-radius: 8px; text-align: center; }
.verification-item label { display: block; font-size: 0.85rem; color: #666; margin-bottom: 6px; }
.big-num { font-size: 1.5rem; font-weight: 700; color: #333; }
.big-num.improved { color: #1a237e; }
.big-num.positive { color: #2e7d32; }
.big-num.negative { color: #d32f2f; }

.viz-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.viz-header h4 { color: #1a237e; }
.viz-content { margin-top: 15px; }
.viz-row { display: flex; gap: 20px; flex-wrap: wrap; }
.viz-card { flex: 1; min-width: 400px; background: white; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; }
.viz-card h5 { margin-bottom: 10px; color: #333; font-size: 0.95rem; }
.viz-summary { margin-top: 20px; display: flex; gap: 30px; flex-wrap: wrap; align-items: flex-start; }
.summary-item { display: flex; flex-direction: column; gap: 4px; }
.summary-item label { font-size: 0.85rem; color: #666; }
.summary-item span { font-size: 1.5rem; font-weight: 700; color: #1a237e; }
.summary-suggestions { flex: 1; }
.summary-suggestions h5 { color: #333; margin-bottom: 8px; }
.summary-suggestions ul { list-style: disc; padding-left: 20px; }
.summary-suggestions li { color: #666; font-size: 0.9rem; margin-bottom: 4px; }
.empty-viz { text-align: center; padding: 40px; color: #999; }

.hint { color: #666; font-size: 0.9rem; margin-bottom: 15px; }
.current-schedule { margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e0e0e0; }
.current-schedule h5 { color: #1a237e; margin-bottom: 10px; }
.schedule-info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 12px; }
.schedule-info-item { display: flex; flex-direction: column; gap: 4px; }
.schedule-info-item label { font-size: 0.85rem; color: #666; }
.schedule-info-item span { font-weight: 500; }
.status-indicator { padding: 3px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; width: fit-content; }
.status-indicator.enabled { background: #e8f5e9; color: #2e7d32; }
.status-indicator.disabled { background: #ffebee; color: #d32f2f; }
.schedule-actions { display: flex; gap: 10px; }
.schedule-form { margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }

.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-card { background: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
.history-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.history-time { color: #666; font-size: 0.85rem; }
.history-trigger { padding: 3px 8px; border-radius: 10px; font-size: 0.8rem; font-weight: 600; }
.history-trigger.manual { background: #e3f2fd; color: #1565c0; }
.history-trigger.auto { background: #e8f5e9; color: #2e7d32; }
.history-trigger.batch { background: #fff3e0; color: #e65100; }
.history-optimizer { color: #999; font-size: 0.85rem; }
.history-scores { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 10px; }
.history-score-item { display: flex; flex-direction: column; gap: 4px; }
.history-score-item label { font-size: 0.8rem; color: #999; }
.mini-scores { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-score { font-size: 0.8rem; color: #333; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }
.improvement-badge { font-weight: 700; font-size: 1rem; }
.improvement-badge.positive { color: #2e7d32; }
.improvement-badge.negative { color: #d32f2f; }
.empty-history { text-align: center; padding: 40px; color: #999; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; border-radius: 12px; width: 100%; max-width: 700px; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #eee; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
.modal-body { padding: 24px; }
.detail-section { margin-bottom: 20px; }
.detail-section h5 { color: #1a237e; margin-bottom: 8px; }
.detail-section pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; }

@media (max-width: 768px) {
  .eval-charts-row, .viz-row { flex-direction: column; }
  .chart-container, .viz-card { min-width: auto; width: 100%; }
  .history-scores { flex-direction: column; }
}
</style>
