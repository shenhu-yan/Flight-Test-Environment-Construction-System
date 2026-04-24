<template>
  <div class="dashboard">
    <h2>系统仪表盘</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #e3f2fd;">📁</div>
        <div class="stat-content"><h3>项目数量</h3><p>{{ stats.projects }}</p></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #e8f5e9;">🌍</div>
        <div class="stat-content"><h3>环境数量</h3><p>{{ stats.environments }}</p></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #fff3e0;">🤖</div>
        <div class="stat-content"><h3>模型数量</h3><p>{{ stats.models }}</p></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #fce4ec;">📊</div>
        <div class="stat-content"><h3>调整次数</h3><p>{{ stats.adjustments }}</p></div>
      </div>
    </div>
    <div class="charts-row">
      <div class="chart-card"><h4>环境状态分布</h4><div ref="statusChart" style="width:100%;height:300px;"></div></div>
      <div class="chart-card"><h4>项目环境统计</h4><div ref="projectChart" style="width:100%;height:300px;"></div></div>
    </div>
    <div class="charts-row">
      <div class="chart-card wide"><h4>环境操作趋势</h4><div ref="trendChart" style="width:100%;height:300px;"></div></div>
    </div>
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-grid">
        <router-link to="/env-gen" class="action-card"><span class="action-icon">🔧</span><span>生成环境</span></router-link>
        <router-link to="/env-adjust" class="action-card"><span class="action-icon">⚙</span><span>调整环境</span></router-link>
        <router-link to="/env-optimize" class="action-card"><span class="action-icon">📈</span><span>优化环境</span></router-link>
        <router-link to="/models" class="action-card"><span class="action-icon">📦</span><span>管理模型</span></router-link>
      </div>
    </div>
    <div class="recent-activities">
      <h3>最近活动</h3>
      <div class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-icon-wrap" :style="{ background: activity.color }">{{ activity.icon }}</div>
          <div class="activity-content">
            <span class="activity-text">{{ activity.content }}</span>
            <span class="activity-time">{{ activity.time }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'Dashboard',
  data() {
    return {
      stats: { projects: 3, environments: 8, models: 5, adjustments: 12 },
      recentActivities: [
        { id: 1, content: '创建环境「城市飞行测试」', time: '2026-04-22 14:30', icon: '🌍', color: '#e8f5e9' },
        { id: 2, content: '自动调整环境 (ID: ENV-003)', time: '2026-04-22 13:15', icon: '⚙', color: '#fff3e0' },
        { id: 3, content: '优化环境「山地风暴测试」', time: '2026-04-22 11:00', icon: '📈', color: '#e3f2fd' },
        { id: 4, content: '上传模型「DQN-v2」', time: '2026-04-21 16:45', icon: '📦', color: '#fce4ec' },
        { id: 5, content: '创建项目「无人机避障训练」', time: '2026-04-21 10:20', icon: '📁', color: '#e3f2fd' }
      ],
      statusChartInstance: null,
      projectChartInstance: null,
      trendChartInstance: null
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.renderStatusChart()
      this.renderProjectChart()
      this.renderTrendChart()
    })
  },
  beforeUnmount() {
    if (this.statusChartInstance) this.statusChartInstance.dispose()
    if (this.projectChartInstance) this.projectChartInstance.dispose()
    if (this.trendChartInstance) this.trendChartInstance.dispose()
  },
  methods: {
    renderStatusChart() {
      if (!this.$refs.statusChart) return
      this.statusChartInstance = echarts.init(this.$refs.statusChart)
      this.statusChartInstance.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
          data: [
            { name: '已创建', value: 3, itemStyle: { color: '#1976D2' } },
            { name: '运行中', value: 2, itemStyle: { color: '#388E3C' } },
            { name: '已调整', value: 1, itemStyle: { color: '#7B1FA2' } },
            { name: '已优化', value: 2, itemStyle: { color: '#0097A7' } }
          ],
          label: { formatter: '{b}\n{c}个' },
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' } }
        }]
      })
    },
    renderProjectChart() {
      if (!this.$refs.projectChart) return
      this.projectChartInstance = echarts.init(this.$refs.projectChart)
      this.projectChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['无人机避障', '固定翼导航', '旋翼控制'] },
        yAxis: { type: 'value', name: '环境数量', minInterval: 1 },
        series: [{
          type: 'bar', data: [3, 2, 3], barWidth: '40%',
          itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#1a237e' }, { offset: 1, color: '#7986CB' }]) },
          label: { show: true, position: 'top', formatter: '{c}' }
        }]
      })
    },
    renderTrendChart() {
      if (!this.$refs.trendChart) return
      this.trendChartInstance = echarts.init(this.$refs.trendChart)
      this.trendChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['环境创建', '环境调整'] },
        xAxis: { type: 'category', data: ['4/18', '4/19', '4/20', '4/21', '4/22'] },
        yAxis: { type: 'value', name: '次数', minInterval: 1 },
        series: [
          { name: '环境创建', type: 'line', data: [1, 2, 1, 3, 1], smooth: true, itemStyle: { color: '#1a237e' } },
          { name: '环境调整', type: 'line', data: [0, 1, 3, 2, 4], smooth: true, itemStyle: { color: '#FF9800' } }
        ]
      })
    }
  }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; margin: 0 auto; padding: 24px; }
h2 { color: #1a237e; font-size: 1.5rem; margin-bottom: 20px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: white; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.stat-content h3 { font-size: 0.85rem; color: #666; margin-bottom: 4px; }
.stat-content p { font-size: 1.8rem; font-weight: 700; color: #1a237e; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.charts-row .wide { grid-column: 1 / -1; }
.chart-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-card h4 { color: #333; margin-bottom: 12px; font-size: 1rem; }
.quick-actions { margin-bottom: 24px; }
.quick-actions h3 { color: #1a237e; margin-bottom: 12px; }
.action-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.action-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; background: white; border-radius: 12px; text-decoration: none; color: #333; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: transform 0.2s, box-shadow 0.2s; }
.action-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.action-icon { font-size: 2rem; }
.recent-activities h3 { color: #1a237e; margin-bottom: 12px; }
.activity-list { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.activity-item { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid #f0f0f0; }
.activity-item:last-child { border-bottom: none; }
.activity-icon-wrap { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
.activity-content { display: flex; justify-content: space-between; flex: 1; }
.activity-text { color: #333; font-size: 0.9rem; }
.activity-time { color: #999; font-size: 0.8rem; }
@media (max-width: 768px) {
  .stats-grid, .action-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}
</style>
