<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <button @click="openCreateModal" class="btn btn-primary">+ 创建用户</button>
    </div>
    <div class="table-container">
      <table class="data-table">
        <thead><tr><th>ID</th><th>用户名</th><th>角色</th><th>创建时间</th></tr></thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td><span :class="['role-badge', user.role]">{{ roleLabel(user.role) }}</span></td>
            <td>{{ user.created_at }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>创建用户</h3><button @click="showCreateModal = false" class="close-btn">&times;</button></div>
        <form @submit.prevent="createUser">
          <div class="form-group"><label>用户名</label><input type="text" v-model="newUser.username" required></div>
          <div class="form-group"><label>密码</label><input type="password" v-model="newUser.password" required></div>
          <div class="form-group"><label>角色</label>
            <select v-model="newUser.role"><option value="admin">管理员</option><option value="config">配置员</option><option value="dev">开发者</option><option value="viewer">查看用户</option></select>
          </div>
          <div class="modal-footer"><button type="button" @click="showCreateModal = false" class="btn btn-secondary">取消</button><button type="submit" class="btn btn-primary">创建</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Users',
  data() {
    return {
      showCreateModal: false,
      newUser: { username: '', password: '', role: 'viewer' },
      users: [
        { id: 1, username: 'admin', role: 'admin', created_at: '2026-04-20 08:00' },
        { id: 2, username: 'config', role: 'config', created_at: '2026-04-20 08:00' },
        { id: 3, username: 'dev', role: 'dev', created_at: '2026-04-20 08:00' },
        { id: 4, username: 'user', role: 'viewer', created_at: '2026-04-20 08:00' }
      ]
    }
  },
  methods: {
    roleLabel(r) { return { admin: '管理员', config: '配置员', dev: '开发者', viewer: '查看用户' }[r] || r },
    openCreateModal() { this.newUser = { username: '', password: '', role: 'viewer' }; this.showCreateModal = true },
    createUser() {
      this.users.push({ id: Date.now(), username: this.newUser.username, role: this.newUser.role, created_at: new Date().toLocaleString() })
      this.showCreateModal = false
    }
  }
}
</script>

<style scoped>
.users-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { color: #1a237e; font-size: 1.5rem; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.btn-secondary { background: #e0e0e0; color: #333; }
.table-container { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 14px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background: #fafafa; font-weight: 600; font-size: 0.85rem; }
.data-table tr:hover { background: #f8f9ff; }
.role-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
.role-badge.admin { background: #e8eaf6; color: #1a237e; }
.role-badge.config { background: #e3f2fd; color: #1565c0; }
.role-badge.dev { background: #e8f5e9; color: #2e7d32; }
.role-badge.viewer { background: #f3e5f5; color: #7b1fa2; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; border-radius: 12px; width: 100%; max-width: 480px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
form { padding: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #3f51b5; }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
</style>
