<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <span>设置</span>
      </template>
      <el-tabs v-model="activeTab">
        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="tab-toolbar">
            <el-button type="primary" @click="showCreateUserDialog">新建用户</el-button>
          </div>

          <el-table :data="users" style="width: 100%" v-loading="usersLoading">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="global_role" label="角色">
              <template #default="{ row }">
                <el-tag :type="row.global_role === 'admin' ? 'danger' : 'info'">{{ row.global_role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" />
            <el-table-column label="操作" width="280">
              <template #default="{ row }">
                <el-button size="small" @click="editUser(row)">编辑</el-button>
                <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
                <el-popconfirm title="确认删除该用户?" @confirm="deleteUser(row)">
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 项目成员管理 -->
        <el-tab-pane label="项目成员" name="members">
          <div class="tab-toolbar">
            <el-select v-model="selectedProjectId" placeholder="选择项目" style="width: 200px; margin-right: 10px;">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <el-button type="primary" @click="showAddMemberDialog" :disabled="!selectedProjectId">添加成员</el-button>
          </div>

          <el-table :data="members" style="width: 100%" v-loading="membersLoading" v-if="selectedProjectId">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'configurer' ? 'warning' : 'info'">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="changeMemberRole(row)">修改角色</el-button>
                <el-popconfirm title="确认移除该成员?" @confirm="removeMember(row)">
                  <template #reference>
                    <el-button size="small" type="danger">移除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="请先选择项目" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新建/编辑用户弹窗 -->
    <el-dialog v-model="showUserDialog" :title="editingUser ? '编辑用户' : '新建用户'" width="400px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.global_role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="配置员" value="configurer" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员弹窗 -->
    <el-dialog v-model="showMemberDialog" title="添加成员" width="400px">
      <el-form :model="memberForm" label-width="80px">
        <el-form-item label="用户名">
          <el-select v-model="memberForm.user_id" filterable placeholder="选择用户" style="width: 100%">
            <el-option v-for="u in availableUsers" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="memberForm.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="配置员" value="configurer" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">确定</el-button>
      </template>
    </el-dialog>

    <!-- 修改角色弹窗 -->
    <el-dialog v-model="showRoleDialog" title="修改成员角色" width="400px">
      <el-form label-width="80px">
        <el-form-item label="用户">
          <el-input :value="editingMember?.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newRole" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="配置员" value="configurer" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMemberRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="showResetPwdDialog" title="重置密码" width="400px">
      <el-form label-width="80px">
        <el-form-item label="用户">
          <el-input :value="resetPwdUser?.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="resetPwdForm.password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="saveResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/api'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const projectStore = useProjectStore()
const authStore = useAuthStore()
const projects = computed(() => projectStore.projects)

const activeTab = ref('users')

// 用户管理
const users = ref<any[]>([])
const usersLoading = ref(false)
const showUserDialog = ref(false)
const editingUser = ref<any>(null)
const userForm = ref({ username: '', password: '', global_role: 'viewer' })

// 项目成员管理
const selectedProjectId = ref('')
const members = ref<any[]>([])
const membersLoading = ref(false)
const showMemberDialog = ref(false)
const memberForm = ref({ user_id: '', role: 'viewer' })
const showRoleDialog = ref(false)
const editingMember = ref<any>(null)
const newRole = ref('viewer')
const showResetPwdDialog = ref(false)
const resetPwdUser = ref<any>(null)
const resetPwdForm = ref({ password: '' })

const availableUsers = computed(() => {
  const memberIds = members.value.map(m => m.user_id)
  return users.value.filter(u => !memberIds.includes(u.id))
})

onMounted(async () => {
  await projectStore.fetchProjects()
  if (projects.value.length > 0) {
    selectedProjectId.value = projects.value[0].id
  }
  if (authStore.user?.global_role === 'admin') {
    await loadUsers()
  }
})

watch(selectedProjectId, async (val) => {
  if (val) await loadMembers()
})

const loadUsers = async () => {
  usersLoading.value = true
  try {
    const res = await api.get('/api/users')
    users.value = res.data.data
  } finally {
    usersLoading.value = false
  }
}

const showCreateUserDialog = () => {
  editingUser.value = null
  userForm.value = { username: '', password: '', global_role: 'viewer' }
  showUserDialog.value = true
}

const editUser = (user: any) => {
  editingUser.value = user
  userForm.value = { username: user.username, password: '', global_role: user.global_role }
  showUserDialog.value = true
}

const saveUser = async () => {
  try {
    if (editingUser.value) {
      await api.put(`/api/users/${editingUser.value.id}`, {
        global_role: userForm.value.global_role,
      })
      ElMessage.success('用户已更新')
    } else {
      await api.post('/api/users', userForm.value)
      ElMessage.success('用户已创建')
    }
    showUserDialog.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const deleteUser = async (user: any) => {
  try {
    await api.delete(`/api/users/${user.id}`)
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const resetPassword = (user: any) => {
  resetPwdUser.value = user
  resetPwdForm.value = { password: '' }
  showResetPwdDialog.value = true
}

const saveResetPassword = async () => {
  if (!resetPwdForm.value.password) {
    ElMessage.warning('请输入新密码')
    return
  }
  try {
    await api.post(`/api/users/${resetPwdUser.value.id}/reset-password`, resetPwdForm.value)
    ElMessage.success('密码已重置')
    showResetPwdDialog.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '重置失败')
  }
}

const loadMembers = async () => {
  if (!selectedProjectId.value) return
  membersLoading.value = true
  try {
    const res = await api.get(`/api/projects/${selectedProjectId.value}/members`)
    members.value = res.data.data
  } finally {
    membersLoading.value = false
  }
}

const showAddMemberDialog = () => {
  memberForm.value = { user_id: '', role: 'viewer' }
  showMemberDialog.value = true
}

const addMember = async () => {
  if (!memberForm.value.user_id) {
    ElMessage.warning('请选择用户')
    return
  }
  try {
    await api.post(`/api/projects/${selectedProjectId.value}/members`, memberForm.value)
    ElMessage.success('成员已添加')
    showMemberDialog.value = false
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

const changeMemberRole = (member: any) => {
  editingMember.value = member
  newRole.value = member.role
  showRoleDialog.value = true
}

const saveMemberRole = async () => {
  try {
    await api.put(`/api/projects/${selectedProjectId.value}/members/${editingMember.value.user_id}`, {
      role: newRole.value,
    })
    ElMessage.success('角色已更新')
    showRoleDialog.value = false
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const removeMember = async (member: any) => {
  try {
    await api.delete(`/api/projects/${selectedProjectId.value}/members/${member.user_id}`)
    ElMessage.success('成员已移除')
    await loadMembers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '移除失败')
  }
}
</script>

<style scoped>
.tab-toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}
</style>
