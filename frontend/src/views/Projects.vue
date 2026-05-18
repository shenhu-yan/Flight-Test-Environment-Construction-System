<template>
  <div class="projects-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目管理</h1>
        <p class="page-desc">创建和管理飞行试验项目</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-number">{{ projects.length }}</div>
        <div class="stat-label">项目总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ projects.length }}</div>
        <div class="stat-label">活跃项目</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ memberCount }}</div>
        <div class="stat-label">参与成员</div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Empty -->
    <div v-else-if="projects.length === 0" class="empty-state">
      <el-empty description="暂无项目，点击上方按钮创建第一个项目">
        <el-button type="primary" @click="openCreateDialog">创建项目</el-button>
      </el-empty>
    </div>

    <!-- Project List -->
    <div v-else class="project-list">
      <div
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        :class="{ active: projectStore.currentProject?.id === project.id }"
      >
        <div class="card-header">
          <div class="card-title-row">
            <h3 class="card-title">{{ project.name }}</h3>
            <el-tag
              v-if="projectStore.currentProject?.id === project.id"
              type="success"
              size="small"
              effect="dark"
              round
            >
              当前项目
            </el-tag>
          </div>
          <p class="card-desc">{{ project.description || '暂无描述' }}</p>
        </div>

        <div class="card-meta">
          <div class="meta-item">
            <el-icon><User /></el-icon>
            <span>{{ project.created_by || '未知' }}</span>
          </div>
          <div class="meta-item">
            <el-icon><Clock /></el-icon>
            <span>{{ formatDate(project.created_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <el-button
            v-if="projectStore.currentProject?.id !== project.id"
            type="primary"
            size="small"
            @click="switchToProject(project)"
          >
            切换到此项目
          </el-button>
          <el-button size="small" @click="openEditDialog(project)">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <el-button size="small" @click="openMembersDialog(project)">
            <el-icon><UserFilled /></el-icon> 成员
          </el-button>
          <el-popconfirm
            title="确定要删除此项目吗？此操作不可恢复。"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @confirm="handleDelete(project)"
          >
            <template #reference>
              <el-button size="small" type="danger" text>
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="showFormDialog"
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-position="top" :rules="formRules" ref="formRef">
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="输入项目名称，如：LeMans空调优化测试"
            maxlength="128"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="输入项目描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Members Dialog -->
    <el-dialog
      v-model="showMembersDialog"
      :title="`项目成员 — ${selectedProjectForMembers?.name || ''}`"
      width="520px"
    >
      <div class="members-section">
        <div class="members-header">
          <span class="members-count">共 {{ members.length }} 位成员</span>
          <el-button type="primary" size="small" @click="showAddMember = true">
            <el-icon><Plus /></el-icon> 添加成员
          </el-button>
        </div>

        <!-- Add member form -->
        <div v-if="showAddMember" class="add-member-form">
          <el-input
            v-model="newMemberId"
            placeholder="输入用户ID"
            size="small"
            style="flex:1"
          />
          <el-select v-model="newMemberRole" size="small" style="width:100px">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑者" value="editor" />
            <el-option label="查看者" value="viewer" />
          </el-select>
          <el-button type="primary" size="small" :loading="addingMember" @click="handleAddMember">
            添加
          </el-button>
          <el-button size="small" @click="showAddMember = false">取消</el-button>
        </div>

        <!-- Member list -->
        <div class="member-list" v-if="members.length">
          <div v-for="m in members" :key="m.id" class="member-item">
            <div class="member-info">
              <div class="member-avatar">{{ (m.user_id || '?')[0].toUpperCase() }}</div>
              <div>
                <div class="member-id">{{ m.user_id }}</div>
                <el-tag size="small" :type="m.role === 'admin' ? 'danger' : m.role === 'editor' ? 'warning' : 'info'" round>
                  {{ m.role === 'admin' ? '管理员' : m.role === 'editor' ? '编辑者' : '查看者' }}
                </el-tag>
              </div>
            </div>
            <el-popconfirm
              title="确定移除此成员？"
              @confirm="handleRemoveMember(m)"
            >
              <template #reference>
                <el-button size="small" type="danger" text>移除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
        <div v-else class="empty-members">暂无成员</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, User, UserFilled, Clock } from '@element-plus/icons-vue'
import { useProjectStore } from '../stores/project'
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  getMembers,
  addMember,
  removeMember
} from '../api/projects'
import type { Project } from '../types'

const projectStore = useProjectStore()

const projects = ref<Project[]>([])
const loading = ref(false)
const submitting = ref(false)

// Form dialog
const showFormDialog = ref(false)
const editingProject = ref<Project | null>(null)
const form = ref({ name: '', description: '' })
const formRef = ref()
const formRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

// Members dialog
const showMembersDialog = ref(false)
const selectedProjectForMembers = ref<Project | null>(null)
const members = ref<any[]>([])
const showAddMember = ref(false)
const newMemberId = ref('')
const newMemberRole = ref('viewer')
const addingMember = ref(false)

const memberCount = computed(() => {
  // Approximate: each project has at least 1 member (creator)
  return projects.value.length
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

async function loadProjects() {
  loading.value = true
  try {
    const res = await getProjects({ page: 1, page_size: 100 })
    const data = res.data.data
    projects.value = Array.isArray(data) ? data : (data?.data || [])
    // Update store
    projectStore.projects = projects.value
    projectStore.initFromStorage()
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingProject.value = null
  form.value = { name: '', description: '' }
  showFormDialog.value = true
}

function openEditDialog(project: Project) {
  editingProject.value = project
  form.value = { name: project.name, description: project.description || '' }
  showFormDialog.value = true
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  submitting.value = true
  try {
    if (editingProject.value) {
      await updateProject(editingProject.value.id, {
        name: form.value.name,
        description: form.value.description
      })
      ElMessage.success('项目已更新')
    } else {
      const res = await createProject({
        name: form.value.name,
        description: form.value.description
      })
      ElMessage.success('项目创建成功')
      // Auto switch to new project
      const newProject = res.data?.data
      if (newProject) {
        projectStore.switchProject(newProject)
      }
    }
    showFormDialog.value = false
    await loadProjects()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(project: Project) {
  try {
    await deleteProject(project.id)
    ElMessage.success('项目已删除')
    if (projectStore.currentProject?.id === project.id) {
      projectStore.currentProject = null
      localStorage.removeItem('currentProjectId')
    }
    await loadProjects()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '删除失败')
  }
}

function switchToProject(project: Project) {
  projectStore.switchProject(project)
  ElMessage.success(`已切换到项目「${project.name}」`)
}

async function openMembersDialog(project: Project) {
  selectedProjectForMembers.value = project
  showMembersDialog.value = true
  showAddMember.value = false
  newMemberId.value = ''
  newMemberRole.value = 'viewer'
  await loadMembers(project.id)
}

async function loadMembers(projectId: string) {
  try {
    const res = await getMembers(projectId)
    const data = res.data.data
    members.value = Array.isArray(data) ? data : (data?.data || [])
  } catch {
    members.value = []
  }
}

async function handleAddMember() {
  if (!newMemberId.value.trim()) {
    ElMessage.warning('请输入用户ID')
    return
  }
  if (!selectedProjectForMembers.value) return
  addingMember.value = true
  try {
    await addMember(selectedProjectForMembers.value.id, {
      user_id: newMemberId.value.trim(),
      role: newMemberRole.value
    })
    ElMessage.success('成员已添加')
    showAddMember.value = false
    newMemberId.value = ''
    await loadMembers(selectedProjectForMembers.value.id)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '添加失败')
  } finally {
    addingMember.value = false
  }
}

async function handleRemoveMember(member: any) {
  if (!selectedProjectForMembers.value) return
  try {
    await removeMember(selectedProjectForMembers.value.id, member.id)
    ElMessage.success('成员已移除')
    await loadMembers(selectedProjectForMembers.value.id)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '移除失败')
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-page {
  max-width: 1000px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.03em;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Project list */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px 24px;
  transition: all 0.2s;
}

.project-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border-color: var(--border);
}

.project-card.active {
  border-color: var(--primary);
  background: rgba(0, 102, 204, 0.03);
}

.card-header {
  margin-bottom: 12px;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0;
}

.card-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.card-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-muted);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

/* Loading & Empty */
.loading-state,
.empty-state {
  padding: 60px 0;
}

/* Members */
.members-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.members-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.members-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.add-member-form {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.member-id {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.empty-members {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 14px;
}
</style>
