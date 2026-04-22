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
      const labels = {
        admin: '管理员',
        config: '配置员',
        dev: '开发者',
        viewer: '查看用户'
      }
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
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
  color: white;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-brand .brand-link {
  font-size: 1.2rem;
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
  transition: all 0.2s;
  font-size: 0.9rem;
}

.navbar-item:hover,
.navbar-item.router-link-active {
  background-color: rgba(255,255,255,0.15);
  color: white;
}

.navbar-dropdown {
  position: relative;
}

.dropdown-toggle {
  cursor: pointer;
  user-select: none;
}

.dropdown-content {
  position: absolute;
  background-color: white;
  min-width: 160px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  border-radius: 8px;
  overflow: hidden;
  display: none;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 8px;
}

.navbar-dropdown:hover .dropdown-content {
  display: block;
}

.dropdown-item {
  color: #333;
  padding: 10px 16px;
  text-decoration: none;
  display: block;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.dropdown-item:hover {
  background-color: #e8eaf6;
  color: #1a237e;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.9);
}

.logout-btn {
  background-color: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background-color: rgba(255,255,255,0.25);
}

.main-content {
  flex: 1;
  background-color: #f0f2f5;
}

@media (max-width: 768px) {
  .navbar {
    flex-wrap: wrap;
    height: auto;
    padding: 12px;
    gap: 8px;
  }

  .navbar-menu {
    order: 3;
    width: 100%;
    flex-wrap: wrap;
    justify-content: center;
  }

  .navbar-right {
    order: 2;
  }
}
</style>
