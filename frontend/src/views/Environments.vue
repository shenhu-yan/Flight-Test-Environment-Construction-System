<template>
  <div class="environments">
    <div class="environments-header">
      <h2>环境管理</h2>
      <div class="header-actions">
        <select v-model.number="selectedProject" @change="loadEnvironments" class="filter-select">
          <option value="">所有项目</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.project_name }}
          </option>
        </select>
        <select v-model="selectedStatus" @change="loadEnvironments" class="filter-select">
          <option value="">所有状态</option>
          <option value="created">已创建</option>
          <option value="running">运行中</option>
          <option value="adjusted">已调整</option>
          <option value="optimized">已优化</option>
          <option value="completed">已完成</option>
        </select>
      </div>
    </div>

    <div class="environments-list">
      <div v-if="environments.length === 0" class="empty-state">
        <p>暂无环境数据</p>
      </div>
      <div v-else class="env-cards">
        <div v-for="env in environments" :key="env.id" class="env-card">
          <div class="env-card-header">
            <h4>{{ env.env_name }}</h4>
            <span :class="['status-badge', env.status]">{{ statusLabel(env.status) }}</span>
          </div>
          <div class="env-card-body">
            <div class="env-info-row">
              <label>环境ID</label>
              <code>{{ env.env_id }}</code>
            </div>
            <div class="env-info-row">
              <label>所属项目</label>
              <span>{{ getProjectName(env.project_id) }}</span>
            </div>
            <div class="env-info-row">
              <label>创建时间</label>
              <span>{{ formatDate(env.created_at) }}</span>
            </div>

            <div v-if="env.preview_data" class="env-preview">
              <h5>环境预览</h5>
              <div class="preview-tags">
                <span v-if="env.preview_data.summary" class="preview-tag">{{ env.preview_data.summary.terrain }}</span>
                <span v-if="env.preview_data.summary" class="preview-tag">{{ env.preview_data.summary.weather }}</span>
                <span v-if="env.preview_data.summary" class="preview-tag">{{ env.preview_data.summary.obstacle_count }}个障碍物</span>
              </div>
              <div v-if="env.preview_data.complexity_score" class="complexity-bar-wrap">
                <label>复杂度</label>
                <div class="complexity-bar">
                  <div class="complexity-fill" :style="{ width: (env.preview_data.complexity_score * 100) + '%' }"></div>
                </div>
                <span class="complexity-value">{{ (env.preview_data.complexity_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
          <div class="env-card-actions">
            <button @click="viewEnvironment(env)" class="btn btn-info">查看</button>
            <button @click="previewEnvironment(env)" class="btn btn-preview">预览</button>
            <button @click="adjustEnvironment(env)" class="btn btn-adjust">调整</button>
            <button @click="optimizeEnvironment(env)" class="btn btn-optimize">优化</button>
            <button @click="exportEnvironment(env)" class="btn btn-export">导出</button>
            <button @click="deleteEnvironment(env.id)" class="btn btn-danger">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>环境详情</h3>
          <button @click="showViewModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body" v-if="selectedEnvironment">
          <div class="detail-grid">
            <div class="detail-item">
              <label>环境名称</label>
              <span>{{ selectedEnvironment.env_name }}</span>
            </div>
            <div class="detail-item">
              <label>环境ID</label>
              <code>{{ selectedEnvironment.env_id }}</code>
            </div>
            <div class="detail-item">
              <label>所属项目</label>
              <span>{{ getProjectName(selectedEnvironment.project_id) }}</span>
            </div>
            <div class="detail-item">
              <label>描述格式</label>
              <span>{{ selectedEnvironment.desc_format?.toUpperCase() || 'JSON' }}</span>
            </div>
            <div class="detail-item">
              <label>当前状态</label>
              <span :class="['status-badge', selectedEnvironment.status]">{{ statusLabel(selectedEnvironment.status) }}</span>
            </div>
            <div class="detail-item">
              <label>创建时间</label>
              <span>{{ formatDate(selectedEnvironment.created_at) }}</span>
            </div>
            <div class="detail-item">
              <label>更新时间</label>
              <span>{{ formatDate(selectedEnvironment.updated_at) }}</span>
            </div>
          </div>

          <div v-if="selectedEnvironment.preview_data" class="detail-preview">
            <h4>环境预览</h4>
            <div class="preview-detail-grid">
              <div class="preview-detail-card">
                <h5>场景概要</h5>
                <div class="preview-item"><label>地形:</label><span>{{ selectedEnvironment.preview_data.summary?.terrain || '-' }}</span></div>
                <div class="preview-item"><label>气象:</label><span>{{ selectedEnvironment.preview_data.summary?.weather || '-' }}</span></div>
                <div class="preview-item"><label>障碍物数量:</label><span>{{ selectedEnvironment.preview_data.summary?.obstacle_count || 0 }}</span></div>
                <div class="preview-item"><label>障碍物:</label><span>{{ selectedEnvironment.preview_data.summary?.obstacle_names?.join(', ') || '无' }}</span></div>
              </div>
              <div class="preview-detail-card">
                <h5>物理模型</h5>
                <div class="preview-item"><label>飞行力学:</label><span>{{ selectedEnvironment.preview_data.summary?.flight_dynamics || '-' }}</span></div>
                <div class="preview-item"><label>空气动力学:</label><span>{{ selectedEnvironment.preview_data.summary?.aerodynamics || '-' }}</span></div>
              </div>
              <div class="preview-detail-card">
                <h5>奖励机制</h5>
                <div class="preview-item"><label>奖励值:</label><span>{{ selectedEnvironment.preview_data.summary?.reward_value || '-' }}</span></div>
                <div class="preview-item"><label>惩罚规则数:</label><span>{{ selectedEnvironment.preview_data.summary?.penalty_count || 0 }}</span></div>
                <div class="preview-item"><label>目标阈值:</label><span>{{ selectedEnvironment.preview_data.summary?.target_threshold || '-' }}</span></div>
              </div>
            </div>
            <div v-if="selectedEnvironment.preview_data.scene_description" class="scene-desc">
              <h5>场景描述</h5>
              <p>{{ selectedEnvironment.preview_data.scene_description }}</p>
            </div>
          </div>

          <div class="detail-config">
            <h4>环境配置</h4>
            <pre>{{ JSON.stringify(selectedEnvironment.config, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPreviewModal" class="modal-overlay" @click.self="showPreviewModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>环境预览 - {{ previewEnv?.env_name }}</h3>
          <button @click="showPreviewModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body" v-if="previewData">
          <div class="preview-grid-full">
            <div class="preview-card">
              <h5>场景概要</h5>
              <div class="preview-item"><label>地形:</label><span>{{ previewData.summary?.terrain || '-' }}</span></div>
              <div class="preview-item"><label>气象:</label><span>{{ previewData.summary?.weather || '-' }}</span></div>
              <div class="preview-item"><label>障碍物数量:</label><span>{{ previewData.summary?.obstacle_count || 0 }}</span></div>
              <div class="preview-item"><label>障碍物:</label><span>{{ previewData.summary?.obstacle_names?.join(', ') || '无' }}</span></div>
            </div>
            <div class="preview-card">
              <h5>物理模型</h5>
              <div class="preview-item"><label>飞行力学:</label><span>{{ previewData.summary?.flight_dynamics || '-' }}</span></div>
              <div class="preview-item"><label>空气动力学:</label><span>{{ previewData.summary?.aerodynamics || '-' }}</span></div>
            </div>
            <div class="preview-card">
              <h5>奖励机制</h5>
              <div class="preview-item"><label>奖励值:</label><span>{{ previewData.summary?.reward_value || '-' }}</span></div>
              <div class="preview-item"><label>惩罚规则数:</label><span>{{ previewData.summary?.penalty_count || 0 }}</span></div>
              <div class="preview-item"><label>目标阈值:</label><span>{{ previewData.summary?.target_threshold || '-' }}</span></div>
            </div>
            <div class="preview-card highlight">
              <h5>复杂度评估</h5>
              <div class="complexity-bar-wrap">
                <div class="complexity-bar">
                  <div class="complexity-fill" :style="{ width: (previewData.complexity_score * 100) + '%' }"></div>
                </div>
                <span class="complexity-value">{{ (previewData.complexity_score * 100).toFixed(0) }}%</span>
              </div>
              <p class="scene-desc">{{ previewData.scene_description }}</p>
            </div>
          </div>
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
      environments: [],
      projects: [],
      selectedProject: '',
      selectedStatus: '',
      showViewModal: false,
      showPreviewModal: false,
      selectedEnvironment: null,
      previewEnv: null,
      previewData: null
    }
  },
  mounted() {
    this.loadProjects()
    this.loadEnvironments()
  },
  methods: {
    async loadProjects() {
      try {
        const response = await this.$axios.get('/projects')
        this.projects = response.data
      } catch (error) {
        console.error('加载项目失败:', error)
      }
    },
    async loadEnvironments() {
      try {
        let url = '/environments'
        const params = []
        if (this.selectedProject) params.push(`project_id=${this.selectedProject}`)
        if (this.selectedStatus) params.push(`status=${this.selectedStatus}`)
        if (params.length > 0) url += '?' + params.join('&')
        const response = await this.$axios.get(url)
        this.environments = response.data
      } catch (error) {
        console.error('加载环境失败:', error)
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
    viewEnvironment(env) {
      this.selectedEnvironment = env
      this.showViewModal = true
    },
    async previewEnvironment(env) {
      this.previewEnv = env
      try {
        const response = await this.$axios.get(`/environments/${env.id}/preview`)
        this.previewData = response.data.preview
        this.showPreviewModal = true
      } catch (error) {
        console.error('加载预览失败:', error)
        if (env.preview_data) {
          this.previewData = env.preview_data
          this.showPreviewModal = true
        } else {
          alert('预览数据不可用')
        }
      }
    },
    adjustEnvironment(env) {
      this.$router.push(`/env-adjust?env_id=${env.id}`)
    },
    optimizeEnvironment(env) {
      this.$router.push(`/env-optimize?env_id=${env.id}`)
    },
    async exportEnvironment(env) {
      try {
        const token = localStorage.getItem('token')
        const url = `/api/env/export/${env.env_id}?format=json`
        const xhr = new XMLHttpRequest()
        xhr.open('GET', url, true)
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        xhr.responseType = 'blob'
        xhr.onload = () => {
          if (xhr.status === 200) {
            const blob = xhr.response
            const downloadUrl = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = `${env.env_name}_${env.env_id}.json`
            link.click()
            window.URL.revokeObjectURL(downloadUrl)
          } else {
            alert('导出失败')
          }
        }
        xhr.send()
      } catch (error) {
        console.error('导出环境失败:', error)
        alert('导出环境失败')
      }
    },
    async deleteEnvironment(envId) {
      if (confirm('确定要删除这个环境吗？此操作不可恢复')) {
        try {
          await this.$axios.delete(`/environments/${envId}`)
          this.loadEnvironments()
        } catch (error) {
          console.error('删除环境失败:', error)
          alert(error.response?.data?.error || '删除环境失败')
        }
      }
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
.environments { max-width: 1200px; margin: 0 auto; padding: 24px; }
.environments-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.environments-header h2 { color: #1a237e; font-size: 1.5rem; }
.header-actions { display: flex; gap: 10px; }
.filter-select { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
.filter-select:focus { border-color: #1a237e; outline: none; }

.empty-state { text-align: center; color: #999; padding: 60px 20px; background: white; border-radius: 12px; }

.env-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }
.env-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; }
.env-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.env-card-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f0f0f0; }
.env-card-header h4 { color: #1a237e; font-size: 1rem; margin: 0; }
.env-card-body { padding: 16px 20px; }
.env-info-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9rem; }
.env-info-row label { color: #666; font-weight: 500; }
.env-info-row code { background: #f5f5f5; padding: 1px 6px; border-radius: 4px; font-size: 0.85rem; color: #1a237e; }

.env-preview { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.env-preview h5 { font-size: 0.85rem; color: #888; margin-bottom: 8px; }
.preview-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.preview-tag { background: #e8eaf6; color: #283593; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 500; }
.complexity-bar-wrap { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }
.complexity-bar-wrap label { color: #666; font-weight: 500; }
.complexity-bar { flex: 1; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
.complexity-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #FF9800, #f44336); border-radius: 4px; transition: width 0.3s; }
.complexity-value { font-weight: 600; color: #1a237e; min-width: 36px; }

.env-card-actions { display: flex; gap: 6px; padding: 12px 20px; border-top: 1px solid #f0f0f0; flex-wrap: wrap; }
.btn { padding: 5px 10px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: all 0.2s; }
.btn-info { background-color: #1976d2; color: white; }
.btn-info:hover { background-color: #1565c0; }
.btn-preview { background-color: #7B1FA2; color: white; }
.btn-preview:hover { background-color: #6A1B9A; }
.btn-adjust { background-color: #FF9800; color: white; }
.btn-adjust:hover { background-color: #F57C00; }
.btn-optimize { background-color: #4CAF50; color: white; }
.btn-optimize:hover { background-color: #388E3C; }
.btn-export { background-color: #0097A7; color: white; }
.btn-export:hover { background-color: #00838F; }
.btn-danger { background-color: #d32f2f; color: white; }
.btn-danger:hover { background-color: #b71c1c; }

.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.status-badge.created { background-color: #e3f2fd; color: #1976D2; }
.status-badge.running { background-color: #e8f5e9; color: #388E3C; }
.status-badge.completed { background-color: #fff3e0; color: #F57C00; }
.status-badge.failed { background-color: #ffebee; color: #D32F2F; }
.status-badge.adjusted { background-color: #f3e5f5; color: #7B1FA2; }
.status-badge.optimized { background-color: #e0f7fa; color: #0097A7; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background-color: white; border-radius: 12px; width: 100%; max-width: 800px; max-height: 85vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; background: white; z-index: 1; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
.modal-body { padding: 24px; }

.detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-weight: 600; color: #666; font-size: 0.85rem; }
.detail-item code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; color: #1a237e; }

.detail-preview { margin-bottom: 20px; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.detail-preview h4 { margin-bottom: 12px; color: #1a237e; font-size: 1rem; }
.preview-detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.preview-detail-card { background: white; padding: 12px; border-radius: 8px; }
.preview-detail-card h5 { margin-bottom: 8px; color: #333; font-size: 0.9rem; }
.preview-item { display: flex; justify-content: space-between; padding: 2px 0; font-size: 0.85rem; }
.preview-item label { color: #666; }
.scene-desc { margin-top: 12px; padding: 12px; background: white; border-radius: 8px; }
.scene-desc h5 { margin-bottom: 6px; color: #333; font-size: 0.9rem; }
.scene-desc p { color: #666; font-size: 0.9rem; line-height: 1.5; }

.detail-config { margin-top: 16px; }
.detail-config h4 { margin-bottom: 10px; color: #1a237e; font-size: 1rem; }
.detail-config pre { background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; line-height: 1.5; }

.preview-grid-full { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.preview-card { background: #f8f9ff; padding: 16px; border-radius: 8px; }
.preview-card h5 { margin-bottom: 10px; color: #1a237e; font-size: 0.95rem; }
.preview-card.highlight { border: 2px solid #e8eaf6; }

@media (max-width: 768px) {
  .environments-header { flex-direction: column; align-items: flex-start; }
  .env-cards { grid-template-columns: 1fr; }
  .env-card-actions { justify-content: center; }
  .modal-card { margin: 10px; max-height: 95vh; }
}
</style>
