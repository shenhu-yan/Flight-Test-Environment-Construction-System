<template>
  <div class="models">
    <div class="models-header">
      <h2>模型管理</h2>
      <button @click="openUploadModal" class="button">上传模型</button>
    </div>
    
    <div class="filter-section">
      <select v-model.number="selectedProject" @change="loadModels">
        <option value="">所有项目</option>
        <option v-for="project in projects" :key="project.id" :value="project.id">
          {{ project.project_name }}
        </option>
      </select>
      <select v-model="selectedType" @change="loadModels">
        <option value="">所有类型</option>
        <option value="scenario">场景模型</option>
        <option value="physics">物理模型</option>
        <option value="algorithm">算法模型</option>
      </select>
    </div>
    
    <div class="models-list">
      <table class="models-table">
        <thead>
          <tr>
            <th>模型名称</th>
            <th>模型ID</th>
            <th>项目</th>
            <th>类型</th>
            <th>版本</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="model in models" :key="model.id">
            <td>{{ model.model_name }}</td>
            <td>{{ model.model_id }}</td>
            <td>{{ getProjectName(model.project_id) }}</td>
            <td>{{ model.model_type }}</td>
            <td>{{ model.version }}</td>
            <td>
              <span :class="['status-badge', model.status]">{{ model.status }}</span>
            </td>
            <td class="actions">
              <button @click="downloadModel(model.model_id)" class="action-button download">下载</button>
              <button @click="deleteModel(model.id)" class="action-button delete">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 上传模型模态框 -->
    <div v-if="showUploadModal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>上传模型</h3>
          <button @click="showUploadModal = false" class="close-button">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="uploadModel" enctype="multipart/form-data">
            <div class="form-group">
              <label for="project_id">项目</label>
              <select id="project_id" v-model.number="uploadForm.project_id" required>
                <option value="">请选择项目</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">
                  {{ project.project_name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label for="task_id">任务ID</label>
              <input type="text" id="task_id" v-model="uploadForm.task_id" required>
            </div>
            <div class="form-group">
              <label for="model_type">模型类型</label>
              <select id="model_type" v-model="uploadForm.model_type" required>
                <option value="scenario">场景模型</option>
                <option value="physics">物理模型</option>
                <option value="algorithm">算法模型</option>
              </select>
            </div>
            <div class="form-group">
              <label for="version">版本</label>
              <input type="text" id="version" v-model="uploadForm.version" placeholder="1.0.0">
            </div>
            <div class="form-group">
              <label for="description">描述</label>
              <textarea id="description" v-model="uploadForm.description"></textarea>
            </div>
            <div class="form-group">
              <label for="model_file">模型文件</label>
              <input type="file" id="model_file" ref="fileInput" @change="handleFileChange" required>
            </div>
            <div class="form-actions">
              <button type="submit" class="button">上传</button>
              <button type="button" @click="showUploadModal = false" class="button secondary">取消</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Models',
  data() {
    return {
      models: [],
      projects: [],
      selectedProject: '',
      selectedType: '',
      showUploadModal: false,
      uploadForm: {
        project_id: '',
        task_id: '',
        model_type: 'scenario',
        version: '1.0.0',
        description: '',
        file: null
      }
    }
  },
  mounted() {
    this.loadProjects()
    this.loadModels()
  },
  methods: {
    async loadProjects() {
      try {
        const response = await this.$axios.get('/projects')
        this.projects = response.data
      } catch (error) {
        console.error('加载项目失败:', error)
      }
    },
    async loadModels() {
      try {
        let url = '/models'
        if (this.selectedProject) {
          url += `?project_id=${this.selectedProject}`
        }
        if (this.selectedType) {
          url += `${this.selectedProject ? '&' : '?'}model_type=${this.selectedType}`
        }
        const response = await this.$axios.get(url)
        this.models = response.data
      } catch (error) {
        console.error('加载模型失败:', error)
      }
    },
    getProjectName(projectId) {
      const project = this.projects.find(p => p.id == projectId)
      return project ? project.project_name : '未知项目'
    },
    openUploadModal() {
      this.uploadForm = {
        project_id: '',
        task_id: '',
        model_type: 'scenario',
        version: '1.0.0',
        description: '',
        file: null
      }
      this.showUploadModal = true
    },
    handleFileChange(event) {
      this.uploadForm.file = event.target.files[0]
    },
    async uploadModel() {
      try {
        const formData = new FormData()
        formData.append('project_id', this.uploadForm.project_id)
        formData.append('task_id', this.uploadForm.task_id)
        formData.append('model_type', this.uploadForm.model_type)
        formData.append('version', this.uploadForm.version)
        formData.append('description', this.uploadForm.description)
        formData.append('file', this.uploadForm.file)
        
        await this.$axios.post('/models/mgr/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        this.showUploadModal = false
        this.loadModels()
      } catch (error) {
        console.error('上传模型失败:', error)
      }
    },
    downloadModel(modelId) {
      const token = localStorage.getItem('token')
      const url = `/api/models/mgr/download/${modelId}`
      const link = document.createElement('a')
      link.href = url
      link.target = '_blank'
      const xhr = new XMLHttpRequest()
      xhr.open('GET', url, true)
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.responseType = 'blob'
      xhr.onload = () => {
        if (xhr.status === 200) {
          const blob = xhr.response
          const downloadUrl = window.URL.createObjectURL(blob)
          link.href = downloadUrl
          const disposition = xhr.getResponseHeader('Content-Disposition')
          let filename = 'model'
          if (disposition && disposition.includes('filename=')) {
            filename = disposition.split('filename=')[1].replace(/"/g, '')
          }
          link.download = filename
          link.click()
          window.URL.revokeObjectURL(downloadUrl)
        }
      }
      xhr.send()
    },
    async deleteModel(modelId) {
      if (confirm('确定要删除这个模型吗？')) {
        try {
          await this.$axios.delete(`/models/mgr/delete/${modelId}`)
          this.loadModels()
        } catch (error) {
          console.error('删除模型失败:', error)
        }
      }
    }
  }
}
</script>

<style>
.models {
  max-width: 1200px;
  margin: 0 auto;
}

.models-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.models-header h2 {
  color: #333;
}

.button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #45a049;
}

.button.secondary {
  background-color: #999;
}

.button.secondary:hover {
  background-color: #777;
}

.filter-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.filter-section select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.models-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border-radius: 8px;
  overflow: hidden;
}

.models-table th,
.models-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.models-table th {
  background-color: #f5f5f5;
  font-weight: bold;
  color: #333;
}

.models-table tr:hover {
  background-color: #f9f9f9;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.normal {
  background-color: #e8f5e8;
  color: #388E3C;
}

.status-badge.abnormal {
  background-color: #ffebee;
  color: #D32F2F;
}

.status-badge.deprecated {
  background-color: #fff3e0;
  color: #F57C00;
}

.status-badge.archived {
  background-color: #e3f2fd;
  color: #1976D2;
}

.status-badge.recommended {
  background-color: #e0f7fa;
  color: #0097A7;
}

.actions {
  display: flex;
  gap: 10px;
}

.action-button {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s;
}

.action-button.download {
  background-color: #2196F3;
  color: white;
}

.action-button.download:hover {
  background-color: #1976D2;
}

.action-button.delete {
  background-color: #f44336;
  color: white;
}

.action-button.delete:hover {
  background-color: #d32f2f;
}

/* 模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .models-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .filter-section {
    flex-direction: column;
  }
  
  .models-table {
    font-size: 0.9rem;
  }
  
  .models-table th,
  .models-table td {
    padding: 8px;
  }
  
  .actions {
    flex-direction: column;
    gap: 5px;
  }
}
</style>
