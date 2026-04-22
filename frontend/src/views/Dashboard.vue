<template>
  <div class="dashboard">
    <h2>系统仪表盘</h2>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #e3f2fd;">📁</div>
        <div class="stat-content">
          <h3>项目数量</h3>
          <p>{{ stats.projects }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #e8f5e9;">🌍</div>
        <div class="stat-content">
          <h3>环境数量</h3>
          <p>{{ stats.environments }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #fff3e0;">🤖</div>
        <div class="stat-content">
          <h3>模型数量</h3>
          <p>{{ stats.models }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background-color: #fce4ec;">📊</div>
        <div class="stat-content">
          <h3>调整次数</h3>
          <p>{{ stats.adjustments }}</p>
        </div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h4>环境状态分布</h4>
        <div ref="statusChart" style="width:100%;height:300px;"></div>
      </div>
      <div class="chart-card">
        <h4>项目环境统计</h4>
        <div ref="projectChart" style="width:100%;height:300px;"></div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card wide">
        <h4>环境操作趋势</h4>
        <div ref="trendChart" style="width:100%;height:300px;"></div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-grid">
        <router-link to="/env-gen" class="action-card">
          <span class="action-icon">🔧</span>
          <span>生成环境</span>
        </router-link>
        <router-link to="/env-adjust" class="action-card">
          <span class="action-icon">⚙</span>
          <span>调整环境</span>
        </router-link>
        <router-link to="/env-optimize" class="action-card">
          <span class="action-icon">📈</span>
          <span>优化环境</span>
        </router-link>
        <router-link to="/models" class="action-card">
          <span class="action-icon">📦</span>
          <span>管理模型</span>
        </router-link>
      </div>
    </div>

    <div class="recent-activities">
      <h3>最近活动</h3>
      <div class="activity-list">
        <div v-if="recentActivities.length === 0" class="empty-tip">暂无活动记录</div>
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-icon-wrap" :style="{ background: activity.color }">
            {{ activity.icon }}
          </div>
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
      stats: {
        projects: 0,
        environments: 0,
        models: 0,
        adjustments: 0
      },
      envList: [],
      projectList: [],
      adjustmentList: [],
      recentActivities: [],
      statusChartInstance: null,
      projectChartInstance: null,
      trendChartInstance: null
    }
  },
  mounted() {
    this.loadStats()
  },
  beforeUnmount() {
    if (this.statusChartInstance) this.statusChartInstance.dispose()
    if (this.projectChartInstance) this.projectChartInstance.dispose()
    if (this.trendChartInstance) this.trendChartInstance.dispose()
  },
  methods: {
    async loadStats() {
      try {
        const [projectsRes, envsRes, modelsRes, adjustmentsRes] = await Promise.allSettled([
          this.$axios.get('/projects'),
          this.$axios.get('/environments'),
          this.$axios.get('/models'),
          this.$axios.get('/adjustments')
        ])
        if (projectsRes.status === 'fulfilled') {
          this.stats.projects = projectsRes.value.data.length || 0
          this.projectList = projectsRes.value.data || []
        }
        if (envsRes.status === 'fulfilled') {
          this.stats.environments = envsRes.value.data.length || 0
          this.envList = envsRes.value.data || []
        }
        if (modelsRes.status === 'fulfilled') {
          this.stats.models = modelsRes.value.data.length || 0
        }
        if (adjustmentsRes.status === 'fulfilled') {
          this.stats.adjustments = adjustmentsRes.value.data.length || 0
          this.adjustmentList = adjustmentsRes.value.data || []
        }

        this.buildRecentActivities()
        this.$nextTick(() => {
          this.renderStatusChart()
          this.renderProjectChart()
          this.renderTrendChart()
        })
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    },
    buildRecentActivities() {
      const activities = []

      this.envList.forEach(env => {
        activities.push({
          id: `env-${env.id}`,
          content: `创建环境「${env.env_name}」`,
          time: this.formatDate(env.created_at),
          icon: '🌍',
          color: '#e8f5e9'
        })
      })

      this.adjustmentList.forEach(adj => {
        activities.push({
          id: `adj-${adj.id}`,
          content: `${adj.trigger === 'auto' ? '自动' : '手动'}调整环境 (ID: ${adj.env_id})`,
          time: this.formatDate(adj.created_at),
          icon: '⚙',
          color: '#fff3e0'
        })
      })

      activities.sort((a, b) => new Date(b.time) - new Date(a.time))
      this.recentActivities = activities.slice(0, 10)
    },
    renderStatusChart() {
      if (!this.$refs.statusChart) return
      this.statusChartInstance = echarts.init(this.$refs.statusChart)

      const statusCount = {}
      const statusLabels = {
        created: '已创建', running: '运行中', adjusted: '已调整',
        optimized: '已优化', completed: '已完成', failed: '失败'
      }
      const statusColors = {
        created: '#1976D2', running: '#388E3C', adjusted: '#7B1FA2',
        optimized: '#0097A7', completed: '#F57C00', failed: '#D32F2F'
      }

      this.envList.forEach(env => {
        statusCount[env.status] = (statusCount[env.status] || 0) + 1
      })

      const data = Object.entries(statusCount).map(([key, value]) => ({
        name: statusLabels[key] || key,
        value,
        itemStyle: { color: statusColors[key] || '#999' }
      }))

      if (data.length === 0) {
        data.push({ name: '暂无数据', value: 1, itemStyle: { color: '#e0e0e0' } })
      }

      this.statusChartInstance.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '55%'],
          data,
          label: { formatter: '{b}\n{c}个' },
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' } }
        }]
      })
    },
    renderProjectChart() {
      if (!this.$refs.projectChart) return
      this.projectChartInstance = echarts.init(this.$refs.projectChart)

      const projectEnvCount = {}
      this.projectList.forEach(p => {
        projectEnvCount[p.project_name] = 0
      })
      this.envList.forEach(env => {
        const project = this.projectList.find(p => p.id === env.project_id)
        if (project) {
          projectEnvCount[project.project_name] = (projectEnvCount[project.project_name] || 0) + 1
        }
      })

      const names = Object.keys(projectEnvCount)
      const values = Object.values(projectEnvCount)

      this.projectChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: names,
          axisLabel: { rotate: names.length > 4 ? 30 : 0, fontSize: 12 }
        },
        yAxis: { type: 'value', name: '环境数量', minInterval: 1 },
        series: [{
          type: 'bar',
          data: values,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#1a237e' },
              { offset: 1, color: '#7986CB' }
            ])
          },
          barWidth: '40%',
          label: { show: true, position: 'top', formatter: '{c}' }
        }]
      })
    },
    renderTrendChart() {
      if (!this.$refs.trendChart) return
      this.trendChartInstance = echarts.init(this.$refs.trendChart)

      const envByDate = {}
      const adjByDate = {}

      this.envList.forEach(env => {
        const date = this.getDateKey(env.created_at)
        envByDate[date] = (envByDate[date] || 0) + 1
      })

      this.adjustmentList.forEach(adj => {
        const date = this.getDateKey(adj.created_at)
        adjByDate[date] = (adjByDate[date] || 0) + 1
      })

      const allDates = new Set([...Object.keys(envByDate), ...Object.keys(adjByDate)])
      const sortedDates = [...allDates].sort()

      const last7 = sortedDates.slice(-7)
      const envCounts = last7.map(d => envByDate[d] || 0)
      const adjCounts = last7.map(d => adjByDate[d] || 0)

      this.trendChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['环境创建', '环境调整'] },
        xAxis: { type: 'category', data: last7 },
        yAxis: { type: 'value', name: '次数', minInterval: 1 },
        series: [
          {
            name: '环境创建',
            type: 'line',
            data: envCounts,
            smooth: true,
            itemStyle: { color: '#1a237e' },
            areaStyle: { color: 'rgba(26,35,126,0.1)' }
          },
          {
            name: '环境调整',
            type: 'line',
            data: adjCounts,
            smooth: true,
            itemStyle: { color: '#FF9800' },
            areaStyle: { color: 'rgba(255,152,0,0.1)' }
          }
        ]
      })
    },
    getDateKey(dateStr) {
      if (!dateStr) return '未知'
      const d = new Date(dateStr)
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; margin: 0 auto; padding: 24px; }
.dashboard h2 { margin-bottom: 24px; color: #1a237e; font-size: 1.5rem; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); display: flex; align-items: center; gap: 16px; transition: transform 0.2s, box-shadow 0.2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.stat-icon { font-size: 1.8rem; width: 56px; height: 56px; display: flex; justify-content: center; align-items: center; border-radius: 12px; }
.stat-content h3 { color: #666; font-size: 0.85rem; margin-bottom: 4px; font-weight: 500; }
.stat-content p { color: #1a237e; font-size: 1.8rem; font-weight: 700; }

.charts-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.chart-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-card.wide { grid-column: 1 / -1; }
.chart-card h4 { margin-bottom: 12px; color: #1a237e; font-size: 1rem; }

.quick-actions { margin-bottom: 24px; }
.quick-actions h3 { margin-bottom: 16px; color: #333; font-size: 1.1rem; }
.action-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
.action-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 20px; background-color: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-decoration: none; color: #333; transition: all 0.2s; font-weight: 500; }
.action-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); color: #1a237e; }
.action-icon { font-size: 2rem; }

.recent-activities { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.recent-activities h3 { margin-bottom: 16px; color: #333; font-size: 1.1rem; }
.empty-tip { text-align: center; color: #999; padding: 20px; }
.activity-list { display: flex; flex-direction: column; }
.activity-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; }
.activity-item:last-child { border-bottom: none; }
.activity-icon-wrap { width: 36px; height: 36px; border-radius: 10px; display: flex; justify-content: center; align-items: center; font-size: 1rem; flex-shrink: 0; }
.activity-content { display: flex; justify-content: space-between; align-items: center; flex: 1; min-width: 0; }
.activity-text { color: #333; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.activity-time { color: #999; font-size: 0.8rem; flex-shrink: 0; margin-left: 12px; }

@media (max-width: 768px) {
  .dashboard { padding: 16px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .action-grid { grid-template-columns: repeat(2, 1fr); }
  .activity-content { flex-direction: column; align-items: flex-start; gap: 2px; }
  .activity-time { margin-left: 0; }
}
</style>
