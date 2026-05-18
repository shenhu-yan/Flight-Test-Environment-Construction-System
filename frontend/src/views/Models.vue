<template>
  <div class="models-page">
    <div class="page-header">
      <h1>模型库</h1>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传模型
      </el-button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <el-select v-model="filterType" placeholder="模型类型" clearable style="width: 160px">
        <el-option label="场景模型" value="scene" />
        <el-option label="物理模型" value="physics" />
        <el-option label="RL算法模型" value="rl_algorithm" />
        <el-option label="奖励函数模型" value="reward" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 140px">
        <el-option label="活跃" value="active" />
        <el-option label="推荐" value="recommended" />
        <el-option label="已弃用" value="deprecated" />
        <el-option label="错误" value="error" />
      </el-select>
      <el-input v-model="searchText" placeholder="搜索模型名称..." clearable prefix-icon="Search" style="width: 280px" />
    </div>

    <!-- Model Cards Grid -->
    <div class="model-grid" v-loading="loading">
      <el-empty v-if="filteredModels.length === 0" description="暂无模型" />
      <div v-for="model in filteredModels" :key="model.id" class="model-card" @click="openDetail(model)">
        <div class="model-card-header">
          <el-tag :type="statusTagType(model.status)" size="small">{{ statusLabel(model.status) }}</el-tag>
          <el-tag v-if="model.status === 'recommended'" type="warning" size="small" effect="dark">推荐</el-tag>
        </div>
        <div class="model-card-icon">
          <el-icon :size="48" color="#0066cc">
            <Box />
          </el-icon>
        </div>
        <div class="model-card-info">
          <h3>{{ model.name }}</h3>
          <p class="model-type">{{ typeLabel(model.type) }}</p>
          <p class="model-version">当前版本: {{ model.current_version }}</p>
          <p class="model-time">{{ formatDate(model.created_at) }}</p>
        </div>
        <div class="model-card-actions">
          <el-button size="small" text @click.stop="downloadModel(model)">
            <el-icon><Download /></el-icon>
          </el-button>
          <el-button size="small" text type="danger" @click.stop="confirmDelete(model)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传模型" width="520px" destroy-on-close>
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="uploadForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="场景模型" value="scene" />
            <el-option label="物理模型" value="physics" />
            <el-option label="RL算法模型" value="rl_algorithm" />
            <el-option label="奖励函数模型" value="reward" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="模型描述" />
        </el-form-item>
        <el-form-item label="模型文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetailDialog" title="模型详情" width="680px" destroy-on-close>
      <template v-if="selectedModel">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ selectedModel.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(selectedModel.type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(selectedModel.status)">{{ statusLabel(selectedModel.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前版本">{{ selectedModel.current_version }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedModel.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedModel.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="version-section">
          <h3>版本历史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="ver in versions"
              :key="ver.id"
              :timestamp="formatDate(ver.created_at)"
              :type="ver.version === selectedModel.current_version ? 'primary' : ''"
              placement="top"
            >
              <div class="version-item">
                <span class="version-tag">{{ ver.version }}</span>
                <el-tag v-if="ver.version === selectedModel.current_version" size="small" type="success">当前</el-tag>
                <span class="version-meta">下载 {{ ver.download_count }} 次</span>
                <el-button size="small" text @click="rollbackVersion(ver)">回滚</el-button>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <div class="version-actions">
          <el-button type="primary" @click="uploadNewVersion">上传新版本</el-button>
          <el-button @click="openDiffDialog">版本对比</el-button>
          <el-button @click="downloadModel(selectedModel)">下载当前版本</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Version Diff Dialog -->
    <el-dialog v-model="showDiffDialog" title="版本对比" width="600px" destroy-on-close>
      <div class="diff-selector">
        <el-select v-model="diffVersion1" placeholder="选择版本A" style="width: 200px">
          <el-option v-for="v in versions" :key="v.id" :label="v.version" :value="v.version" />
        </el-select>
        <span class="diff-vs">VS</span>
        <el-select v-model="diffVersion2" placeholder="选择版本B" style="width: 200px">
          <el-option v-for="v in versions" :key="v.id" :label="v.version" :value="v.version" />
        </el-select>
        <el-button type="primary" @click="compareVersions" :disabled="!diffVersion1 || !diffVersion2">对比</el-button>
      </div>
      <el-table v-if="diffResult" :data="diffResult" border style="margin-top: 16px">
        <el-table-column prop="field" label="字段" width="160" />
        <el-table-column prop="version1" :label="diffVersion1" />
        <el-table-column prop="version2" :label="diffVersion2" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Delete, UploadFilled, Box } from '@element-plus/icons-vue'
import type { ModelItem, ModelVersion } from '../types'
import * as modelsApi from '../api/models'

const loading = ref(false)
const models = ref<ModelItem[]>([])
const versions = ref<ModelVersion[]>([])
const filterType = ref('')
const filterStatus = ref('')
const searchText = ref('')

const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const showDiffDialog = ref(false)
const selectedModel = ref<ModelItem | null>(null)
const uploading = ref(false)
const uploadForm = ref({ name: '', type: 'scene', description: '' })
const uploadFile = ref<File | null>(null)

const diffVersion1 = ref('')
const diffVersion2 = ref('')
const diffResult = ref<{ field: string; version1: string; version2: string }[] | null>(null)

const filteredModels = computed(() => {
  return models.value.filter(m => {
    if (filterType.value && m.type !== filterType.value) return false
    if (filterStatus.value && m.status !== filterStatus.value) return false
    if (searchText.value && !m.name.includes(searchText.value)) return false
    return true
  })
})

function statusTagType(status: string) {
  const map: Record<string, string> = { active: 'success', recommended: 'warning', deprecated: 'info', error: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '活跃', recommended: '推荐', deprecated: '已弃用', error: '错误' }
  return map[status] || status
}

function typeLabel(type: string) {
  const map: Record<string, string> = { scene: '场景模型', physics: '物理模型', rl_algorithm: 'RL算法模型', reward: '奖励函数模型' }
  return map[type] || type
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function loadModels() {
  loading.value = true
  try {
    const res = await modelsApi.getModels({ page: 1, page_size: 100 })
    models.value = res.data?.data || []
  } catch { models.value = [] }
  loading.value = false
}

function handleFileChange(file: any) {
  uploadFile.value = file.raw
}

async function handleUpload() {
  if (!uploadForm.value.name || !uploadFile.value) {
    ElMessage.warning('请填写模型名称并选择文件')
    return
  }
  uploading.value = true
  try {
    await modelsApi.uploadModel(uploadForm.value, uploadFile.value)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { name: '', type: 'scene', description: '' }
    loadModels()
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  }
  uploading.value = false
}

async function openDetail(model: ModelItem) {
  selectedModel.value = model
  showDetailDialog.value = true
  try {
    const res = await modelsApi.getModelVersions(model.id)
    versions.value = res.data?.data || []
  } catch { versions.value = [] }
}

async function downloadModel(model: ModelItem) {
  try {
    const res = await modelsApi.downloadModelVersion(model.id, model.current_version)
    const url = res.data?.data
    if (url) window.open(url, '_blank')
  } catch { ElMessage.error('下载失败') }
}

async function confirmDelete(model: ModelItem) {
  try {
    await ElMessageBox.confirm(`确定删除模型「${model.name}」？`, '确认删除', { type: 'warning' })
    await modelsApi.deleteModel(model.id)
    ElMessage.success('已删除')
    loadModels()
  } catch {}
}

async function rollbackVersion(ver: ModelVersion) {
  if (!selectedModel.value) return
  try {
    await ElMessageBox.confirm(`确定回滚到版本 ${ver.version}？`, '确认回滚', { type: 'warning' })
    await modelsApi.rollbackModel(selectedModel.value.id, ver.version)
    ElMessage.success('回滚成功')
    openDetail(selectedModel.value)
  } catch {}
}

function uploadNewVersion() {
  showUploadDialog.value = true
}

async function openDiffDialog() {
  showDiffDialog.value = true
  diffResult.value = null
}

async function compareVersions() {
  if (!selectedModel.value || !diffVersion1.value || !diffVersion2.value) return
  try {
    const res = await modelsApi.diffVersions(selectedModel.value.id, diffVersion1.value, diffVersion2.value)
    diffResult.value = res.data?.data || []
  } catch { diffResult.value = [] }
}

onMounted(loadModels)
</script>

<style scoped>
.models-page { padding: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 24px; }
.model-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.model-card {
  background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px;
  cursor: pointer; transition: all 0.2s; position: relative;
}
.model-card:hover { border-color: #0066cc; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.model-card-header { display: flex; gap: 8px; margin-bottom: 12px; }
.model-card-icon { text-align: center; margin: 8px 0; }
.model-card-info { text-align: center; }
.model-card-info h3 { margin: 8px 0 4px; font-size: 16px; font-weight: 600; }
.model-type, .model-version, .model-time { font-size: 13px; color: #666; margin: 2px 0; }
.model-card-actions { display: flex; justify-content: center; gap: 8px; margin-top: 12px; }
.version-section { margin-top: 24px; }
.version-section h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.version-item { display: flex; align-items: center; gap: 8px; }
.version-tag { font-weight: 600; }
.version-meta { font-size: 12px; color: #999; margin-left: auto; }
.version-actions { display: flex; gap: 12px; margin-top: 20px; }
.diff-selector { display: flex; align-items: center; gap: 12px; }
.diff-vs { font-weight: 600; color: #666; }
</style>
