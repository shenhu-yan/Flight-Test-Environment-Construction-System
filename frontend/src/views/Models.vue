<template>
  <div class="models-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模型库</span>
          <div class="header-actions">
            <el-select v-model="filterType" placeholder="模型类型" clearable style="width: 120px; margin-right: 10px">
              <el-option label="场景模型" value="scene" />
              <el-option label="物理模型" value="physics" />
              <el-option label="RL算法" value="rl_algorithm" />
              <el-option label="奖励函数" value="reward" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px; margin-right: 10px">
              <el-option label="活跃" value="active" />
              <el-option label="推荐" value="recommended" />
              <el-option label="已弃用" value="deprecated" />
            </el-select>
            <el-button type="primary" @click="showUploadDialog = true">上传模型</el-button>
          </div>
        </div>
      </template>

      <div class="model-grid">
        <el-card v-for="model in models" :key="model.id" class="model-card" shadow="hover">
          <div class="model-header">
            <span class="model-name">{{ model.name }}</span>
            <el-tag :type="getStatusType(model.status)" size="small">{{ model.status }}</el-tag>
          </div>
          <div class="model-info">
            <div>类型: {{ getTypeLabel(model.type) }}</div>
            <div>版本: {{ model.current_version }}</div>
            <div>创建时间: {{ model.created_at }}</div>
          </div>
          <div class="model-actions">
            <el-button size="small" @click="viewModel(model)">详情</el-button>
            <el-button size="small" @click="uploadNewVersion(model)">新版本</el-button>
            <el-button size="small" type="danger" @click="deleteModel(model)">删除</el-button>
          </div>
        </el-card>
        <el-empty v-if="models.length === 0" description="暂无模型" />
      </div>
    </el-card>

    <el-dialog v-model="showUploadDialog" title="上传模型" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="uploadForm.type">
            <el-option label="场景模型" value="scene" />
            <el-option label="物理模型" value="physics" />
            <el-option label="RL算法" value="rl_algorithm" />
            <el-option label="奖励函数" value="reward" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadModel" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="模型详情" width="600px">
      <div v-if="selectedModel">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ selectedModel.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ getTypeLabel(selectedModel.type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedModel.status)">{{ selectedModel.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前版本">{{ selectedModel.current_version }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedModel.description }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>版本历史</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="version in versions"
            :key="version.id"
            :timestamp="version.created_at"
            placement="top"
          >
            <el-card shadow="never">
              <div class="version-item">
                <span>v{{ version.version }}</span>
                <div>
                  <el-button size="small" @click="downloadVersion(version)">下载</el-button>
                  <el-button size="small" @click="rollbackVersion(version)">回滚</el-button>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import api from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'

const projectStore = useProjectStore()
const models = ref<any[]>([])
const versions = ref<any[]>([])
const filterType = ref('')
const filterStatus = ref('')
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const selectedModel = ref<any>(null)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)

const uploadForm = ref({
  name: '',
  type: 'scene',
  description: ''
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    active: 'success',
    recommended: 'warning',
    deprecated: 'info',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    scene: '场景模型',
    physics: '物理模型',
    rl_algorithm: 'RL算法',
    reward: '奖励函数'
  }
  return map[type] || type
}

onMounted(async () => {
  await loadModels()
})

watch([filterType, filterStatus], async () => {
  await loadModels()
})

const loadModels = async () => {
  if (!projectStore.currentProject) return
  const params: any = { project_id: projectStore.currentProject.id }
  if (filterType.value) params.type = filterType.value
  if (filterStatus.value) params.status = filterStatus.value

  const response = await api.get('/api/models', { params })
  models.value = response.data.data
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const uploadModel = async () => {
  if (!projectStore.currentProject || !selectedFile.value) return

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('project_id', projectStore.currentProject.id)
    formData.append('name', uploadForm.value.name)
    formData.append('type', uploadForm.value.type)
    formData.append('description', uploadForm.value.description)

    await api.post('/api/models', formData)
    showUploadDialog.value = false
    ElMessage.success('模型上传成功')
    await loadModels()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const viewModel = async (model: any) => {
  selectedModel.value = model
  const response = await api.get(`/api/models/${model.id}/versions`)
  versions.value = response.data.data
  showDetailDialog.value = true
}

const uploadNewVersion = (model: any) => {
  selectedModel.value = model
  showUploadDialog.value = true
}

const downloadVersion = async (version: any) => {
  try {
    const response = await api.get(`/api/models/${selectedModel.value.id}/versions/${version.version}/download`)
    window.open(response.data.data.url, '_blank')
  } catch (error: any) {
    ElMessage.error('下载失败')
  }
}

const rollbackVersion = async (version: any) => {
  await ElMessageBox.confirm(`确定要回滚到版本 ${version.version} 吗？`, '确认')
  await api.post(`/api/models/${selectedModel.value.id}/rollback`, null, {
    params: { version: version.version }
  })
  ElMessage.success('回滚成功')
  showDetailDialog.value = false
  await loadModels()
}

const deleteModel = async (model: any) => {
  await ElMessageBox.confirm('确定要删除该模型吗？', '确认')
  await api.delete(`/api/models/${model.id}`)
  ElMessage.success('删除成功')
  await loadModels()
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.model-card {
  cursor: pointer;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.model-name {
  font-weight: bold;
  font-size: 16px;
}

.model-info {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.model-info div {
  margin-bottom: 5px;
}

.model-actions {
  display: flex;
  gap: 5px;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
