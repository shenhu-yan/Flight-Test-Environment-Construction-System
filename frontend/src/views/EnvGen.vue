<template>
  <div class="env-gen">
    <h2>环境生成</h2>

    <div class="tabs">
      <button :class="['tab-button', { active: activeTab === 'generate' }]" @click="activeTab = 'generate'">生成环境</button>
      <button :class="['tab-button', { active: activeTab === 'templates' }]" @click="activeTab = 'templates'">模板管理</button>
      <button :class="['tab-button', { active: activeTab === 'import' }]" @click="activeTab = 'import'">导入环境</button>
    </div>

    <div v-if="activeTab === 'generate'" class="tab-content">
      <form @submit.prevent="generateEnvironment">
        <div class="form-row">
          <div class="form-group half">
            <label for="project_id">项目</label>
            <select id="project_id" v-model.number="genForm.project_id" required>
              <option value="">请选择项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.project_name }}
              </option>
            </select>
          </div>
          <div class="form-group half">
            <label for="env_name">环境名称</label>
            <input type="text" id="env_name" v-model="genForm.env_name" required>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group third">
            <label for="template_id">模板</label>
            <select id="template_id" v-model="genForm.template_id" @change="loadTemplate">
              <option value="">自定义配置</option>
              <option v-for="template in templates" :key="template.template_id" :value="template.template_id">
                {{ template.name }}
              </option>
            </select>
          </div>
          <div class="form-group third">
            <label for="batch_count">批量生成数量</label>
            <input type="number" id="batch_count" v-model="genForm.batch_count" min="1" max="10">
          </div>
          <div class="form-group third">
            <label for="desc_format">描述语言</label>
            <select id="desc_format" v-model="genForm.desc_format">
              <option value="json">JSON</option>
              <option value="xml">XML</option>
            </select>
          </div>
        </div>

        <div class="config-section">
          <h3>环境配置</h3>

          <div class="config-group">
            <h4>场景配置</h4>
            <div class="form-row">
              <div class="form-group half">
                <label for="terrain">地形</label>
                <select id="terrain" v-model="genForm.config.scenario.terrain">
                  <option v-for="option in terrainOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <div class="form-group half">
                <label for="weather">气象</label>
                <select id="weather" v-model="genForm.config.scenario.weather">
                  <option v-for="option in weatherOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>障碍物</label>
              <div class="checkbox-group">
                <label v-for="obstacle in obstacleOptions" :key="obstacle.value">
                  <input type="checkbox" :value="obstacle.value" v-model="genForm.config.scenario.obstacles">
                  {{ obstacle.label }}
                </label>
              </div>
            </div>
          </div>

          <div class="config-group">
            <h4>物理规则</h4>
            <div class="form-row">
              <div class="form-group half">
                <label for="flight_dynamics">飞行力学</label>
                <select id="flight_dynamics" v-model="genForm.config.physics.flight_dynamics">
                  <option v-for="option in dynamicsOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <div class="form-group half">
                <label for="aerodynamics">空气动力学</label>
                <select id="aerodynamics" v-model="genForm.config.physics.aerodynamics">
                  <option v-for="option in aeroOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label for="collision_detection">碰撞检测</label>
              <select id="collision_detection" v-model="genForm.config.physics.collision_detection">
                <option value="enabled">启用</option>
                <option value="disabled">禁用</option>
              </select>
            </div>
          </div>

          <div class="config-group">
            <h4>奖励函数</h4>
            <div class="form-row">
              <div class="form-group half">
                <label for="reward_value">奖励值</label>
                <input type="number" id="reward_value" v-model.number="genForm.config.reward.reward_value" min="1" max="100">
              </div>
              <div class="form-group half">
                <label for="target_threshold">目标阈值</label>
                <input type="number" id="target_threshold" v-model.number="genForm.config.reward.target_threshold" min="0.01" max="1" step="0.01">
              </div>
            </div>
            <div class="form-group">
              <label>惩罚规则</label>
              <div class="checkbox-group">
                <label v-for="rule in penaltyOptions" :key="rule.value">
                  <input type="checkbox" :value="rule.value" v-model="genForm.config.reward.penalty_rules">
                  {{ rule.label }}
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" @click="previewConfig" class="button preview">预览</button>
          <button type="submit" class="button">生成环境</button>
          <button type="button" @click="resetForm" class="button secondary">重置</button>
        </div>
      </form>

      <div v-if="previewData" class="preview-section">
        <h3>环境预览</h3>
        <div class="preview-grid">
          <div class="preview-card">
            <h4>场景概要</h4>
            <div class="preview-item"><label>地形:</label><span>{{ previewData.summary.terrain }}</span></div>
            <div class="preview-item"><label>气象:</label><span>{{ previewData.summary.weather }}</span></div>
            <div class="preview-item"><label>障碍物数量:</label><span>{{ previewData.summary.obstacle_count }}</span></div>
            <div class="preview-item"><label>障碍物:</label><span>{{ previewData.summary.obstacle_names.join(', ') || '无' }}</span></div>
          </div>
          <div class="preview-card">
            <h4>物理模型</h4>
            <div class="preview-item"><label>飞行力学:</label><span>{{ previewData.summary.flight_dynamics }}</span></div>
            <div class="preview-item"><label>空气动力学:</label><span>{{ previewData.summary.aerodynamics }}</span></div>
          </div>
          <div class="preview-card">
            <h4>奖励机制</h4>
            <div class="preview-item"><label>奖励值:</label><span>{{ previewData.summary.reward_value }}</span></div>
            <div class="preview-item"><label>惩罚规则数:</label><span>{{ previewData.summary.penalty_count }}</span></div>
            <div class="preview-item"><label>目标阈值:</label><span>{{ previewData.summary.target_threshold }}</span></div>
          </div>
          <div class="preview-card highlight">
            <h4>复杂度评估</h4>
            <div class="complexity-bar">
              <div class="complexity-fill" :style="{ width: (previewData.complexity_score * 100) + '%' }"></div>
            </div>
            <span class="complexity-value">{{ (previewData.complexity_score * 100).toFixed(0) }}%</span>
            <p class="scene-desc">{{ previewData.scene_description }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'templates'" class="tab-content">
      <div class="templates-header">
        <h3>模板列表</h3>
        <button @click="openCreateTemplateModal" class="button">创建模板</button>
      </div>

      <div class="templates-list">
        <table class="templates-table">
          <thead>
            <tr>
              <th>模板名称</th>
              <th>模板ID</th>
              <th>类型</th>
              <th>复杂度</th>
              <th>试验类型</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="template in templates" :key="template.id">
              <td>{{ template.name }}</td>
              <td>{{ template.template_id }}</td>
              <td>{{ template.type }}</td>
              <td>{{ template.complexity }}</td>
              <td>{{ template.test_type }}</td>
              <td class="actions">
                <button @click="editTemplate(template)" class="action-button edit">编辑</button>
                <button @click="deleteTemplate(template.template_id)" class="action-button delete">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="activeTab === 'import'" class="tab-content">
      <h3>导入环境描述文件</h3>
      <p class="import-hint">支持 JSON 和 XML 格式的环境描述文件</p>
      <form @submit.prevent="importEnvironment">
        <div class="form-group">
          <label for="import_project_id">项目</label>
          <select id="import_project_id" v-model.number="importForm.project_id" required>
            <option value="">请选择项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.project_name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="import_env_name">环境名称</label>
          <input type="text" id="import_env_name" v-model="importForm.env_name" required>
        </div>
        <div class="form-group">
          <label for="import_file">选择文件</label>
          <input type="file" id="import_file" ref="importFileInput" accept=".json,.xml" required>
        </div>
        <div class="form-actions">
          <button type="submit" class="button">导入</button>
        </div>
      </form>
    </div>

    <div v-if="showCreateTemplateModal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingTemplate ? '编辑模板' : '创建模板' }}</h3>
          <button @click="showCreateTemplateModal = false" class="close-button">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveTemplate">
            <div class="form-group">
              <label for="template_name">模板名称</label>
              <input type="text" id="template_name" v-model="templateForm.name" required>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label for="template_type">类型</label>
                <select id="template_type" v-model="templateForm.type" required>
                  <option value="fixed_wing">固定翼</option>
                  <option value="rotor">旋翼</option>
                  <option value="drone">无人机</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
              <div class="form-group half">
                <label for="template_complexity">复杂度</label>
                <select id="template_complexity" v-model="templateForm.complexity" required>
                  <option value="basic">基础</option>
                  <option value="medium">中等</option>
                  <option value="advanced">高级</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label for="template_test_type">试验类型</label>
              <select id="template_test_type" v-model="templateForm.test_type" required>
                <option value="maneuver">机动飞行</option>
                <option value="fault_simulation">故障模拟</option>
                <option value="environment_adaptation">环境适应</option>
                <option value="general">通用</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="submit" class="button">保存</button>
              <button type="button" @click="showCreateTemplateModal = false" class="button secondary">取消</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EnvGen',
  data() {
    return {
      activeTab: 'generate',
      projects: [],
      templates: [],
      genForm: {
        project_id: '',
        env_name: '',
        template_id: '',
        batch_count: 1,
        desc_format: 'json',
        config: {
          scenario: { terrain: 'flat', weather: 'clear', obstacles: [] },
          physics: { flight_dynamics: 'basic', aerodynamics: 'basic', collision_detection: 'enabled' },
          reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 }
        }
      },
      terrainOptions: [
        { value: 'flat', label: '平坦地形' },
        { value: 'hilly', label: '丘陵地形' },
        { value: 'mountainous', label: '山地地形' },
        { value: 'urban', label: '城市地形' },
        { value: 'forest', label: '森林地形' }
      ],
      weatherOptions: [
        { value: 'clear', label: '晴朗' },
        { value: 'windy', label: '有风' },
        { value: 'light_rain', label: '小雨' },
        { value: 'heavy_rain', label: '大雨' },
        { value: 'storm', label: '风暴' }
      ],
      obstacleOptions: [
        { value: 'building', label: '建筑物' },
        { value: 'tree', label: '树木' },
        { value: 'lamp_post', label: '路灯' },
        { value: 'wind_turbine', label: '风力发电机' },
        { value: 'power_line', label: '电线' },
        { value: 'bird', label: '鸟类' }
      ],
      dynamicsOptions: [
        { value: 'basic', label: '基础' },
        { value: 'medium', label: '中等' },
        { value: 'advanced', label: '高级' }
      ],
      aeroOptions: [
        { value: 'basic', label: '基础' },
        { value: 'medium', label: '中等' },
        { value: 'detailed', label: '详细' },
        { value: 'precise', label: '精确' }
      ],
      penaltyOptions: [
        { value: 'collision', label: '碰撞' },
        { value: 'out_of_bounds', label: '越界' },
        { value: 'fault', label: '故障' },
        { value: 'timeout', label: '超时' }
      ],
      importForm: { project_id: '', env_name: '' },
      previewData: null,
      showCreateTemplateModal: false,
      editingTemplate: false,
      templateForm: { name: '', type: 'fixed_wing', complexity: 'basic', test_type: 'maneuver' }
    }
  },
  mounted() {
    this.loadProjects()
    this.loadTemplates()
    this.loadMetadata()
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
    async loadTemplates() {
      try {
        const response = await this.$axios.get('/env/templates')
        this.templates = response.data
      } catch (error) {
        console.error('加载模板失败:', error)
      }
    },
    async loadMetadata() {
      try {
        const response = await this.$axios.get('/env/metadata')
        const metadata = response.data

        // 更新下拉选项
        if (metadata.terrain_types) {
          this.terrainOptions = metadata.terrain_types.map(t => ({
            value: t.value,
            label: t.name
          }))
        }

        if (metadata.weather_types) {
          this.weatherOptions = metadata.weather_types.map(w => ({
            value: w.value,
            label: w.name
          }))
        }

        if (metadata.obstacle_types) {
          this.obstacleOptions = metadata.obstacle_types.map(o => ({
            value: o.value,
            label: o.name
          }))
        }

        if (metadata.dynamics_types) {
          this.dynamicsOptions = metadata.dynamics_types.map(d => ({
            value: d.value,
            label: d.name
          }))
        }

        if (metadata.aero_types) {
          this.aeroOptions = metadata.aero_types.map(a => ({
            value: a.value,
            label: a.name
          }))
        }
      } catch (error) {
        console.error('加载元数据失败:', error)
      }
    },
    async loadTemplate() {
      if (this.genForm.template_id) {
        try {
          const response = await this.$axios.get(`/env/templates/${this.genForm.template_id}`)
          if (response.data.config) {
            this.genForm.config = JSON.parse(JSON.stringify(response.data.config))
          }
        } catch (error) {
          console.error('加载模板配置失败:', error)
        }
      }
    },
    async previewConfig() {
      try {
        const response = await this.$axios.post('/environments/preview-config', {
          config: this.genForm.config
        })
        this.previewData = response.data.preview
      } catch (error) {
        console.error('预览失败:', error)
        alert(error.response?.data?.error || '预览失败')
      }
    },
    async generateEnvironment() {
      if (!this.genForm.project_id) {
        alert('请选择项目')
        return
      }
      try {
        await this.$axios.post('/env/generate', this.genForm)
        alert('环境生成成功')
        this.previewData = null
        this.resetForm()
      } catch (error) {
        console.error('生成环境失败:', error)
        alert(error.response?.data?.error || '生成环境失败')
      }
    },
    resetForm() {
      this.genForm = {
        project_id: '',
        env_name: '',
        template_id: '',
        batch_count: 1,
        desc_format: 'json',
        config: {
          scenario: { terrain: 'flat', weather: 'clear', obstacles: [] },
          physics: { flight_dynamics: 'basic', aerodynamics: 'basic', collision_detection: 'enabled' },
          reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 }
        }
      }
    },
    async importEnvironment() {
      if (!this.$refs.importFileInput.files[0]) {
        alert('请选择文件')
        return
      }
      try {
        const formData = new FormData()
        formData.append('file', this.$refs.importFileInput.files[0])
        formData.append('project_id', this.importForm.project_id)
        formData.append('env_name', this.importForm.env_name)
        await this.$axios.post('/env/import', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        alert('环境导入成功')
        this.importForm = { project_id: '', env_name: '' }
      } catch (error) {
        console.error('导入环境失败:', error)
        alert(error.response?.data?.error || '导入环境失败')
      }
    },
    openCreateTemplateModal() {
      this.editingTemplate = false
      this.templateForm = { name: '', type: 'fixed_wing', complexity: 'basic', test_type: 'maneuver' }
      this.showCreateTemplateModal = true
    },
    editTemplate(template) {
      this.editingTemplate = true
      this.templateForm = { ...template }
      this.showCreateTemplateModal = true
    },
    async saveTemplate() {
      try {
        if (this.editingTemplate) {
          await this.$axios.put(`/env/templates/${this.templateForm.template_id}`, this.templateForm)
        } else {
          await this.$axios.post('/env/templates', this.templateForm)
        }
        this.showCreateTemplateModal = false
        this.loadTemplates()
        alert('模板保存成功')
      } catch (error) {
        console.error('保存模板失败:', error)
        alert(error.response?.data?.error || '保存模板失败')
      }
    },
    async deleteTemplate(templateId) {
      if (confirm('确定要删除这个模板吗？')) {
        try {
          await this.$axios.delete(`/env/templates/${templateId}`)
          this.loadTemplates()
        } catch (error) {
          console.error('删除模板失败:', error)
          alert(error.response?.data?.error || '删除模板失败')
        }
      }
    }
  }
}
</script>

