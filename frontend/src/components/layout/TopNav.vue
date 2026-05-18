<template>
  <div class="top-nav">
    <div class="nav-left">
      <span class="logo-text">FLTECT</span>
      <span class="logo-subtitle">飞行试验环境构建系统</span>
    </div>
    <div class="nav-center">
      <router-link to="/" class="nav-link" :class="{ active: route.path === '/' || route.path === '/projects' }">项目管理</router-link>
      <router-link to="/env-generation" class="nav-link" :class="{ active: route.path === '/env-generation' }">环境管理</router-link>
      <router-link to="/monitor" class="nav-link" :class="{ active: route.path === '/monitor' }">训练监控</router-link>
      <router-link to="/optimization" class="nav-link" :class="{ active: route.path === '/optimization' }">优化中心</router-link>
      <router-link to="/models" class="nav-link" :class="{ active: route.path === '/models' }">模型库</router-link>
    </div>
    <div class="nav-right">
      <!-- Notification Bell -->
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-badge">
        <el-button text class="notification-btn" @click="$router.push('/settings?tab=notifications')">
          <el-icon :size="18"><Bell /></el-icon>
        </el-button>
      </el-badge>

      <!-- User Dropdown -->
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-dropdown">
          <el-icon><User /></el-icon>
          <span class="username">{{ authStore.user?.username || '用户' }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="authStore.user?.global_role === 'admin'" command="settings">
              <el-icon><Setting /></el-icon> 系统设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, User, ArrowDown, Setting, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { getNotifications } from '../../api/logs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const unreadCount = ref(0)
let pollTimer: number | null = null

async function fetchUnreadCount() {
  try {
    const res = await getNotifications({ page: 1, page_size: 1, is_read: false })
    const data = res.data
    unreadCount.value = data?.total || 0
  } catch {
    unreadCount.value = 0
  }
}

function handleCommand(command: string) {
  if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'logout') {
    authStore.logout()
  }
}

onMounted(() => {
  fetchUnreadCount()
  pollTimer = window.setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.top-nav {
  height: var(--nav-height);
  background: #000000;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.logo-subtitle {
  font-size: 12px;
  color: #86868b;
  font-weight: 400;
}
.nav-center {
  display: flex;
  gap: 4px;
}
.nav-link {
  color: #86868b;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}
.nav-link:hover {
  color: #ffffff;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.08);
}
.nav-link.active {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.12);
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.notification-badge {
  margin-right: 4px;
}
.notification-btn {
  color: #ffffff !important;
  padding: 6px !important;
}
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #ffffff;
  cursor: pointer;
  font-size: 13px;
}
.username {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
