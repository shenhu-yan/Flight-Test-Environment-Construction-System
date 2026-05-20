<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="header-left">
        <span class="logo">Flight Test System</span>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="header-menu"
        >
          <el-menu-item index="/envs">环境管理</el-menu-item>
          <el-menu-item index="/monitor">训练监控</el-menu-item>
          <el-menu-item index="/optimization">优化中心</el-menu-item>
          <el-menu-item index="/models">模型库</el-menu-item>
          <el-menu-item index="/settings">设置</el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <el-dropdown>
          <span class="user-info">
            {{ authStore.user?.username || 'User' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="layout-aside">
        <div class="project-section">
          <div class="project-header">
            <span>项目</span>
            <div>
              <el-button type="primary" size="small" @click="showCreateProjectDialog = true">
                新建
              </el-button>
              <el-button
                v-if="projectStore.currentProject"
                type="danger"
                size="small"
                @click="deleteProject"
              >
                删除
              </el-button>
            </div>
          </div>
          <el-select
            v-model="projectStore.currentProject"
            placeholder="选择项目"
            value-key="id"
            style="width: 100%"
          >
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project"
            />
          </el-select>
        </div>
      </el-aside>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="showCreateProjectDialog" title="新建项目" width="400px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="createForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="createForm.description" type="textarea" placeholder="请输入项目描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateProjectDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()

const showCreateProjectDialog = ref(false)
const createForm = ref({
  name: '',
  description: ''
})

const activeMenu = computed(() => route.path)

onMounted(async () => {
  await authStore.fetchUser()
  await projectStore.fetchProjects()
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const createProject = async () => {
  if (!createForm.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }

  try {
    await projectStore.createProject(createForm.value.name, createForm.value.description)
    showCreateProjectDialog.value = false
    createForm.value = { name: '', description: '' }
    ElMessage.success('项目创建成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  }
}

const deleteProject = async () => {
  if (!projectStore.currentProject) return

  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${projectStore.currentProject.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    await projectStore.deleteProject(projectStore.currentProject.id)
    ElMessage.success('项目已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e6e6e6;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  margin-right: 40px;
}

.header-menu {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.layout-aside {
  background: #f5f5f5;
  border-right: 1px solid #e6e6e6;
}

.project-section {
  padding: 16px;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: bold;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
