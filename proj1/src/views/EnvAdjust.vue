<template>
  <div class="env-adjust">
    <h2>环境动态调整</h2>
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
        <div class="detail-item"><label>所属项目</label><span>{{ getProjectName(selectedEnvironment.project_id) }}</span></div>
        <div class="detail-item"><label>当前状态</label><span :class="['status-badge', selectedEnvironment.status]">{{ statusLabel(selectedEnvironment.status) }}</span></div>
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
          <div class="monitor-grid">
            <div class="monitor-card"><h4>奖励值</h4><div class="monitor-value">{{ monitorData.reward_value }}</div><div ref="rewardGauge" style="width:100%;height:200px;"></div></div>
            <div class="monitor-card"><h4>成功率</h4><div class="monitor-value">{{ (monitorData.success_rate * 100).toFixed(1) }}%</div><div ref="successGauge" style="width:100%;height:200px;"></div></div>
            <div class="monitor-card"><h4>收敛速度</h4><div class="monitor-value">{{ (monitorData.convergence_speed * 100).toFixed(1) }}%</div><div ref="convergenceGauge" style="width:100%;height:200px;"></div></div>
            <div class="monitor-card"><h4>泛化评分</h4><div class="monitor-value">{{ (monitorData.generalization_score * 100).toFixed(1) }}%</div><div ref="generalGauge" style="width:100%;height:200px;"></div></div>
          </div>
          <div class="monitor-actions"><button @click="monitorPerformance" class="btn btn-primary">刷新监测</button></div>
          <div v-if="monitorResult" class="monitor-result">
            <h4>监测结果</h4>
            <div class="result-grid">
              <div class="result-item"><label>综合评分</label><span>{{ monitorResult.overall_score }}</span></div>
              <div class="result-item"><label>建议操作</label><span>{{ monitorResult.suggestion }}</span></div>
              <div class="result-item"><label>风险等级</label><span :class="['risk-badge', monitorResult.risk_level]">{{ monitorResult.risk_level }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'auto'" class="tab-content">
          <h4>自动调整参数</h4>
          <div class="form-row">
            <div class="form-group half"><label>调整策略</label>
              <select v-model="autoAdjustForm.strategy"><option value="gradient">梯度优化</option><option value="bayesian">贝叶斯优化</option><option value="evolutionary">进化策略</option></select>
            </div>
            <div class="form-group half"><label>最大迭代次数</label><input type="number" v-model.number="autoAdjustForm.max_iterations" min="1" max="100"></div>
          </div>
          <div class="form-row">
            <div class="form-group half"><label>学习率</label><input type="number" v-model.number="autoAdjustForm.learning_rate" min="0.001" max="1" step="0.001"></div>
            <div class="form-group half"><label>收敛阈值</label><input type="number" v-model.number="autoAdjustForm.convergence_threshold" min="0.001" max="0.5" step="0.001"></div>
          </div>
          <div class="form-actions"><button @click="autoAdjust" class="btn btn-primary">执行自动调整</button></div>
          <div v-if="autoAdjustResult" class="result-section">
            <h4>调整结果</h4>
            <div class="result-grid">
              <div class="result-item"><label>调整前评分</label><span>{{ autoAdjustResult.before_score }}</span></div>
              <div class="result-item"><label>调整后评分</label><span>{{ autoAdjustResult.after_score }}</span></div>
              <div class="result-item"><label>迭代次数</label><span>{{ autoAdjustResult.iterations }}</span></div>
              <div class="result-item"><label>改善幅度</label><span>{{ autoAdjustResult.improvement }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'manual'" class="tab-content">
          <h4>手动调整参数</h4>
          <div class="form-row">
            <div class="form-group third"><label>地形</label>
              <select v-model="manualForm.terrain"><option v-for="o in terrainOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
            </div>
            <div class="form-group third"><label>气象</label>
              <select v-model="manualForm.weather"><option v-for="o in weatherOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
            </div>
            <div class="form-group third"><label>奖励值</label><input type="number" v-model.number="manualForm.reward_value" min="1" max="100"></div>
          </div>
          <div class="form-group"><label>调整原因</label><textarea v-model="manualForm.reason" rows="3" placeholder="请输入调整原因"></textarea></div>
          <div class="form-actions"><button @click="manualAdjust" class="btn btn-primary">执行手动调整</button></div>
          <div v-if="manualResult" class="result-section"><h4>调整结果</h4><p>{{ manualResult.message }}</p></div>
        </div>
        <div v-if="activeTab === 'history'" class="tab-content">
          <h4>调整历史</h4>
          <table class="data-table">
            <thead><tr><th>时间</th><th>类型</th><th>调整内容</th><th>结果</th></tr></thead>
            <tbody>
              <tr v-for="h in adjustHistory" :key="h.id"><td>{{ h.time }}</td><td>{{ h.type }}</td><td>{{ h.content }}</td><td><span :class="['status-badge', h.result]">{{ h.result }}</span></td></tr>
            </tbody>
          </table>
        </div>
        <div v-if="activeTab === 'visualization'" class="tab-content">
          <h4>性能对比</h4>
          <div ref="comparisonChart" style="width:100%;height:400px;"></div>
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
      selectedEnvId: '',
      selectedEnvironment: null,
      activeTab: 'monitor',
      environments: [
        { id: 1, env_name: '城市飞行测试', env_id: 'ENV-001', project_id: 1, status: 'running' },
        { id: 2, env_name: '山地风暴测试', env_id: 'ENV-002', project_id: 2, status: 'optimized' },
        { id: 3, env_name: '森林避障训练', env_id: 'ENV-003', project_id: 1, status: 'adjusted' },
        { id: 4, env_name: '丘陵导航环境', env_id: 'ENV-004', project_id: 3, status: 'created' }
      ],
      projects: [{ id: 1, project_name: '无人机避障训练' }, { id: 2, project_name: '固定翼导航测试' }, { id: 3, project_name: '旋翼控制优化' }],
      monitorData: { reward_value: 15, success_rate: 0.72, convergence_speed: 0.65, generalization_score: 0.58 },
      monitorResult: null,
      autoAdjustForm: { strategy: 'gradient', max_iterations: 50, learning_rate: 0.01, convergence_threshold: 0.01 },
      autoAdjustResult: null,
      manualForm: { terrain: 'flat', weather: 'clear', reward_value: 10, reason: '' },
      manualResult: null,
      terrainOptions: [{ value: 'flat', label: '平坦地形' }, { value: 'hilly', label: '丘陵地形' }, { value: 'mountainous', label: '山地地形' }, { value: 'urban', label: '城市地形' }],
      weatherOptions: [{ value: 'clear', label: '晴朗' }, { value: 'windy', label: '有风' }, { value: 'light_rain', label: '小雨' }, { value: 'storm', label: '风暴' }],
      adjustHistory: [
        { id: 1, time: '2026-04-22 15:00', type: '自动调整', content: '梯度优化-迭代30次', result: 'success' },
        { id: 2, time: '2026-04-22 13:15', type: '手动调整', content: '气象:晴朗→有风', result: 'success' },
        { id: 3, time: '2026-04-21 16:30', type: '自动调整', content: '贝叶斯优化-迭代20次', result: 'success' }
      ],
      chartInstance: null,
      gaugeInstances: []
    }
  },
  beforeUnmount() {
    if (this.chartInstance) this.chartInstance.dispose()
    this.gaugeInstances.forEach(g => g.dispose())
  },
  methods: {
    statusLabel(s) { return { created: '已创建', running: '运行中', adjusted: '已调整', optimized: '已优化' }[s] || s },
    getProjectName(pid) { return this.projects.find(p => p.id === pid)?.project_name || '-' },
    loadEnvironment() {
      this.selectedEnvironment = this.environments.find(e => e.id === this.selectedEnvId) || null
      this.monitorResult = null; this.autoAdjustResult = null; this.manualResult = null
      if (this.selectedEnvironment) this.$nextTick(() => this.renderGauges())
    },
    renderGauges() {
      this.gaugeInstances.forEach(g => g.dispose())
      this.gaugeInstances = []
      const refs = [this.$refs.rewardGauge, this.$refs.successGauge, this.$refs.convergenceGauge, this.$refs.generalGauge]
      const values = [this.monitorData.reward_value, this.monitorData.success_rate * 100, this.monitorData.convergence_speed * 100, this.monitorData.generalization_score * 100]
      const colors = ['#1a237e', '#2e7d32', '#e65100', '#7b1fa2']
      refs.forEach((ref, i) => {
        if (!ref) return
        const chart = echarts.init(ref)
        chart.setOption({
          series: [{ type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: i === 0 ? 100 : 100, detail: { formatter: i === 0 ? '{value}' : '{value}%', fontSize: 16 }, data: [{ value: values[i].toFixed(1) }], axisLine: { lineStyle: { width: 10, color: [[0.3, '#f44336'], [0.7, '#FF9800'], [1, colors[i]]] } }, pointer: { width: 4 } }]
        })
        this.gaugeInstances.push(chart)
      })
    },
    monitorPerformance() {
      this.monitorData = { reward_value: Math.round(Math.random() * 30 + 10), success_rate: Math.random() * 0.5 + 0.3, convergence_speed: Math.random() * 0.5 + 0.3, generalization_score: Math.random() * 0.5 + 0.3 }
      this.monitorResult = { overall_score: (Math.random() * 40 + 60).toFixed(1), suggestion: this.monitorData.success_rate < 0.5 ? '建议调整奖励函数' : '环境表现良好', risk_level: this.monitorData.success_rate < 0.5 ? 'high' : 'low' }
      this.$nextTick(() => this.renderGauges())
    },
    autoAdjust() {
      const before = (Math.random() * 30 + 50).toFixed(1)
      const after = (parseFloat(before) + Math.random() * 15 + 5).toFixed(1)
      this.autoAdjustResult = { before_score: before, after_score: after, iterations: Math.floor(Math.random() * 30 + 10), improvement: '+' + (after - before).toFixed(1) }
    },
    manualAdjust() {
      this.manualResult = { message: '手动调整成功！环境参数已更新。（前端演示，无后端）' }
    },
    renderComparisonChart() {
      if (!this.$refs.comparisonChart) return
      if (this.chartInstance) this.chartInstance.dispose()
      this.chartInstance = echarts.init(this.$refs.comparisonChart)
      this.chartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['调整前', '调整后'] },
        radar: {
          indicator: [{ name: '奖励值', max: 100 }, { name: '成功率', max: 100 }, { name: '收敛速度', max: 100 }, { name: '泛化能力', max: 100 }, { name: '稳定性', max: 100 }],
          center: ['50%', '55%'], radius: '65%'
        },
        series: [{
          type: 'radar',
          data: [
            { name: '调整前', value: [45, 55, 50, 40, 60], itemStyle: { color: '#FF9800' }, areaStyle: { opacity: 0.2 } },
            { name: '调整后', value: [72, 78, 65, 58, 75], itemStyle: { color: '#1a237e' }, areaStyle: { opacity: 0.2 } }
          ]
        }]
      })
    }
  },
  watch: {
    activeTab(val) { if (val === 'visualization') this.$nextTick(() => this.renderComparisonChart()) }
  }
}
</script>

