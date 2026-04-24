<template>
  <div class="env-optimize">
    <h2>环境优化</h2>
    <div class="env-selector">
      <label>选择环境</label>
      <select v-model.number="selectedEnvId" @change="loadEnvironment">
        <option value="">请选择环境</option>
        <option v-for="env in environments" :key="env.id" :value="env.id">{{ env.env_name }} ({{ env.env_id }})</option>
      </select>
    </div>
    <div v-if="selectedEnvironment" class="env-details">
      <h3>环境详情</h3>
      <div class="detail-grid">
        <div class="detail-item"><label>环境名称</label><span>{{ selectedEnvironment.env_name }}</span></div>
        <div class="detail-item"><label>环境ID</label><span>{{ selectedEnvironment.env_id }}</span></div>
        <div class="detail-item"><label>项目</label><span>{{ getProjectName(selectedEnvironment.project_id) }}</span></div>
        <div class="detail-item"><label>状态</label><span :class="['status-badge', selectedEnvironment.status]">{{ statusLabel(selectedEnvironment.status) }}</span></div>
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
          <h4>环境性能评估</h4>
          <div class="eval-grid">
            <div class="eval-card"><label>奖励值</label><div class="eval-value">{{ performanceData.reward_value }}</div><div ref="rewardChart" style="width:100%;height:160px;"></div></div>
            <div class="eval-card"><label>成功率</label><div class="eval-value">{{ (performanceData.success_rate * 100).toFixed(1) }}%</div><div ref="successChart" style="width:100%;height:160px;"></div></div>
            <div class="eval-card"><label>收敛速度</label><div class="eval-value">{{ (performanceData.convergence_speed * 100).toFixed(1) }}%</div><div ref="convergenceChart" style="width:100%;height:160px;"></div></div>
            <div class="eval-card"><label>泛化评分</label><div class="eval-value">{{ (performanceData.generalization_score * 100).toFixed(1) }}%</div><div ref="generalChart" style="width:100%;height:160px;"></div></div>
          </div>
          <div class="form-actions"><button @click="evaluateEnvironment" class="btn btn-primary">执行评估</button></div>
          <div v-if="evalResult" class="result-section">
            <h4>评估结果</h4>
            <div class="result-grid">
              <div class="result-item"><label>综合评分</label><span>{{ evalResult.overall_score }}</span></div>
              <div class="result-item"><label>优化建议</label><span>{{ evalResult.suggestion }}</span></div>
              <div class="result-item"><label>优先级</label><span :class="['priority-badge', evalResult.priority]">{{ evalResult.priority }}</span></div>
              <div class="result-item"><label>预计提升</label><span>{{ evalResult.estimated_improvement }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'optimize'" class="tab-content">
          <h4>环境优化配置</h4>
          <div class="form-row">
            <div class="form-group half"><label>优化算法</label>
              <select v-model="optimizeForm.algorithm"><option value="pso">粒子群优化</option><option value="ga">遗传算法</option><option value="bayesian">贝叶斯优化</option><option value="rl">强化学习优化</option></select>
            </div>
            <div class="form-group half"><label>优化目标</label>
              <select v-model="optimizeForm.objective"><option value="reward">最大化奖励</option><option value="success_rate">最大化成功率</option><option value="convergence">加速收敛</option><option value="generalization">提升泛化</option></select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group third"><label>最大迭代次数</label><input type="number" v-model.number="optimizeForm.max_iterations" min="1" max="500"></div>
            <div class="form-group third"><label>种群大小</label><input type="number" v-model.number="optimizeForm.population_size" min="10" max="200"></div>
            <div class="form-group third"><label>变异率</label><input type="number" v-model.number="optimizeForm.mutation_rate" min="0.01" max="0.5" step="0.01"></div>
          </div>
          <div class="form-actions"><button @click="optimizeEnvironment" class="btn btn-primary">执行优化</button></div>
          <div v-if="optimizeResult" class="result-section">
            <h4>优化结果</h4>
            <div class="result-grid">
              <div class="result-item"><label>优化前评分</label><span>{{ optimizeResult.before_score }}</span></div>
              <div class="result-item"><label>优化后评分</label><span>{{ optimizeResult.after_score }}</span></div>
              <div class="result-item"><label>迭代次数</label><span>{{ optimizeResult.iterations }}</span></div>
              <div class="result-item"><label>提升幅度</label><span>{{ optimizeResult.improvement }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'visualization'" class="tab-content">
          <h4>优化可视化</h4>
          <div ref="optimizationChart" style="width:100%;height:400px;"></div>
        </div>
        <div v-if="activeTab === 'schedule'" class="tab-content">
          <h4>持续优化调度</h4>
          <div class="form-row">
            <div class="form-group half"><label>调度频率</label>
              <select v-model="scheduleForm.frequency"><option value="hourly">每小时</option><option value="daily">每天</option><option value="weekly">每周</option></select>
            </div>
            <div class="form-group half"><label>优化阈值</label><input type="number" v-model.number="scheduleForm.threshold" min="0" max="100"></div>
          </div>
          <div class="form-group"><label>启用自动优化</label><input type="checkbox" v-model="scheduleForm.enabled"></div>
          <div class="form-actions"><button @click="saveSchedule" class="btn btn-primary">保存调度</button></div>
          <div v-if="scheduleResult" class="result-section"><p>{{ scheduleResult }}</p></div>
        </div>
        <div v-if="activeTab === 'history'" class="tab-content">
          <h4>优化历史</h4>
          <table class="data-table">
            <thead><tr><th>时间</th><th>算法</th><th>目标</th><th>提升</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="h in optimizeHistory" :key="h.id"><td>{{ h.time }}</td><td>{{ h.algorithm }}</td><td>{{ h.objective }}</td><td>{{ h.improvement }}</td><td><span :class="['status-badge', h.status]">{{ h.status }}</span></td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="activeTab === 'batch'" class="tab-content">
          <h4>批量优化</h4>
          <div class="batch-env-list">
            <label v-for="env in environments" :key="env.id" class="batch-item">
              <input type="checkbox" :value="env.id" v-model="batchEnvIds">{{ env.env_name }}
            </label>
          </div>
          <div class="form-row">
            <div class="form-group half"><label>优化算法</label>
              <select v-model="batchForm.algorithm"><option value="pso">粒子群优化</option><option value="ga">遗传算法</option><option value="bayesian">贝叶斯优化</option></select>
            </div>
            <div class="form-group half"><label>优化目标</label>
              <select v-model="batchForm.objective"><option value="reward">最大化奖励</option><option value="success_rate">最大化成功率</option></select>
            </div>
          </div>
          <div class="form-actions"><button @click="batchOptimize" class="btn btn-primary">执行批量优化</button></div>
          <div v-if="batchResult" class="result-section"><p>{{ batchResult }}</p></div>
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
      selectedEnvId: '',
      selectedEnvironment: null,
      activeTab: 'evaluate',
      environments: [
        { id: 1, env_name: '城市飞行测试', env_id: 'ENV-001', project_id: 1, status: 'running' },
        { id: 2, env_name: '山地风暴测试', env_id: 'ENV-002', project_id: 2, status: 'optimized' },
        { id: 3, env_name: '森林避障训练', env_id: 'ENV-003', project_id: 1, status: 'adjusted' },
        { id: 4, env_name: '丘陵导航环境', env_id: 'ENV-004', project_id: 3, status: 'created' }
      ],
      projects: [{ id: 1, project_name: '无人机避障训练' }, { id: 2, project_name: '固定翼导航测试' }, { id: 3, project_name: '旋翼控制优化' }],
      performanceData: { reward_value: 18, success_rate: 0.68, convergence_speed: 0.55, generalization_score: 0.62 },
      evalResult: null,
      optimizeForm: { algorithm: 'pso', objective: 'reward', max_iterations: 100, population_size: 50, mutation_rate: 0.1 },
      optimizeResult: null,
      scheduleForm: { frequency: 'daily', threshold: 70, enabled: false },
      scheduleResult: null,
      batchEnvIds: [],
      batchForm: { algorithm: 'pso', objective: 'reward' },
      batchResult: null,
      optimizeHistory: [
        { id: 1, time: '2026-04-22 16:00', algorithm: '粒子群优化', objective: '最大化奖励', improvement: '+12.5%', status: 'success' },
        { id: 2, time: '2026-04-21 14:30', algorithm: '贝叶斯优化', objective: '最大化成功率', improvement: '+8.3%', status: 'success' },
        { id: 3, time: '2026-04-20 10:00', algorithm: '遗传算法', objective: '加速收敛', improvement: '+5.1%', status: 'success' }
      ],
      chartInstances: []
    }
  },
  beforeUnmount() { this.chartInstances.forEach(c => c.dispose()) },
  methods: {
    statusLabel(s) { return { created: '已创建', running: '运行中', adjusted: '已调整', optimized: '已优化' }[s] || s },
    getProjectName(pid) { return this.projects.find(p => p.id === pid)?.project_name || '-' },
    loadEnvironment() {
      this.selectedEnvironment = this.environments.find(e => e.id === this.selectedEnvId) || null
      this.evalResult = null; this.optimizeResult = null
      if (this.selectedEnvironment) this.$nextTick(() => this.renderEvalCharts())
    },
    renderEvalCharts() {
      this.chartInstances.forEach(c => c.dispose())
      this.chartInstances = []
      const refs = [this.$refs.rewardChart, this.$refs.successChart, this.$refs.convergenceChart, this.$refs.generalChart]
      const vals = [this.performanceData.reward_value, this.performanceData.success_rate * 100, this.performanceData.convergence_speed * 100, this.performanceData.generalization_score * 100]
      const colors = ['#1a237e', '#2e7d32', '#e65100', '#7b1fa2']
      refs.forEach((ref, i) => {
        if (!ref) return
        const chart = echarts.init(ref)
        chart.setOption({
          series: [{ type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100, detail: { formatter: '{value}', fontSize: 14 }, data: [{ value: vals[i].toFixed(1) }], axisLine: { lineStyle: { width: 8, color: [[0.3, '#f44336'], [0.7, '#FF9800'], [1, colors[i]]] } }, pointer: { width: 3 } }]
        })
        this.chartInstances.push(chart)
      })
    },
    evaluateEnvironment() {
      this.performanceData = { reward_value: Math.round(Math.random() * 30 + 10), success_rate: Math.random() * 0.5 + 0.3, convergence_speed: Math.random() * 0.5 + 0.3, generalization_score: Math.random() * 0.5 + 0.3 }
      this.evalResult = { overall_score: (Math.random() * 30 + 60).toFixed(1), suggestion: this.performanceData.success_rate < 0.5 ? '建议优化奖励函数和场景配置' : '环境表现良好，可进行微调', priority: this.performanceData.success_rate < 0.5 ? 'high' : 'low', estimated_improvement: '+' + (Math.random() * 15 + 5).toFixed(1) + '%' }
      this.$nextTick(() => this.renderEvalCharts())
    },
    optimizeEnvironment() {
      const before = (Math.random() * 30 + 50).toFixed(1)
      const after = (parseFloat(before) + Math.random() * 20 + 5).toFixed(1)
      this.optimizeResult = { before_score: before, after_score: after, iterations: Math.floor(Math.random() * 80 + 20), improvement: '+' + (after - before).toFixed(1) + '%' }
    },
    renderOptimizationChart() {
      if (!this.$refs.optimizationChart) return
      const chart = echarts.init(this.$refs.optimizationChart)
      const iterations = Array.from({ length: 50 }, (_, i) => i + 1)
      let val = 50
      const data = iterations.map(() => { val += Math.random() * 4 - 1; return Math.max(0, Math.min(100, val)).toFixed(1) })
      chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: iterations, name: '迭代次数' },
        yAxis: { type: 'value', name: '评分', min: 0, max: 100 },
        series: [{ type: 'line', data, smooth: true, itemStyle: { color: '#1a237e' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(26,35,126,0.3)' }, { offset: 1, color: 'rgba(26,35,126,0.05)' }]) } }]
      })
      this.chartInstances.push(chart)
    },
    saveSchedule() { this.scheduleResult = '调度配置已保存！（前端演示，无后端）' },
    batchOptimize() {
      if (this.batchEnvIds.length === 0) { alert('请选择至少一个环境'); return }
      this.batchResult = `已对 ${this.batchEnvIds.length} 个环境执行批量优化！（前端演示，无后端）`
    }
  },
  watch: {
    activeTab(val) { if (val === 'visualization') this.$nextTick(() => this.renderOptimizationChart()) }
  }
}
</script>

