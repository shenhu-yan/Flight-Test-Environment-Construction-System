<template>
  <div class="env-adjust">
    <h2>环境动态调整</h2>

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
          <label>环境名称</label>
          <span>{{ selectedEnvironment.env_name }}</span>
        </div>
        <div class="detail-item">
          <label>环境ID</label>
          <span>{{ selectedEnvironment.env_id }}</span>
        </div>
        <div class="detail-item">
          <label>所属项目</label>
          <span>{{ getProjectName(selectedEnvironment.project_id) }}</span>
        </div>
        <div class="detail-item">
          <label>当前状态</label>
          <span :class="['status-badge', selectedEnvironment.status]">{{ statusLabel(selectedEnvironment.status) }}</span>
        </div>
      </div>

      <div v-if="selectedEnvironment.preview_data" class="preview-section">
        <h4>环境预览</h4>
        <div class="preview-grid">
          <div class="preview-card">
            <h5>场景概要</h5>
            <div class="preview-item"><label>地形:</label><span>{{ selectedEnvironment.preview_data.summary?.terrain || '-' }}</span></div>
            <div class="preview-item"><label>气象:</label><span>{{ selectedEnvironment.preview_data.summary?.weather || '-' }}</span></div>
            <div class="preview-item"><label>障碍物数量:</label><span>{{ selectedEnvironment.preview_data.summary?.obstacle_count || 0 }}</span></div>
          </div>
          <div class="preview-card">
            <h5>物理模型</h5>
            <div class="preview-item"><label>飞行力学:</label><span>{{ selectedEnvironment.preview_data.summary?.flight_dynamics || '-' }}</span></div>
            <div class="preview-item"><label>空气动力学:</label><span>{{ selectedEnvironment.preview_data.summary?.aerodynamics || '-' }}</span></div>
          </div>
          <div class="preview-card">
            <h5>奖励机制</h5>
            <div class="preview-item"><label>奖励值:</label><span>{{ selectedEnvironment.preview_data.summary?.reward_value || '-' }}</span></div>
            <div class="preview-item"><label>惩罚规则数:</label><span>{{ selectedEnvironment.preview_data.summary?.penalty_count || 0 }}</span></div>
          </div>
        </div>
      </div>

      <div class="adjustment-section">
        <h3>调整操作</h3>

        <div class="tabs">
          <button :class="['tab-button', { active: activeTab === 'monitor' }]" @click="activeTab = 'monitor'">实时监测</button>
          <button :class="['tab-button', { active: activeTab === 'auto' }]" @click="activeTab = 'auto'">自动调整</button>
          <button :class="['tab-button', { active: activeTab === 'manual' }]" @click="activeTab = 'manual'">手动调整</button>
          <button :class="['tab-button', { active: activeTab === 'history' }]" @click="activeTab = 'history'">调整历史</button>
          <button :class="['tab-button', { active: activeTab === 'visualization' }]" @click="activeTab = 'visualization'">性能对比</button>
        </div>

        <div v-if="activeTab === 'monitor'" class="tab-content">
          <h4>实时性能监测</h4>
          <p class="hint">输入当前训练性能指标，系统将判断是否需要调整环境参数</p>
          <form @submit.prevent="monitorPerformance">
            <div class="form-group">
              <label>性能指标</label>
              <div class="metric-grid">
                <div class="metric-item">
                  <label>奖励值</label>
                  <input type="number" v-model.number="monitorData.reward_value" min="0" max="100" step="0.1">
                  <span class="metric-hint">0-100</span>
                </div>
                <div class="metric-item">
                  <label>成功率</label>
                  <input type="number" v-model.number="monitorData.success_rate" min="0" max="1" step="0.01">
                  <span class="metric-hint">0-1</span>
                </div>
                <div class="metric-item">
                  <label>收敛速度</label>
                  <input type="number" v-model.number="monitorData.convergence_speed" min="0" max="1" step="0.01">
                  <span class="metric-hint">0-1</span>
                </div>
                <div class="metric-item">
                  <label>泛化能力</label>
                  <input type="number" v-model.number="monitorData.generalization_score" min="0" max="1" step="0.01">
                  <span class="metric-hint">0-1</span>
                </div>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="button primary">监测分析</button>
            </div>
          </form>

          <div v-if="monitorResult" class="monitor-result">
            <div :class="['monitor-status', monitorResult.adjustment_needed ? 'warning' : 'ok']">
              <span class="status-icon">{{ monitorResult.adjustment_needed ? '⚠️' : '✅' }}</span>
              <span>{{ monitorResult.adjustment_needed ? '需要调整' : '当前状态良好' }}</span>
            </div>
            <div v-if="monitorResult.adjustment_reason" class="adjustment-reason">
              <h5>调整原因</h5>
              <p v-if="monitorResult.reason_text">{{ monitorResult.reason_text }}</p>
              <p v-else>{{ reasonLabel(monitorResult.adjustment_reason) }}</p>
              <button v-if="monitorResult.adjustment_needed" @click="applyAutoAdjust" class="button primary">立即自动调整</button>
            </div>
            <div v-if="monitorResult.analysis" class="analysis-section">
              <h5>详细分析</h5>
              <div class="analysis-grid">
                <div v-if="monitorResult.analysis.convergence_speed != null" class="analysis-item">
                  <label>收敛速度:</label>
                  <span>{{ (monitorResult.analysis.convergence_speed * 100).toFixed(0) }}%</span>
                </div>
                <div v-if="monitorResult.analysis.success_rate != null" class="analysis-item">
                  <label>成功率:</label>
                  <span>{{ (monitorResult.analysis.success_rate * 100).toFixed(0) }}%</span>
                </div>
                <div v-if="monitorResult.analysis.generalization_score != null" class="analysis-item">
                  <label>泛化能力:</label>
                  <span>{{ (monitorResult.analysis.generalization_score * 100).toFixed(0) }}%</span>
                </div>
              </div>
              <div v-if="monitorResult.analysis.issues && monitorResult.analysis.issues.length > 0" class="issues-list">
                <h6>发现问题:</h6>
                <ul>
                  <li v-for="(issue, index) in monitorResult.analysis.issues" :key="index">{{ issue }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'auto'" class="tab-content">
          <h4>自动调整</h4>
          <p class="hint">系统将根据性能指标自动调整环境参数，如增加复杂度、调整奖励机制等</p>
          <form @submit.prevent="autoAdjust">
            <div class="form-group">
              <label>性能指标</label>
              <div class="metric-grid">
                <div class="metric-item">
                  <label>奖励值</label>
                  <input type="number" v-model.number="performanceData.reward_value" min="0" max="100" step="0.1">
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
              <button type="submit" class="button primary">执行自动调整</button>
            </div>
          </form>

          <div v-if="autoAdjustResult" class="adjust-result">
            <h5>调整结果</h5>
            <div class="result-info">
              <div class="result-item">
                <label>调整ID</label>
                <span>{{ autoAdjustResult.adjustment_id }}</span>
              </div>
              <div class="result-item">
                <label>调整策略</label>
                <span>{{ autoAdjustResult.message }}</span>
              </div>
            </div>
            <div v-if="autoAdjustResult.new_config" class="config-diff">
              <h5>调整后配置</h5>
              <pre>{{ JSON.stringify(autoAdjustResult.new_config, null, 2) }}</pre>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'manual'" class="tab-content">
          <h4>手动调整</h4>
          <p class="hint">手动修改环境参数，系统将记录调整历史</p>
          <form @submit.prevent="manualAdjust">
            <div class="form-group">
              <label>调整原因</label>
              <textarea v-model="manualAdjustForm.reason" placeholder="请输入调整原因" rows="2"></textarea>
            </div>

            <div class="config-section">
              <h5>场景配置</h5>
              <div class="form-row">
                <div class="form-group half">
                  <label for="terrain">地形</label>
                  <select id="terrain" v-model="manualAdjustForm.config.scenario.terrain">
                    <option value="flat">平坦</option>
                    <option value="hilly">丘陵</option>
                    <option value="mountainous">山地</option>
                    <option value="urban">城市</option>
                    <option value="forest">森林</option>
                  </select>
                </div>
                <div class="form-group half">
                  <label for="weather">气象</label>
                  <select id="weather" v-model="manualAdjustForm.config.scenario.weather">
                    <option value="clear">晴朗</option>
                    <option value="windy">有风</option>
                    <option value="light_rain">小雨</option>
                    <option value="heavy_rain">大雨</option>
                    <option value="storm">风暴</option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label>障碍物</label>
                <div class="checkbox-group">
                  <label v-for="obstacle in obstacleOptions" :key="obstacle.value">
                    <input type="checkbox" :value="obstacle.value" v-model="manualAdjustForm.config.scenario.obstacles">
                    {{ obstacle.label }}
                  </label>
                </div>
              </div>
            </div>

            <div class="config-section">
              <h5>物理规则</h5>
              <div class="form-row">
                <div class="form-group half">
                  <label for="flight_dynamics">飞行力学</label>
                  <select id="flight_dynamics" v-model="manualAdjustForm.config.physics.flight_dynamics">
                    <option value="basic">基础</option>
                    <option value="medium">中等</option>
                    <option value="advanced">高级</option>
                  </select>
                </div>
                <div class="form-group half">
                  <label for="aerodynamics">空气动力学</label>
                  <select id="aerodynamics" v-model="manualAdjustForm.config.physics.aerodynamics">
                    <option value="basic">基础</option>
                    <option value="medium">中等</option>
                    <option value="detailed">详细</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="config-section">
              <h5>奖励函数</h5>
              <div class="form-row">
                <div class="form-group half">
                  <label for="reward_value">奖励值</label>
                  <input type="number" id="reward_value" v-model.number="manualAdjustForm.config.reward.reward_value" min="1" max="100">
                </div>
                <div class="form-group half">
                  <label for="target_threshold">目标阈值</label>
                  <input type="number" id="target_threshold" v-model.number="manualAdjustForm.config.reward.target_threshold" min="0.01" max="1" step="0.01">
                </div>
              </div>
              <div class="form-group">
                <label>惩罚规则</label>
                <div class="checkbox-group">
                  <label v-for="rule in penaltyOptions" :key="rule.value">
                    <input type="checkbox" :value="rule.value" v-model="manualAdjustForm.config.reward.penalty_rules">
                    {{ rule.label }}
                  </label>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="button primary">执行手动调整</button>
            </div>
          </form>
        </div>

        <div v-if="activeTab === 'history'" class="tab-content">
          <h4>调整历史</h4>
          <p class="hint">查看环境调整历史记录，支持回滚到历史版本</p>
          <div v-if="adjustments.length > 0" class="history-list">
            <div v-for="adj in adjustments" :key="adj.id" class="history-card">
              <div class="history-header">
                <span class="history-time">{{ formatDate(adj.created_at) }}</span>
                <span :class="['history-trigger', adj.trigger]">{{ triggerLabel(adj.trigger) }}</span>
                <span class="history-adjuster">{{ adj.adjuster }}</span>
              </div>
              <div class="history-body">
                <div v-if="adj.reason" class="history-reason">
                  <label>原因:</label>
                  <span>{{ adj.reason }}</span>
                </div>
                <div v-if="adj.performance_before" class="history-perf">
                  <label>调整前性能:</label>
                  <div class="mini-metrics">
                    <span v-if="adj.performance_before.reward_value != null">奖励: {{ adj.performance_before.reward_value }}</span>
                    <span v-if="adj.performance_before.success_rate != null">成功率: {{ adj.performance_before.success_rate }}</span>
                    <span v-if="adj.performance_before.convergence_speed != null">收敛: {{ adj.performance_before.convergence_speed }}</span>
                  </div>
                </div>
                <div v-if="adj.performance_after" class="history-perf">
                  <label>调整后性能:</label>
                  <div class="mini-metrics">
                    <span v-if="adj.performance_after.reward_value != null">奖励: {{ adj.performance_after.reward_value }}</span>
                    <span v-if="adj.performance_after.success_rate != null">成功率: {{ adj.performance_after.success_rate }}</span>
                    <span v-if="adj.performance_after.convergence_speed != null">收敛: {{ adj.performance_after.convergence_speed }}</span>
                  </div>
                </div>
              </div>
              <div class="history-actions">
                <button @click="viewAdjustment(adj)" class="button small">查看详情</button>
                <button @click="rollbackAdjustment(adj.id)" class="button small warning">回滚</button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂无调整历史记录</p>
          </div>
        </div>

        <div v-if="activeTab === 'visualization'" class="tab-content">
          <div class="viz-header">
            <h4>性能对比可视化</h4>
            <button @click="loadVisualization" class="button primary">加载数据</button>
          </div>

          <div v-if="vizData" class="viz-content">
            <div class="viz-row">
              <div class="viz-card">
                <h5>调整前后性能对比</h5>
                <div ref="compareChart" style="width:100%;height:350px;"></div>
              </div>
              <div class="viz-card">
                <h5>调整历史时间线</h5>
                <div ref="timelineChart" style="width:100%;height:350px;"></div>
              </div>
            </div>
            <div class="viz-summary">
              <div class="summary-item">
                <label>调整次数</label>
                <span class="big-num">{{ vizData.adjustment_count }}</span>
              </div>
              <div class="summary-item">
                <label>优化次数</label>
                <span class="big-num">{{ vizData.optimization_count }}</span>
              </div>
              <div v-if="vizData.suggestions.length > 0" class="summary-suggestions">
                <h5>当前建议</h5>
                <ul>
                  <li v-for="(s, i) in vizData.suggestions" :key="i">{{ s }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>点击"加载数据"查看性能对比可视化</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAdjustmentModal" class="modal-overlay" @click.self="showAdjustmentModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>调整详情</h3>
          <button @click="showAdjustmentModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedAdjustment">
          <div class="detail-item">
            <label>调整时间</label>
            <span>{{ formatDate(selectedAdjustment.created_at) }}</span>
          </div>
          <div class="detail-item">
            <label>调整人</label>
            <span>{{ selectedAdjustment.adjuster }}</span>
          </div>
          <div class="detail-item">
            <label>触发方式</label>
            <span>{{ triggerLabel(selectedAdjustment.trigger) }}</span>
          </div>
          <div class="detail-item">
            <label>调整原因</label>
            <span>{{ selectedAdjustment.reason || '-' }}</span>
          </div>
          <div v-if="selectedAdjustment.performance_before" class="detail-item">
            <label>调整前性能</label>
            <pre>{{ JSON.stringify(selectedAdjustment.performance_before, null, 2) }}</pre>
          </div>
          <div v-if="selectedAdjustment.performance_after" class="detail-item">
            <label>调整后性能</label>
            <pre>{{ JSON.stringify(selectedAdjustment.performance_after, null, 2) }}</pre>
          </div>
          <div class="detail-item">
            <label>调整参数</label>
            <pre>{{ JSON.stringify(selectedAdjustment.params, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'EnvAdjust',
  data() {
    return {
      environments: [],
      projects: [],
      selectedEnvId: '',
      selectedEnvironment: null,
      activeTab: 'monitor',
      monitorData: {
        reward_value: 0,
        success_rate: 0.5,
        convergence_speed: 0.5,
        generalization_score: 0.5
      },
      monitorResult: null,
      performanceData: {
        reward_value: 0,
        success_rate: 0.5,
        convergence_speed: 0.5,
        generalization_score: 0.5
      },
      autoAdjustResult: null,
      manualAdjustForm: {
        reason: '',
        config: {
          scenario: { terrain: 'flat', weather: 'clear', obstacles: [] },
          physics: { flight_dynamics: 'basic', aerodynamics: 'basic', collision_detection: 'enabled' },
          reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 }
        }
      },
      obstacleOptions: [
        { value: 'building', label: '建筑物' },
        { value: 'tree', label: '树木' },
        { value: 'lamp_post', label: '路灯' },
        { value: 'wind_turbine', label: '风力发电机' },
        { value: 'power_line', label: '电线' }
      ],
      penaltyOptions: [
        { value: 'collision', label: '碰撞' },
        { value: 'out_of_bounds', label: '越界' },
        { value: 'fault', label: '故障' },
        { value: 'timeout', label: '超时' }
      ],
      adjustments: [],
      showAdjustmentModal: false,
      selectedAdjustment: null,
      vizData: null,
      compareChartInstance: null,
      timelineChartInstance: null
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
    if (this.compareChartInstance) this.compareChartInstance.dispose()
    if (this.timelineChartInstance) this.timelineChartInstance.dispose()
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
          this.manualAdjustForm.config = JSON.parse(JSON.stringify(this.selectedEnvironment.config || {}))
          this.autoAdjustResult = null
          this.monitorResult = null
          this.vizData = null
          this.loadAdjustments()
        } catch (error) {
          console.error('加载环境详情失败:', error)
          alert('加载环境详情失败')
        }
      } else {
        this.selectedEnvironment = null
        this.adjustments = []
      }
    },
    async loadAdjustments() {
      if (this.selectedEnvId) {
        try {
          const response = await this.$axios.get(`/env/${this.selectedEnvId}/adjustments`)
          this.adjustments = response.data
        } catch (error) {
          console.error('加载调整历史失败:', error)
        }
      }
    },
    getProjectName(projectId) {
      const project = this.projects.find(p => p.id == projectId)
      return project ? project.project_name : '未知项目'
    },
    statusLabel(status) {
      const map = { created: '已创建', running: '运行中', completed: '已完成', failed: '失败', adjusted: '已调整', optimized: '已优化' }
      return map[status] || status
    },
    triggerLabel(trigger) {
      const map = { auto: '自动', manual: '手动', batch: '批量' }
      return map[trigger] || trigger
    },
    reasonLabel(reason) {
      const map = {
        convergence_too_fast: '收敛速度过快，环境过于简单，需要增加复杂度',
        convergence_too_slow: '收敛速度过慢，环境可能过于困难，需要降低复杂度',
        low_generalization: '泛化能力不足，需要增加环境多样性'
      }
      return map[reason] || reason
    },
    async monitorPerformance() {
      try {
        const response = await this.$axios.post(`/env/${this.selectedEnvId}/monitor`, {
          performance_data: this.monitorData
        })
        this.monitorResult = response.data
        if (response.data.adjustment_needed) {
          console.log('监测结果:', response.data)
        }
      } catch (error) {
        console.error('监测失败:', error)
        alert(error.response?.data?.error || '监测失败')
      }
    },
    async applyAutoAdjust() {
      try {
        const response = await this.$axios.post(`/env/${this.selectedEnvId}/auto-adjust`, {
          performance_data: this.monitorData
        })
        alert('自动调整成功')
        this.autoAdjustResult = response.data
        this.monitorResult = null
        this.loadEnvironment()
      } catch (error) {
        console.error('自动调整失败:', error)
        alert(error.response?.data?.error || '自动调整失败')
      }
    },
    async autoAdjust() {
      try {
        const response = await this.$axios.post(`/env/${this.selectedEnvId}/auto-adjust`, {
          performance_data: this.performanceData
        })
        alert('自动调整成功')
        this.autoAdjustResult = response.data
        this.loadEnvironment()
      } catch (error) {
        console.error('自动调整失败:', error)
        alert(error.response?.data?.error || '自动调整失败')
      }
    },
    async manualAdjust() {
      try {
        await this.$axios.post(`/env/${this.selectedEnvId}/manual-adjust`, {
          adjustment_params: this.manualAdjustForm.config,
          reason: this.manualAdjustForm.reason
        })
        alert('手动调整成功')
        this.loadEnvironment()
      } catch (error) {
        console.error('手动调整失败:', error)
        alert(error.response?.data?.error || '手动调整失败')
      }
    },
    viewAdjustment(adjustment) {
      this.selectedAdjustment = adjustment
      this.showAdjustmentModal = true
    },
    async rollbackAdjustment(adjustmentId) {
      if (confirm('确定要回滚到这个调整版本吗？')) {
        try {
          await this.$axios.post(`/env/${this.selectedEnvId}/rollback/${adjustmentId}`)
          alert('回滚成功')
          this.loadEnvironment()
        } catch (error) {
          console.error('回滚失败:', error)
          alert(error.response?.data?.error || '回滚失败')
        }
      }
    },
    async loadVisualization() {
      try {
        const response = await this.$axios.get(`/env/${this.selectedEnvId}/visualization`)
        this.vizData = response.data
        this.$nextTick(() => {
          this.renderCompareChart()
          this.renderTimelineChart()
        })
      } catch (error) {
        console.error('加载可视化数据失败:', error)
        alert('加载可视化数据失败')
      }
    },
    renderCompareChart() {
      if (!this.vizData || !this.$refs.compareChart) return
      if (this.compareChartInstance) this.compareChartInstance.dispose()
      this.compareChartInstance = echarts.init(this.$refs.compareChart)

      const scores = this.vizData.current_scores || {}
      const categories = ['多样性', '挑战性', '真实性', '有效性']
      const keys = ['diversity', 'challenge', 'realism', 'effectiveness']
      const currentValues = keys.map(k => ((scores[k] || 0) * 100).toFixed(1))

      const adjRecords = this.adjustments || []
      const beforeValues = adjRecords.length > 0 && adjRecords[0].performance_before
        ? keys.map(k => {
            const perf = adjRecords[0].performance_before || {}
            return ((perf[k] || scores[k] || 0) * 100).toFixed(1)
          })
        : keys.map(k => ((scores[k] || 0) * 80 / 100).toFixed(1))

      this.compareChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['调整前', '当前'] },
        xAxis: { type: 'category', data: categories },
        yAxis: { type: 'value', max: 100, name: '评分' },
        series: [
          { name: '调整前', type: 'bar', data: beforeValues, itemStyle: { color: '#90CAF9' } },
          { name: '当前', type: 'bar', data: currentValues, itemStyle: { color: '#1a237e' } }
        ]
      })
    },
    renderTimelineChart() {
      if (!this.vizData || !this.$refs.timelineChart) return
      if (this.timelineChartInstance) this.timelineChartInstance.dispose()
      this.timelineChartInstance = echarts.init(this.$refs.timelineChart)

      const timeline = this.vizData.score_timeline || []
      const times = timeline.map(t => {
        const d = new Date(t.time)
        return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
      })
      const types = timeline.map(t => t.type === 'optimization' ? '优化' : '调整')

      this.timelineChartInstance.setOption({
        tooltip: {
          trigger: 'axis',
          formatter(params) {
            const p = params[0]
            const item = timeline[p.dataIndex]
            let html = `${p.name}<br/>类型: ${item.type === 'optimization' ? '优化' : '调整'}`
            if (item.scores) {
              html += `<br/>多样性: ${(item.scores.diversity * 100).toFixed(1)}`
              html += `<br/>挑战性: ${(item.scores.challenge * 100).toFixed(1)}`
            }
            if (item.improvement != null) {
              html += `<br/>改进: ${(item.improvement * 100).toFixed(1)}%`
            }
            return html
          }
        },
        xAxis: { type: 'category', data: times, axisLabel: { rotate: 30 } },
        yAxis: { type: 'category', data: ['调整', '优化'], name: '操作类型' },
        series: [{
          type: 'scatter',
          data: timeline.map((t, i) => [i, t.type === 'optimization' ? 1 : 0]),
          symbolSize: 16,
          itemStyle: {
            color(params) {
              return params.value[1] === 1 ? '#4CAF50' : '#FF9800'
            }
          }
        }]
      })
    },
    formatDate(dateString) {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.env-adjust { max-width: 1200px; margin: 0 auto; padding: 24px; }
.env-adjust h2 { margin-bottom: 20px; color: #1a237e; font-size: 1.5rem; }
.env-selector { margin-bottom: 20px; }
.env-selector label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; }
.env-selector select { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; }
.env-selector select:focus { border-color: #1a237e; outline: none; }
.env-details { background-color: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.env-details h3 { margin-bottom: 15px; color: #1a237e; }
.detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-weight: 600; color: #666; font-size: 0.85rem; }
.detail-item span { color: #333; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; width: fit-content; }
.status-badge.created { background-color: #e3f2fd; color: #1976D2; }
.status-badge.running { background-color: #e8f5e9; color: #388E3C; }
.status-badge.completed { background-color: #fff3e0; color: #F57C00; }
.status-badge.failed { background-color: #ffebee; color: #D32F2F; }
.status-badge.adjusted { background-color: #f3e5f5; color: #7B1FA2; }
.status-badge.optimized { background-color: #e0f7fa; color: #0097A7; }

.preview-section { margin-bottom: 20px; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.preview-section h4 { margin-bottom: 12px; color: #1a237e; font-size: 1rem; }
.preview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.preview-card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.preview-card h5 { margin-bottom: 8px; color: #333; font-size: 0.9rem; }
.preview-item { display: flex; justify-content: space-between; padding: 2px 0; font-size: 0.85rem; }
.preview-item label { color: #666; }

.adjustment-section { margin-top: 20px; }
.adjustment-section h3 { margin-bottom: 15px; color: #1a237e; }
.tabs { display: flex; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
.tab-button { padding: 10px 20px; border: none; background: none; cursor: pointer; font-size: 14px; border-bottom: 3px solid transparent; transition: all 0.2s; color: #666; }
.tab-button:hover { background-color: #f5f5f5; }
.tab-button.active { border-bottom-color: #1a237e; color: #1a237e; font-weight: 600; }
.tab-content { padding: 20px; background-color: #f9f9ff; border-radius: 8px; }
.tab-content h4 { margin-bottom: 12px; color: #1a237e; }
.hint { color: #888; font-size: 0.9rem; margin-bottom: 16px; }

.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 15px; transition: border-color 0.2s; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #1a237e; outline: none; }
.form-group textarea { resize: vertical; min-height: 80px; }
.form-row { display: flex; gap: 15px; margin-bottom: 15px; }
.form-group.half { flex: 1; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
.metric-item { display: flex; flex-direction: column; gap: 4px; }
.metric-item label { font-size: 0.85rem; color: #666; }
.metric-hint { font-size: 0.75rem; color: #aaa; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 12px; }
.checkbox-group label { display: flex; align-items: center; gap: 5px; font-weight: normal; cursor: pointer; font-size: 0.9rem; }
.config-section { margin-bottom: 20px; padding: 16px; background-color: white; border-radius: 8px; border: 1px solid #eee; }
.config-section h5 { margin-bottom: 10px; color: #1a237e; font-size: 0.95rem; }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }

.button { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.button.primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.button.primary:hover { box-shadow: 0 2px 8px rgba(26,35,126,0.3); }
.button.small { padding: 4px 10px; font-size: 0.8rem; background-color: #1976d2; color: white; }
.button.small:hover { background-color: #1565c0; }
.button.small.warning { background-color: #FF9800; color: white; }
.button.small.warning:hover { background-color: #F57C00; }

.monitor-result { margin-top: 20px; padding: 16px; background: white; border-radius: 8px; }
.monitor-status { display: flex; align-items: center; gap: 8px; padding: 12px; border-radius: 8px; font-weight: 600; }
.monitor-status.warning { background: #fff3e0; color: #E65100; }
.monitor-status.ok { background: #e8f5e9; color: #2E7D32; }
.status-icon { font-size: 1.2rem; }
.adjustment-reason { margin-top: 12px; padding: 12px; background: #fafafa; border-radius: 8px; }
.adjustment-reason h5 { margin-bottom: 8px; color: #333; }
.adjustment-reason p { color: #666; margin-bottom: 12px; }
.analysis-section { margin-top: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px; border: 1px solid #eee; }
.analysis-section h5 { margin-bottom: 10px; color: #333; font-size: 0.9rem; }
.analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 12px; }
.analysis-item { display: flex; justify-content: space-between; align-items: center; background: white; padding: 8px 12px; border-radius: 6px; }
.analysis-item label { font-size: 0.85rem; color: #666; font-weight: 600; }
.analysis-item span { color: #1a237e; font-weight: 700; }
.issues-list h6 { font-size: 0.85rem; color: #d32f2f; margin-bottom: 6px; }
.issues-list ul { padding-left: 16px; margin: 0; }
.issues-list li { font-size: 0.85rem; color: #666; margin-bottom: 4px; list-style-type: disc; }

.adjust-result { margin-top: 20px; padding: 16px; background: white; border-radius: 8px; }
.adjust-result h5 { margin-bottom: 12px; color: #1a237e; }
.result-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }
.result-item { display: flex; flex-direction: column; gap: 4px; }
.result-item label { font-size: 0.85rem; color: #666; font-weight: 600; }
.config-diff pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; }

.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-card { background: white; padding: 16px; border-radius: 8px; border: 1px solid #eee; }
.history-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.history-time { color: #888; font-size: 0.85rem; }
.history-trigger { padding: 3px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.history-trigger.auto { background: #e3f2fd; color: #1976D2; }
.history-trigger.manual { background: #fff3e0; color: #F57C00; }
.history-trigger.batch { background: #f3e5f5; color: #7B1FA2; }
.history-adjuster { color: #666; font-size: 0.85rem; }
.history-body { margin-bottom: 10px; }
.history-reason { margin-bottom: 6px; font-size: 0.9rem; }
.history-reason label { font-weight: 600; color: #666; font-size: 0.85rem; }
.history-perf { margin-bottom: 4px; }
.history-perf label { font-weight: 600; color: #666; font-size: 0.85rem; }
.mini-metrics { display: flex; gap: 12px; flex-wrap: wrap; }
.mini-metrics span { font-size: 0.85rem; color: #333; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }
.history-actions { display: flex; gap: 8px; }

.empty-state { text-align: center; color: #999; padding: 40px 20px; }

.viz-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.viz-content { margin-top: 16px; }
.viz-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 16px; }
.viz-card { background: white; padding: 16px; border-radius: 8px; border: 1px solid #eee; }
.viz-card h5 { margin-bottom: 12px; color: #333; font-size: 0.95rem; }
.viz-summary { display: flex; gap: 24px; flex-wrap: wrap; padding: 16px; background: white; border-radius: 8px; }
.summary-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.summary-item label { font-size: 0.85rem; color: #666; font-weight: 600; }
.big-num { font-size: 1.8rem; font-weight: 700; color: #1a237e; }
.summary-suggestions { flex: 1; min-width: 200px; }
.summary-suggestions h5 { margin-bottom: 8px; color: #333; font-size: 0.9rem; }
.summary-suggestions ul { padding-left: 16px; }
.summary-suggestions li { font-size: 0.85rem; color: #666; margin-bottom: 4px; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background-color: white; padding: 0; border-radius: 12px; width: 100%; max-width: 700px; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
.modal-body { padding: 24px; }
.modal-body .detail-item { margin-bottom: 15px; }
.modal-body .detail-item label { display: block; margin-bottom: 4px; font-weight: 600; color: #666; font-size: 0.85rem; }
.modal-body .detail-item pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; }

@media (max-width: 768px) {
  .form-row { flex-direction: column; }
  .metric-grid { grid-template-columns: 1fr 1fr; }
  .viz-row { grid-template-columns: 1fr; }
  .preview-grid { grid-template-columns: 1fr; }
}
</style>
