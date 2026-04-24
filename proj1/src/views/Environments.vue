<template>
  <div class="environments">
    <div class="environments-header">
      <h2>环境管理</h2>
      <div class="header-actions">
        <select v-model="selectedStatus" class="filter-select">
          <option value="">所有状态</option>
          <option value="created">已创建</option><option value="running">运行中</option>
          <option value="adjusted">已调整</option><option value="optimized">已优化</option>
        </select>
      </div>
    </div>
    <div class="env-cards">
      <div v-for="env in filteredEnvs" :key="env.id" class="env-card">
        <div class="env-card-header"><h4>{{ env.env_name }}</h4><span :class="['status-badge', env.status]">{{ statusLabel(env.status) }}</span></div>
        <div class="env-card-body">
          <div class="env-info-row"><label>环境ID</label><code>{{ env.env_id }}</code></div>
          <div class="env-info-row"><label>所属项目</label><span>{{ env.project_name }}</span></div>
          <div class="env-info-row"><label>创建时间</label><span>{{ env.created_at }}</span></div>
          <div class="env-preview">
            <div class="preview-tags">
              <span class="preview-tag">{{ env.terrain }}</span>
              <span class="preview-tag">{{ env.weather }}</span>
              <span class="preview-tag">{{ env.obstacle_count }}个障碍物</span>
            </div>
            <div class="complexity-bar-wrap">
              <label>复杂度</label>
              <div class="complexity-bar"><div class="complexity-fill" :style="{ width: (env.complexity * 100) + '%' }"></div></div>
              <span class="complexity-value">{{ (env.complexity * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
        <div class="env-card-actions">
          <button @click="viewEnv(env)" class="btn btn-info">查看</button>
          <button @click="$router.push('/env-adjust?env_id=' + env.id)" class="btn btn-adjust">调整</button>
          <button @click="$router.push('/env-optimize?env_id=' + env.id)" class="btn btn-optimize">优化</button>
          <button @click="deleteEnv(env.id)" class="btn btn-danger">删除</button>
        </div>
      </div>
    </div>
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>环境详情</h3><button @click="showViewModal = false" class="close-btn">&times;</button></div>
        <div class="modal-body" v-if="selectedEnv">
          <div class="detail-grid">
            <div class="detail-item"><label>环境名称</label><span>{{ selectedEnv.env_name }}</span></div>
            <div class="detail-item"><label>环境ID</label><code>{{ selectedEnv.env_id }}</code></div>
            <div class="detail-item"><label>所属项目</label><span>{{ selectedEnv.project_name }}</span></div>
            <div class="detail-item"><label>状态</label><span :class="['status-badge', selectedEnv.status]">{{ statusLabel(selectedEnv.status) }}</span></div>
            <div class="detail-item"><label>地形</label><span>{{ selectedEnv.terrain }}</span></div>
            <div class="detail-item"><label>气象</label><span>{{ selectedEnv.weather }}</span></div>
          </div>
          <div class="detail-config"><h4>环境配置</h4><pre>{{ JSON.stringify(selectedEnv.config, null, 2) }}</pre></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Environments',
  data() {
    return {
      selectedStatus: '',
      showViewModal: false,
      selectedEnv: null,
      environments: [
        { id: 1, env_name: '城市飞行测试', env_id: 'ENV-001', project_name: '无人机避障训练', status: 'running', terrain: '城市地形', weather: '晴朗', obstacle_count: 5, complexity: 0.75, created_at: '2026-04-22 14:30', config: { scenario: { terrain: 'urban', weather: 'clear', obstacles: ['building', 'lamp_post'] }, physics: { flight_dynamics: 'advanced', aerodynamics: 'detailed' }, reward: { reward_value: 15, penalty_rules: ['collision', 'out_of_bounds'] } } },
        { id: 2, env_name: '山地风暴测试', env_id: 'ENV-002', project_name: '固定翼导航测试', status: 'optimized', terrain: '山地地形', weather: '风暴', obstacle_count: 3, complexity: 0.9, created_at: '2026-04-21 16:00', config: { scenario: { terrain: 'mountainous', weather: 'storm', obstacles: ['bird', 'power_line'] }, physics: { flight_dynamics: 'advanced', aerodynamics: 'precise' }, reward: { reward_value: 20, penalty_rules: ['collision', 'fault'] } } },
        { id: 3, env_name: '森林避障训练', env_id: 'ENV-003', project_name: '无人机避障训练', status: 'adjusted', terrain: '森林地形', weather: '小雨', obstacle_count: 4, complexity: 0.6, created_at: '2026-04-21 11:20', config: { scenario: { terrain: 'forest', weather: 'light_rain', obstacles: ['tree', 'bird'] }, physics: { flight_dynamics: 'medium', aerodynamics: 'medium' }, reward: { reward_value: 10, penalty_rules: ['collision', 'timeout'] } } },
        { id: 4, env_name: '丘陵导航环境', env_id: 'ENV-004', project_name: '旋翼控制优化', status: 'created', terrain: '丘陵地形', weather: '有风', obstacle_count: 2, complexity: 0.45, created_at: '2026-04-20 09:15', config: { scenario: { terrain: 'hilly', weather: 'windy', obstacles: ['wind_turbine'] }, physics: { flight_dynamics: 'basic', aerodynamics: 'basic' }, reward: { reward_value: 8, penalty_rules: ['out_of_bounds'] } } }
      ]
    }
  },
  computed: {
    filteredEnvs() {
      if (!this.selectedStatus) return this.environments
      return this.environments.filter(e => e.status === this.selectedStatus)
    }
  },
  methods: {
    statusLabel(s) { return { created: '已创建', running: '运行中', adjusted: '已调整', optimized: '已优化', completed: '已完成', failed: '失败' }[s] || s },
    viewEnv(env) { this.selectedEnv = env; this.showViewModal = true },
    deleteEnv(id) { if (confirm('确定要删除这个环境吗？')) this.environments = this.environments.filter(e => e.id !== id) }
  }
}
</script>

<style scoped>
.environments { max-width: 1200px; margin: 0 auto; padding: 24px; }
.environments-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.environments-header h2 { color: #1a237e; font-size: 1.5rem; }
.filter-select { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.env-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.env-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.env-card-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f0f0f0; }
.env-card-header h4 { color: #1a237e; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.status-badge.created { background: #e3f2fd; color: #1565c0; }
.status-badge.running { background: #e8f5e9; color: #2e7d32; }
.status-badge.adjusted { background: #f3e5f5; color: #7b1fa2; }
.status-badge.optimized { background: #e0f7fa; color: #00838f; }
.env-card-body { padding: 16px 20px; }
.env-info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 0.85rem; }
.env-info-row label { color: #666; }
.env-preview { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.preview-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.preview-tag { background: #f5f5f5; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; color: #555; }
.complexity-bar-wrap { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; }
.complexity-bar { flex: 1; height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; }
.complexity-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #FF9800, #f44336); border-radius: 3px; }
.complexity-value { font-weight: 600; color: #333; }
.env-card-actions { display: flex; gap: 6px; padding: 12px 20px; border-top: 1px solid #f0f0f0; }
.btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: all 0.2s; }
.btn-info { background: #1976d2; color: white; }
.btn-adjust { background: #7B1FA2; color: white; }
.btn-optimize { background: #0097A7; color: white; }
.btn-danger { background: #d32f2f; color: white; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; border-radius: 12px; width: 100%; max-width: 600px; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
.modal-body { padding: 24px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.detail-item label { display: block; font-size: 0.8rem; color: #666; margin-bottom: 2px; }
.detail-config pre { background: #f5f5f5; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; }
code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; color: #1a237e; }
</style>
