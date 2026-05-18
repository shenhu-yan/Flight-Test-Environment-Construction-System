<template>
  <div class="app-layout">
    <TopNav />
    <div class="app-body">
      <SideBar />
      <div class="main-content">
        <router-view />
      </div>
    </div>
    <div class="status-bar">
      <span class="ws-dot" :class="{ connected: wsConnected }"></span>
      <span class="status-text">{{ wsConnected ? '已连接' : '未连接' }}</span>
      <span class="separator">·</span>
      <span class="project-name">{{ projectStore.currentProject?.name || '未选择项目' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import TopNav from './TopNav.vue'
import SideBar from './SideBar.vue'
import { useProjectStore } from '../../stores/project'
import { useAuthStore } from '../../stores/auth'
import { getNotifications } from '../../api/logs'

const projectStore = useProjectStore()
const authStore = useAuthStore()
const wsConnected = ref(false)

let pollTimer: number | null = null
let lastNotifCount = 0

async function checkNewNotifications() {
  try {
    const res = await getNotifications({ page: 1, page_size: 1, is_read: false })
    const total = res.data?.total || 0
    if (lastNotifCount > 0 && total > lastNotifCount) {
      ElNotification({
        title: '新通知',
        message: `您有 ${total - lastNotifCount} 条新通知`,
        type: 'info',
        duration: 5000
      })
    }
    lastNotifCount = total
    wsConnected.value = true
  } catch {
    wsConnected.value = false
  }
}

onMounted(() => {
  authStore.fetchUser()

  // Use HTTP polling for connection status (no /ws/notifications endpoint exists)
  checkNewNotifications()
  pollTimer = window.setInterval(checkNewNotifications, 60000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.app-body {
  display: flex;
  flex: 1;
  margin-top: var(--nav-height);
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-primary);
}
.status-bar {
  height: var(--status-bar-height);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: 12px;
  color: var(--text-secondary);
  gap: 6px;
}
.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  transition: background 0.3s;
}
.ws-dot.connected {
  background: var(--success);
}
.separator {
  margin: 0 4px;
}
.project-name {
  font-weight: 500;
}
</style>