<style scoped>
.env-adjust { max-width: 1000px; margin: 0 auto; padding: 24px; }
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
.status-badge.failed { background: #ffebee; color: #c62828; }
.risk-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.risk-badge.high { background: #ffebee; color: #c62828; }
.risk-badge.low { background: #e8f5e9; color: #2e7d32; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tab-button { padding: 8px 16px; border: none; background: #e0e0e0; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 0.85rem; }
.tab-button.active { background: #1a237e; color: white; }
.tab-content { background: #fafafa; border-radius: 8px; padding: 20px; }
.monitor-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.monitor-card { background: white; border-radius: 8px; padding: 14px; text-align: center; }
.monitor-card h4 { color: #666; font-size: 0.85rem; margin-bottom: 4px; }
.monitor-value { font-size: 1.5rem; font-weight: 700; color: #1a237e; }
.monitor-actions { margin-bottom: 16px; }
.result-section, .monitor-result { margin-top: 16px; padding: 16px; background: white; border-radius: 8px; }
.result-section h4, .monitor-result h4 { color: #1a237e; margin-bottom: 10px; }
.result-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.result-item label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 2px; }
.form-row { display: flex; gap: 16px; }
.form-group { margin-bottom: 16px; }
.form-group.half { flex: 1; }
.form-group.third { flex: 1; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #3f51b5; }
.form-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background: #f5f5f5; font-weight: 600; font-size: 0.85rem; }
</style>
