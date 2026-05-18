<template>
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="section-label">当前项目</div>
      <el-select
        v-model="selectedProjectId"
        placeholder="选择项目"
        size="default"
        style="width: 100%"
        filterable
        @change="handleProjectChange"
      >
        <el-option
          v-for="p in projectStore.projects"
          :key="p.id"
          :label="p.name"
          :value="p.id"
        />
      </el-select>
    </div>

    <div class="sidebar-section" v-if="projectStore.currentProject">
      <div class="section-label">项目信息</div>
      <div class="project-info">
        <div class="info-row">
          <span class="info-label">名称</span>
          <span class="info-value">{{ projectStore.currentProject.name }}</span>
        </div>
        <div class="info-row" v-if="projectStore.currentProject.description">
          <span class="info-label">描述</span>
          <span class="info-value description">{{ projectStore.currentProject.description }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-label">快捷操作</div>
      <div class="quick-actions">
        <el-button type="primary" style="width: 100%" @click="$router.push('/env-generation')">
          <el-icon><Plus /></el-icon> 新建环境
        </el-button>
        <el-button style="width: 100%" @click="$router.push('/models')">
          <el-icon><Upload /></el-icon> 上传模型
        </el-button>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-label">最近环境</div>
      <div class="recent-list" v-if="recentEnvs.length">
        <div
          v-for="env in recentEnvs"
          :key="env.id"
          class="recent-item"
          @click="$router.push('/')"
        >
          <span class="env-name">{{ env.name }}</span>
          <StatusTag :status="env.status" />
        </div>
      </div>
      <div v-else class="empty-hint">暂无环境</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { useProjectStore } from '../../stores/project'
import { getEnvs } from '../../api/envs'
import StatusTag from '../common/StatusTag.vue'
import type { FlightEnv } from '../../types'

const projectStore = useProjectStore()
const selectedProjectId = ref('')
const recentEnvs = ref<FlightEnv[]>([])

const currentProject = computed(() => projectStore.currentProject)

watch(currentProject, async (proj) => {
  if (proj) {
    selectedProjectId.value = proj.id
    await loadRecentEnvs(proj.id)
  }
}, { immediate: true })

async function loadRecentEnvs(projectId: string) {
  try {
    const res = await getEnvs(projectId, { page: 1, page_size: 5 })
    const data = res.data.data
    recentEnvs.value = Array.isArray(data) ? data : (data?.data || [])
  } catch {
    recentEnvs.value = []
  }
}

function handleProjectChange(id: string) {
  const proj = projectStore.projects.find(p => p.id === id)
  if (proj) projectStore.switchProject(proj)
}

onMounted(async () => {
  await projectStore.fetchProjects()
  projectStore.initFromStorage()
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-light);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  height: 100%;
}
.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.section-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
}
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.project-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.info-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}
.info-label {
  color: var(--text-muted);
  min-width: 36px;
}
.info-value {
  color: var(--text-primary);
  font-weight: 500;
}
.info-value.description {
  font-weight: 400;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 14px;
}
.recent-item:hover {
  background: rgba(0, 0, 0, 0.04);
}
.env-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}
.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
