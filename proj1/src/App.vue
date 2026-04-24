<template>
  <div class="app">
    <nav v-if="isLoggedIn" class="navbar">
      <div class="navbar-brand">
        <router-link to="/dashboard" class="brand-link">飞行试验环境构建系统</router-link>
      </div>
      <div class="navbar-menu">
        <router-link to="/dashboard" class="navbar-item">仪表盘</router-link>
        <router-link to="/projects" class="navbar-item">项目管理</router-link>
        <router-link to="/environments" class="navbar-item">环境管理</router-link>
        <router-link to="/models" class="navbar-item">模型管理</router-link>
        <div class="navbar-dropdown">
          <span class="navbar-item dropdown-toggle">环境工具 ▾</span>
          <div class="dropdown-content">
            <router-link to="/env-gen" class="dropdown-item">环境生成</router-link>
            <router-link to="/env-adjust" class="dropdown-item">环境调整</router-link>
            <router-link to="/env-optimize" class="dropdown-item">环境优化</router-link>
          </div>
        </div>
        <router-link v-if="userRole === 'admin'" to="/users" class="navbar-item">用户管理</router-link>
      </div>
      <div class="navbar-right">
        <span class="user-info">{{ username }} ({{ roleLabel }})</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      isLoggedIn: false,
      username: '',
      userRole: ''
    }
  },
  computed: {
    roleLabel() {
      const labels = { admin: '管理员', config: '配置员', dev: '开发者', viewer: '查看用户' }
      return labels[this.userRole] || this.userRole
    }
  },
  watch: {
    $route() {
      this.checkLoginStatus()
    }
  },
  mounted() {
    this.checkLoginStatus()
  },
  methods: {
    checkLoginStatus() {
      const token = localStorage.getItem('token')
      if (token) {
        this.isLoggedIn = true
        this.username = localStorage.getItem('username') || ''
        this.userRole = localStorage.getItem('role') || ''
      } else {
        this.isLoggedIn = false
        this.username = ''
        this.userRole = ''
      }
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      this.isLoggedIn = false
      this.username = ''
      this.userRole = ''
      this.$router.push('/')
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f6fa;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-brand .brand-link {
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  text-decoration: none;
  letter-spacing: 1px;
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: 4px;
}

.navbar-item {
  color: rgba(255,255,255,0.85);
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.navbar-item:hover,
.navbar-item.router-link-active {
  color: white;
  background-color: rgba(255,255,255,0.15);
}

.navbar-dropdown {
  position: relative;
}

.dropdown-toggle {
  cursor: pointer;
}

.dropdown-content {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  min-width: 140px;
  overflow: hidden;
  z-index: 200;
}

.navbar-dropdown:hover .dropdown-content {
  display: block;
}

.dropdown-item {
  display: block;
  color: #333;
  text-decoration: none;
  padding: 10px 16px;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: #f0f0ff;
  color: #1a237e;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  font-size: 0.85rem;
  opacity: 0.9;
}

.logout-btn {
  background-color: rgba(255,255,255,0.2);
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background-color: rgba(255,255,255,0.35);
}

.main-content {
  min-height: calc(100vh - 56px);
}
</style>