<style scoped>
.env-optimize { max-width: 1000px; margin: 0 auto; padding: 24px; }
h2 { color: #1a237e; font-size: 1.5rem; margin-bottom: 16px; }
.env-selector { margin-bottom: 20px; }
.env-selector label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; }
.env-selector select { padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; min-width: 300px; outline: none; }
.env-details { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
h3 { color: #1a237e; margin-bottom: 12px; }
.detail-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.detail-item label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 2px; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.status-badge.created { background: #e3f2fd; color: #1565c0; }
.status-badge.running { background: #e8f5e9; color: #2e7d32; }
.status-badge.adjusted { background: #f3e5f5; color: #7b1fa2; }
.status-badge.optimized { background: #e0f7fa; color: #00838f; }
.status-badge.success { background: #e8f5e9; color: #2e7d32; }
.priority-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.priority-badge.high { background: #ffebee; color: #c62828; }
.priority-badge.low { background: #e8f5e9; color: #2e7d32; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; flex-wrap: wrap; }
.tab-button { padding: 8px 14px; border: none; background: #e0e0e0; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 0.85rem; }
.tab-button.active { background: #1a237e; color: white; }
.tab-content { background: #fafafa; border-radius: 8px; padding: 20px; }
.eval-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.eval-card { background: white; border-radius: 8px; padding: 14px; text-align: center; }
.eval-card label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 4px; }
.eval-value { font-size: 1.4rem; font-weight: 700; color: #1a237e; margin-bottom: 4px; }
.result-section { margin-top: 16px; padding: 16px; background: white; border-radius: 8px; }
.result-section h4 { color: #1a237e; margin-bottom: 10px; }
.result-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.result-item label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 2px; }
.form-row { display: flex; gap: 16px; }
.form-group { margin-bottom: 16px; }
.form-group.half { flex: 1; }
.form-group.third { flex: 1; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #3f51b5; }
.form-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background: #f5f5f5; font-weight: 600; font-size: 0.85rem; }
.batch-env-list { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.batch-item { display: flex; align-items: center; gap: 4px; font-size: 0.9rem; cursor: pointer; }
</style>
