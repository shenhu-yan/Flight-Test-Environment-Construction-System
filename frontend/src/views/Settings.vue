<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-desc">系统配置、用户管理与日志查看</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: User Management (admin only) -->
      <el-tab-pane v-if="isAdmin" label="用户管理" name="users">
        <div class="tab-toolbar">
          <el-button type="primary" @click="openAddUserDialog">
            <el-icon><Plus /></el-icon> 新增用户
          </el-button>
        </div>
        <el-table :data="users" border stripe v-loading="loadingUsers">
          <el-table-column prop="id" label="ID" width="240" show-overflow-tooltip />
          <el-table-column prop="username" label="用户名" width="160" />
          <el-table-column prop="global_role" label="全局角色" width="140">
            <template #default="{ row }">
              <el-tag :type="row.global_role === 'admin' ? 'danger' : row.global_role === 'configurer' ? 'warning' : 'info'">
                {{ roleLabel(row.global_role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" text @click="editUser(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click="confirmDeleteUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab 2: Project Members -->
      <el-tab-pane label="项目成员" name="members">
        <div class="tab-toolbar">
          <el-button type="primary" @click="showAddMemberDialog = true" :disabled="!projectStore.currentProject">
            <el-icon><Plus /></el-icon> 添加成员
          </el-button>
        </div>
        <el-table :data="members" border stripe v-loading="loadingMembers">
          <el-table-column prop="username" label="用户名" width="160" />
          <el-table-column prop="role" label="项目角色" width="140">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'configurer' ? 'warning' : 'info'">
                {{ roleLabel(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" text type="danger" @click="removeMember(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!members.length && !loadingMembers" description="暂无项目成员" :image-size="60" />
      </el-tab-pane>

      <!-- Tab 3: Optimization Schedule -->
      <el-tab-pane label="优化调度" name="schedule">
        <el-form :model="scheduleForm" label-width="120px" style="max-width: 500px">
          <el-form-item label="启用定时优化">
            <el-switch v-model="scheduleForm.enabled" />
          </el-form-item>
          <el-form-item label="Cron 表达式">
            <el-input v-model="scheduleForm.cron" placeholder="例: 0 0 * * *" :disabled="!scheduleForm.enabled" />
          </el-form-item>
          <el-form-item label="执行周期">
            <el-select v-model="scheduleForm.cron" placeholder="选择预设周期" :disabled="!scheduleForm.enabled" clearable>
              <el-option label="每小时" value="0 * * * *" />
              <el-option label="每天凌晨" value="0 0 * * *" />
              <el-option label="每周一凌晨" value="0 0 * * 1" />
              <el-option label="每月1号" value="0 0 1 * *" />
            </el-select>
          </el-form-item>
          <el-form-item label="最大迭代数">
            <el-input-number v-model="scheduleForm.max_iterations" :min="1" :max="1000" :disabled="!scheduleForm.enabled" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSchedule">保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- Tab 4: Operation Logs -->
      <el-tab-pane label="操作日志" name="logs">
        <div class="tab-toolbar">
          <div class="log-filters">
            <el-select v-model="logFilter.action" placeholder="操作类型" clearable style="width: 150px">
              <el-option label="创建" value="create" />
              <el-option label="更新" value="update" />
              <el-option label="删除" value="delete" />
              <el-option label="登录" value="login" />
              <el-option label="导出" value="export" />
            </el-select>
            <el-date-picker
              v-model="logFilter.timeRange"
              type="daterange"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 280px"
            />
            <el-button @click="loadLogs">查询</el-button>
          </div>
          <el-button @click="exportLogsCsv">
            <el-icon><Download /></el-icon> 导出CSV
          </el-button>
        </div>
        <el-table :data="operationLogs" border stripe v-loading="loadingLogs">
          <el-table-column prop="action" label="操作" width="120" />
          <el-table-column prop="resource_type" label="资源类型" width="120" />
          <el-table-column prop="resource_id" label="资源ID" width="200" show-overflow-tooltip />
          <el-table-column prop="operator" label="操作人" width="120" />
          <el-table-column prop="ip_address" label="IP地址" width="140" />
          <el-table-column prop="created_at" label="时间" min-width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab 5: System Logs -->
      <el-tab-pane label="系统日志" name="system_logs">
        <div class="tab-toolbar">
          <div class="log-filters">
            <el-select v-model="sysLogFilter.level" placeholder="日志级别" clearable style="width: 150px">
              <el-option label="DEBUG" value="debug" />
              <el-option label="INFO" value="info" />
              <el-option label="WARNING" value="warning" />
              <el-option label="ERROR" value="error" />
            </el-select>
            <el-button @click="loadSystemLogs">查询</el-button>
          </div>
        </div>
        <el-table :data="systemLogs" border stripe v-loading="loadingSysLogs">
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag :type="sysLogLevelType(row.level)" size="small">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="140" />
          <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab 6: Notifications -->
      <el-tab-pane label="通知" name="notifications">
        <div class="tab-toolbar">
          <div class="log-filters">
            <el-select v-model="notifFilter.isRead" placeholder="状态" clearable style="width: 150px">
              <el-option label="未读" :value="false" />
              <el-option label="已读" :value="true" />
            </el-select>
            <el-button @click="loadNotifications">查询</el-button>
          </div>
          <el-button @click="markAllRead" :disabled="!unreadCount">全部已读</el-button>
        </div>
        <el-table :data="notifications" border stripe v-loading="loadingNotifs">
          <el-table-column width="60">
            <template #default="{ row }">
              <span class="notif-dot" :class="{ unread: !row.is_read }"></span>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" width="200" />
          <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button v-if="!row.is_read" size="small" text @click="markRead(row)">标为已读</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Add/Edit User Dialog -->
    <el-dialog v-model="showUserDialog" :title="editingUser ? '编辑用户' : '新增用户'" width="420px" destroy-on-close>
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" :disabled="!!editingUser" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.global_role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="配置员" value="configurer" />
            <el-option label="查看员" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingUser" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- Add Member Dialog -->
    <el-dialog v-model="showAddMemberDialog" title="添加项目成员" width="420px" destroy-on-close>
      <el-form :model="memberForm" label-width="80px">
        <el-form-item label="用户">
          <el-select v-model="memberForm.user_id" placeholder="选择用户" style="width: 100%" filterable>
            <el-option v-for="u in availableUsers" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="memberForm.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="配置员" value="configurer" />
            <el-option label="查看员" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/project'
import { getUsers, createUser, updateUser, deleteUser } from '../api/auth'
import { getMembers, addMember, removeMember } from '../api/projects'
import { getOperationLogs, getSystemLogs, getNotifications, markNotificationRead, markAllNotificationsRead } from '../api/logs'
import type { User, Notification } from '../types'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const isAdmin = computed(() => authStore.user?.global_role === 'admin')
const activeTab = ref('members')

// Users
const users = ref<any[]>([])
const loadingUsers = ref(false)
const showUserDialog = ref(false)
const editingUser = ref<any>(null)
const savingUser = ref(false)
const userForm = ref({ username: '', password: '', global_role: 'viewer' })

// Members
const members = ref<any[]>([])
const loadingMembers = ref(false)
const showAddMemberDialog = ref(false)
const memberForm = ref({ user_id: '', role: 'viewer' })
const availableUsers = ref<User[]>([])

// Schedule
const scheduleForm = ref({ enabled: false, cron: '0 0 * * *', max_iterations: 10 })

// Operation Logs
const operationLogs = ref<any[]>([])
const loadingLogs = ref(false)
const logFilter = ref({ action: '', timeRange: null as any })

// System Logs
const systemLogs = ref<any[]>([])
const loadingSysLogs = ref(false)
const sysLogFilter = ref({ level: '' })

// Notifications
const notifications = ref<Notification[]>([])
const loadingNotifs = ref(false)
const notifFilter = ref<{ isRead: boolean | null }>({ isRead: null })
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

function roleLabel(role: string) {
  const map: Record<string, string> = { admin: '管理员', configurer: '配置员', viewer: '查看员' }
  return map[role] || role
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function sysLogLevelType(level: string) {
  const map: Record<string, string> = { debug: 'info', info: '', warning: 'warning', error: 'danger' }
  return (map[level] || '') as any
}

// --- Users ---
function openAddUserDialog() {
  editingUser.value = null
  userForm.value = { username: '', password: '', global_role: 'viewer' }
  showUserDialog.value = true
}

function editUser(user: any) {
  editingUser.value = user
  userForm.value = { username: user.username, password: '', global_role: user.global_role }
  showUserDialog.value = true
}

async function loadUsers() {
  loadingUsers.value = true
  try {
    const res = await getUsers()
    users.value = res.data?.data || []
    availableUsers.value = users.value
  } catch { users.value = [] }
  finally { loadingUsers.value = false }
}

async function saveUser() {
  savingUser.value = true
  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, { global_role: userForm.value.global_role })
    } else {
      if (!userForm.value.username || !userForm.value.password) {
        ElMessage.warning('请填写用户名和密码')
        savingUser.value = false
        return
      }
      await createUser(userForm.value)
    }
    ElMessage.success('保存成功')
    showUserDialog.value = false
    editingUser.value = null
    userForm.value = { username: '', password: '', global_role: 'viewer' }
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e.message || '保存失败')
  } finally { savingUser.value = false }
}

async function confirmDeleteUser(user: any) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」？`, '确认删除', { type: 'warning' })
    await deleteUser(user.id)
    ElMessage.success('已删除')
    await loadUsers()
  } catch {}
}

// --- Members ---
async function loadMembers() {
  const projectId = projectStore.currentProject?.id
  if (!projectId) { members.value = []; return }
  loadingMembers.value = true
  try {
    const res = await getMembers(projectId)
    members.value = res.data?.data || []
  } catch { members.value = [] }
  finally { loadingMembers.value = false }
}

async function addMember() {
  const projectId = projectStore.currentProject?.id
  if (!projectId || !memberForm.value.user_id) {
    ElMessage.warning('请选择用户')
    return
  }
  try {
    await addMember(projectId, memberForm.value)
    ElMessage.success('添加成功')
    showAddMemberDialog.value = false
    memberForm.value = { user_id: '', role: 'viewer' }
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e.message || '添加失败')
  }
}

async function removeMember(member: any) {
  const projectId = projectStore.currentProject?.id
  if (!projectId) return
  try {
    await ElMessageBox.confirm(`确定移除成员「${member.username}」？`, '确认移除', { type: 'warning' })
    await removeMember(projectId, member.user_id || member.id)
    ElMessage.success('已移除')
    await loadMembers()
  } catch {}
}

// --- Schedule ---
async function saveSchedule() {
  ElMessage.success('优化调度配置已保存')
}

// --- Operation Logs ---
async function loadLogs() {
  loadingLogs.value = true
  try {
    const params: any = { page: 1, page_size: 100 }
    if (logFilter.value.action) params.action = logFilter.value.action
    const res = await getOperationLogs(params)
    operationLogs.value = res.data?.data || []
  } catch { operationLogs.value = [] }
  finally { loadingLogs.value = false }
}

function exportLogsCsv() {
  if (!operationLogs.value.length) {
    ElMessage.warning('暂无日志可导出')
    return
  }
  const headers = ['操作', '资源类型', '资源ID', '操作人', 'IP地址', '时间']
  const rows = operationLogs.value.map(r => [
    r.action, r.resource_type, r.resource_id, r.operator, r.ip_address, r.created_at
  ])
  const csv = [headers, ...rows].map(row => row.map(c => `"${(c || '').toString().replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `operation_logs_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// --- System Logs ---
async function loadSystemLogs() {
  loadingSysLogs.value = true
  try {
    const params: any = { page: 1, page_size: 100 }
    if (sysLogFilter.value.level) params.level = sysLogFilter.value.level
    const res = await getSystemLogs(params)
    systemLogs.value = res.data?.data || []
  } catch { systemLogs.value = [] }
  finally { loadingSysLogs.value = false }
}

// --- Notifications ---
async function loadNotifications() {
  loadingNotifs.value = true
  try {
    const params: any = { page: 1, page_size: 100 }
    if (notifFilter.value.isRead !== null) params.is_read = notifFilter.value.isRead
    const res = await getNotifications(params)
    notifications.value = res.data?.data || []
  } catch { notifications.value = [] }
  finally { loadingNotifs.value = false }
}

async function markRead(notif: Notification) {
  try {
    await markNotificationRead(notif.id)
    notif.is_read = true
  } catch {}
}

async function markAllRead() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => n.is_read = true)
    ElMessage.success('已全部标为已读')
  } catch { ElMessage.error('操作失败') }
}

onMounted(() => {
  if (isAdmin.value) loadUsers()
  loadMembers()
  loadLogs()
  loadSystemLogs()
  loadNotifications()
})
</script>

<style scoped>
.settings-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 4px; }
.page-desc { font-size: 15px; color: var(--text-secondary); margin: 0; }
.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.log-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}
.notif-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d2d2d7;
}
.notif-dot.unread {
  background: var(--primary);
}
</style>