<style scoped>
.env-gen { max-width: 1200px; margin: 0 auto; padding: 24px; }
.env-gen h2 { margin-bottom: 20px; color: #1a237e; }
.tabs { display: flex; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
.tab-button { padding: 10px 24px; border: none; background: none; cursor: pointer; font-size: 15px; border-bottom: 3px solid transparent; transition: all 0.2s; color: #666; }
.tab-button:hover { background-color: #f5f5f5; }
.tab-button.active { border-bottom-color: #1a237e; color: #1a237e; font-weight: 600; }
.tab-content { background-color: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.form-group { margin-bottom: 15px; }
.form-row { display: flex; gap: 15px; margin-bottom: 15px; }
.form-group.half { flex: 1; }
.form-group.third { flex: 1; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 15px; transition: border-color 0.2s; }
.form-group input:focus, .form-group select:focus { border-color: #1a237e; outline: none; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 12px; }
.checkbox-group label { display: flex; align-items: center; gap: 5px; font-weight: normal; cursor: pointer; font-size: 0.9rem; }
.config-section { margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }
.config-section h3 { margin-bottom: 15px; color: #1a237e; }
.config-group { margin-bottom: 20px; padding: 16px; background-color: #f8f9fa; border-radius: 8px; }
.config-group h4 { margin-bottom: 10px; color: #555; font-size: 0.95rem; }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.button { background-color: #1a237e; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; transition: background-color 0.2s; font-size: 0.9rem; }
.button:hover { background-color: #283593; }
.button.preview { background-color: #FF9800; }
.button.preview:hover { background-color: #F57C00; }
.button.secondary { background-color: #999; }
.button.secondary:hover { background-color: #777; }
.preview-section { margin-top: 24px; padding: 20px; background-color: #f0f2f5; border-radius: 12px; }
.preview-section h3 { margin-bottom: 16px; color: #1a237e; }
.preview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.preview-card { background-color: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.preview-card h4 { margin-bottom: 12px; color: #333; font-size: 0.95rem; border-bottom: 1px solid #eee; padding-bottom: 8px; }
.preview-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.9rem; }
.preview-item label { color: #666; }
.preview-item span { color: #333; font-weight: 500; }
.preview-card.highlight { border: 2px solid #1a237e; }
.complexity-bar { height: 8px; background-color: #e0e0e0; border-radius: 4px; margin: 8px 0; overflow: hidden; }
.complexity-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #FF9800, #f44336); border-radius: 4px; transition: width 0.3s; }
.complexity-value { font-size: 1.2rem; font-weight: 700; color: #1a237e; }
.scene-desc { margin-top: 8px; color: #666; font-size: 0.9rem; line-height: 1.5; }
.templates-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.templates-header h3 { color: #333; }
.templates-table { width: 100%; border-collapse: collapse; }
.templates-table th, .templates-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.templates-table th { background-color: #f5f5f5; font-weight: 600; color: #333; }
.templates-table tr:hover { background-color: #f9f9f9; }
.actions { display: flex; gap: 8px; }
.action-button { padding: 5px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; transition: background-color 0.2s; }
.action-button.edit { background-color: #2196F3; color: white; }
.action-button.edit:hover { background-color: #1976D2; }
.action-button.delete { background-color: #f44336; color: white; }
.action-button.delete:hover { background-color: #d32f2f; }
.import-hint { color: #666; margin-bottom: 16px; font-size: 0.9rem; }
.modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background-color: white; padding: 24px; border-radius: 12px; width: 100%; max-width: 500px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h3 { color: #333; }
.close-button { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
@media (max-width: 768px) { .form-row { flex-direction: column; } .preview-grid { grid-template-columns: 1fr; } }
</style>
