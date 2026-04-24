<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">✈</div>
        <h2>飞行试验环境构建系统</h2>
        <p>Flight Test Environment Construction System</p>
      </div>
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="username" required placeholder="请输入用户名" autocomplete="username">
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required placeholder="请输入密码" autocomplete="current-password">
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
      <div class="login-footer">
        <p>默认账号：admin/admin123 | config/config123 | dev/dev123 | user/user123</p>
      </div>
    </div>
  </div>
</template>

<script>
const mockUsers = [
  { username: 'admin', password: 'admin123', role: 'admin' },
  { username: 'config', password: 'config123', role: 'config' },
  { username: 'dev', password: 'dev123', role: 'dev' },
  { username: 'user', password: 'user123', role: 'viewer' }
]

export default {
  name: 'Login',
  data() {
    return { username: '', password: '', error: '', loading: false }
  },
  methods: {
    login() {
      this.loading = true
      this.error = ''
      const user = mockUsers.find(u => u.username === this.username && u.password === this.password)
      if (user) {
        localStorage.setItem('token', 'mock-token-' + Date.now())
        localStorage.setItem('username', user.username)
        localStorage.setItem('role', user.role)
        this.$router.push('/dashboard')
      } else {
        this.error = '登录失败，请检查用户名和密码'
      }
      this.loading = false
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
}
.login-card {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  width: 100%;
  max-width: 420px;
  overflow: hidden;
}
.login-header {
  text-align: center;
  padding: 40px 30px 20px;
  background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%);
}
.login-icon { font-size: 3rem; margin-bottom: 12px; }
.login-header h2 { color: #1a237e; font-size: 1.4rem; margin-bottom: 6px; }
.login-header p { color: #5c6bc0; font-size: 0.8rem; letter-spacing: 0.5px; }
.login-form { padding: 30px; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input {
  width: 100%; padding: 12px 14px; border: 2px solid #e0e0e0; border-radius: 8px;
  font-size: 15px; transition: border-color 0.2s, box-shadow 0.2s; outline: none;
}
.form-group input:focus { border-color: #3f51b5; box-shadow: 0 0 0 3px rgba(63, 81, 181, 0.15); }
.login-btn {
  width: 100%; background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
  color: white; border: none; padding: 14px; border-radius: 8px; font-size: 16px;
  font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; letter-spacing: 2px;
}
.login-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(26, 35, 126, 0.4); }
.login-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.error-message { color: #d32f2f; text-align: center; margin-bottom: 16px; padding: 10px; background-color: #ffebee; border-radius: 6px; font-size: 0.9rem; }
.login-footer { text-align: center; padding: 16px 30px 24px; border-top: 1px solid #f0f0f0; }
.login-footer p { color: #999; font-size: 0.75rem; line-height: 1.5; }
</style>
