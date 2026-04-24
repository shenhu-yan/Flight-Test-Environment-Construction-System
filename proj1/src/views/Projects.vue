<template>
  <div class="projects">
    <div class="page-header">
      <h2>项目管理</h2>
      <button @click="openCreateModal" class="btn btn-primary">+ 创建项目</button>
    </div>
    <div class="table-container">
      <table class="data-table">
        <thead><tr><th>项目名称</th><th>项目ID</th><th>描述</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-if="projects.length === 0"><td colspan="5" class="empty-row">暂无项目数据</td></tr>
          <tr v-for="project in projects" :key="project.id">
            <td>{{ project.project_name }}</td>
            <td><code>{{ project.project_id }}</code></td>
            <td>{{ project.description || '-' }}</td>
            <td>{{ project.created_at }}</td>
            <td class="actions">
              <button @click="openEditModal(project)" class="btn btn-sm btn-info">编辑</button>
              <button @click="deleteProject(project.id)" class="btn btn-sm btn-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>创建项目</h3><button @click="showCreateModal = false" class="close-btn">&times;</button></div>
        <form @submit.prevent="createProject">
          <div class="form-group"><label>项目名称</label><input type="text" v-model="newProject.project_name" required></div>
          <div class="form-group"><label>项目ID</label><input type="text" v-model="newProject.project_id" required></div>
          <div class="form-group"><label>描述</label><textarea v-model="newProject.description" rows="3"></textarea></div>
          <div class="modal-footer"><button type="button" @click="showCreateModal = false" class="btn btn-secondary">取消</button><button type="submit" class="btn btn-primary">创建</button></div>
        </form>
      </div>
    </div>
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>编辑项目</h3><button @click="showEditModal = false" class="close-btn">&times;</button></div>
        <form @submit.prevent="updateProject">
          <div class="form-group"><label>项目名称</label><input type="text" v-model="editProject.project_name" required></div>
          <div class="form-group"><label>描述</label><textarea v-model="editProject.description" rows="3"></textarea></div>
          <div class="modal-footer"><button type="button" @click="showEditModal = false" class="btn btn-secondary">取消</button><button type="submit" class="btn btn-primary">更新</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Projects',
  data() {
    return {
      projects: [
        { id: 1, project_name: '无人机避障训练', project_id: 'PROJ-001', description: '基于强化学习的无人机避障飞行训练', created_at: '2026-04-20 10:30' },
        { id: 2, project_name: '固定翼导航测试', project_id: 'PROJ-002', description: '固定翼飞行器自主导航环境', created_at: '2026-04-21 14:15' },
        { id: 3, project_name: '旋翼控制优化', project_id: 'PROJ-003', description: '旋翼飞行器姿态控制优化', created_at: '2026-04-22 09:00' }
      ],
      showCreateModal: false,
      showEditModal: false,
      newProject: { project_name: '', project_id: '', description: '' },
      editProject: { id: '', project_name: '', description: '' }
    }
  },
  methods: {
    openCreateModal() { this.newProject = { project_name: '', project_id: '', description: '' }; this.showCreateModal = true },
    openEditModal(p) { this.editProject = { id: p.id, project_name: p.project_name, description: p.description }; this.showEditModal = true },
    createProject() {
      this.projects.push({ id: Date.now(), ...this.newProject, created_at: new Date().toLocaleString() })
      this.showCreateModal = false
    },
    updateProject() {
      const idx = this.projects.findIndex(p => p.id === this.editProject.id)
      if (idx !== -1) { this.projects[idx].project_name = this.editProject.project_name; this.projects[idx].description = this.editProject.description }
      this.showEditModal = false
    },
    deleteProject(id) { if (confirm('确定要删除这个项目吗？')) this.projects = this.projects.filter(p => p.id !== id) }
  }
}
</script>

<style scoped>
.projects { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { color: #1a237e; font-size: 1.5rem; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; font-weight: 500; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.btn-primary:hover { box-shadow: 0 2px 8px rgba(26, 35, 126, 0.3); }
.btn-secondary { background-color: #e0e0e0; color: #333; }
.btn-sm { padding: 4px 10px; font-size: 0.8rem; }
.btn-info { background-color: #1976d2; color: white; }
.btn-danger { background-color: #d32f2f; color: white; }
.table-container { background-color: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background-color: #fafafa; font-weight: 600; color: #333; font-size: 0.85rem; }
.data-table tr:hover { background-color: #f8f9ff; }
.empty-row { text-align: center; color: #999; padding: 40px !important; }
code { background-color: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; color: #1a237e; }
.actions { display: flex; gap: 8px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background-color: white; border-radius: 12px; width: 100%; max-width: 480px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; line-height: 1; }
form { padding: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: #3f51b5; }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
</style>
