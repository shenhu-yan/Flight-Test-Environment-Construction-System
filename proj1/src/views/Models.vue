<template>
  <div class="models">
    <div class="models-header">
      <h2>模型管理</h2>
      <button @click="openUploadModal" class="btn btn-primary">上传模型</button>
    </div>
    <div class="filter-section">
      <select v-model="selectedType" class="filter-select">
        <option value="">所有类型</option>
        <option value="scenario">场景模型</option>
        <option value="physics">物理模型</option>
        <option value="algorithm">算法模型</option>
      </select>
    </div>
    <div class="table-container">
      <table class="data-table">
        <thead><tr><th>模型名称</th><th>模型ID</th><th>类型</th><th>版本</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="model in filteredModels" :key="model.id">
            <td>{{ model.model_name }}</td>
            <td>{{ model.model_id }}</td>
            <td>{{ typeLabel(model.model_type) }}</td>
            <td>{{ model.version }}</td>
            <td><span :class="['status-badge', model.status]">{{ model.status }}</span></td>
            <td class="actions">
              <button @click="alert('下载功能需要后端支持')" class="btn btn-sm btn-info">下载</button>
              <button @click="deleteModel(model.id)" class="btn btn-sm btn-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>上传模型</h3><button @click="showUploadModal = false" class="close-btn">&times;</button></div>
        <form @submit.prevent="uploadModel">
          <div class="form-group"><label>模型名称</label><input type="text" v-model="uploadForm.model_name" required></div>
          <div class="form-group"><label>模型类型</label>
            <select v-model="uploadForm.model_type"><option value="scenario">场景模型</option><option value="physics">物理模型</option><option value="algorithm">算法模型</option></select>
          </div>
          <div class="form-group"><label>版本</label><input type="text" v-model="uploadForm.version" placeholder="1.0.0"></div>
          <div class="form-group"><label>描述</label><textarea v-model="uploadForm.description" rows="3"></textarea></div>
          <div class="form-group"><label>模型文件</label><input type="file"></div>
          <div class="modal-footer"><button type="button" @click="showUploadModal = false" class="btn btn-secondary">取消</button><button type="submit" class="btn btn-primary">上传</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Models',
  data() {
    return {
      selectedType: '',
      showUploadModal: false,
      uploadForm: { model_name: '', model_type: 'scenario', version: '1.0.0', description: '' },
      models: [
        { id: 1, model_name: 'DQN避障模型', model_id: 'MOD-001', model_type: 'algorithm', version: '2.0', status: 'active' },
        { id: 2, model_name: '城市场景生成器', model_id: 'MOD-002', model_type: 'scenario', version: '1.5', status: 'active' },
        { id: 3, model_name: '风场物理模型', model_id: 'MOD-003', model_type: 'physics', version: '1.2', status: 'active' },
        { id: 4, model_name: 'PPO导航模型', model_id: 'MOD-004', model_type: 'algorithm', version: '1.0', status: 'draft' },
        { id: 5, model_name: '山地场景生成器', model_id: 'MOD-005', model_type: 'scenario', version: '1.0', status: 'active' }
      ]
    }
  },
  computed: {
    filteredModels() { if (!this.selectedType) return this.models; return this.models.filter(m => m.model_type === this.selectedType) }
  },
  methods: {
    typeLabel(t) { return { scenario: '场景模型', physics: '物理模型', algorithm: '算法模型' }[t] || t },
    openUploadModal() { this.uploadForm = { model_name: '', model_type: 'scenario', version: '1.0.0', description: '' }; this.showUploadModal = true },
    uploadModel() {
      this.models.push({ id: Date.now(), model_name: this.uploadForm.model_name, model_id: 'MOD-' + String(this.models.length + 1).padStart(3, '0'), model_type: this.uploadForm.model_type, version: this.uploadForm.version, status: 'draft' })
      this.showUploadModal = false
    },
    deleteModel(id) { if (confirm('确定要删除这个模型吗？')) this.models = this.models.filter(m => m.id !== id) }
  }
}
</script>

<style scoped>
.models { max-width: 1200px; margin: 0 auto; padding: 24px; }
.models-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.models-header h2 { color: #1a237e; font-size: 1.5rem; }
.filter-section { margin-bottom: 16px; }
.filter-select { padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-sm { padding: 4px 10px; font-size: 0.8rem; }
.btn-info { background: #1976d2; color: white; }
.btn-danger { background: #d32f2f; color: white; }
.table-container { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background: #fafafa; font-weight: 600; font-size: 0.85rem; }
.data-table tr:hover { background: #f8f9ff; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
.status-badge.active { background: #e8f5e9; color: #2e7d32; }
.status-badge.draft { background: #fff3e0; color: #e65100; }
.actions { display: flex; gap: 8px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; border-radius: 12px; width: 100%; max-width: 480px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
form { padding: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #3f51b5; }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
</style>
