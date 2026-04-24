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
          <div class="form-group half"><label>项目</label>
            <select v-model.number="genForm.project_id" required><option value="">请选择项目</option><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.project_name }}</option></select>
          </div>
          <div class="form-group half"><label>环境名称</label><input type="text" v-model="genForm.env_name" required></div>
        </div>
        <div class="form-row">
          <div class="form-group third"><label>模板</label>
            <select v-model="genForm.template_id" @change="loadTemplate"><option value="">自定义配置</option><option v-for="t in templates" :key="t.template_id" :value="t.template_id">{{ t.name }}</option></select>
          </div>
          <div class="form-group third"><label>批量生成数量</label><input type="number" v-model="genForm.batch_count" min="1" max="10"></div>
          <div class="form-group third"><label>描述语言</label>
            <select v-model="genForm.desc_format"><option value="json">JSON</option><option value="xml">XML</option></select>
          </div>
        </div>
        <div class="config-section">
          <h3>环境配置</h3>
          <div class="config-group"><h4>场景配置</h4>
            <div class="form-row">
              <div class="form-group half"><label>地形</label>
                <select v-model="genForm.config.scenario.terrain"><option v-for="o in terrainOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
              </div>
              <div class="form-group half"><label>气象</label>
                <select v-model="genForm.config.scenario.weather"><option v-for="o in weatherOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
              </div>
            </div>
            <div class="form-group"><label>障碍物</label>
              <div class="checkbox-group"><label v-for="o in obstacleOptions" :key="o.value"><input type="checkbox" :value="o.value" v-model="genForm.config.scenario.obstacles">{{ o.label }}</label></div>
            </div>
          </div>
          <div class="config-group"><h4>物理规则</h4>
            <div class="form-row">
              <div class="form-group half"><label>飞行力学</label>
                <select v-model="genForm.config.physics.flight_dynamics"><option v-for="o in dynamicsOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
              </div>
              <div class="form-group half"><label>空气动力学</label>
                <select v-model="genForm.config.physics.aerodynamics"><option v-for="o in aeroOptions" :key="o.value" :value="o.value">{{ o.label }}</option></select>
              </div>
            </div>
          </div>
          <div class="config-group"><h4>奖励函数</h4>
            <div class="form-row">
              <div class="form-group half"><label>奖励值</label><input type="number" v-model.number="genForm.config.reward.reward_value" min="1" max="100"></div>
              <div class="form-group half"><label>目标阈值</label><input type="number" v-model.number="genForm.config.reward.target_threshold" min="0.01" max="1" step="0.01"></div>
            </div>
            <div class="form-group"><label>惩罚规则</label>
              <div class="checkbox-group"><label v-for="r in penaltyOptions" :key="r.value"><input type="checkbox" :value="r.value" v-model="genForm.config.reward.penalty_rules">{{ r.label }}</label></div>
            </div>
          </div>
        </div>
        <div class="form-actions">
          <button type="button" @click="previewConfig" class="btn btn-preview">预览</button>
          <button type="submit" class="btn btn-primary">生成环境</button>
          <button type="button" @click="resetForm" class="btn btn-secondary">重置</button>
        </div>
      </form>
      <div v-if="previewData" class="preview-section">
        <h3>环境预览</h3>
        <div class="preview-grid">
          <div class="preview-card"><h4>场景概要</h4><div class="preview-item"><label>地形:</label><span>{{ previewData.terrain }}</span></div><div class="preview-item"><label>气象:</label><span>{{ previewData.weather }}</span></div><div class="preview-item"><label>障碍物:</label><span>{{ previewData.obstacles }}</span></div></div>
          <div class="preview-card"><h4>物理模型</h4><div class="preview-item"><label>飞行力学:</label><span>{{ previewData.flight_dynamics }}</span></div><div class="preview-item"><label>空气动力学:</label><span>{{ previewData.aerodynamics }}</span></div></div>
          <div class="preview-card"><h4>奖励机制</h4><div class="preview-item"><label>奖励值:</label><span>{{ previewData.reward_value }}</span></div><div class="preview-item"><label>惩罚规则:</label><span>{{ previewData.penalty_rules }}</span></div></div>
          <div class="preview-card highlight"><h4>复杂度评估</h4><div class="complexity-bar"><div class="complexity-fill" :style="{ width: (previewData.complexity * 100) + '%' }"></div></div><span class="complexity-value">{{ (previewData.complexity * 100).toFixed(0) }}%</span></div>
        </div>
      </div>
    </div>
    <div v-if="activeTab === 'templates'" class="tab-content">
      <div class="templates-header"><h3>模板列表</h3><button @click="openCreateTemplateModal" class="btn btn-primary">创建模板</button></div>
      <table class="data-table">
        <thead><tr><th>模板名称</th><th>模板ID</th><th>类型</th><th>复杂度</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="t in templates" :key="t.id"><td>{{ t.name }}</td><td>{{ t.template_id }}</td><td>{{ t.type }}</td><td>{{ t.complexity }}</td>
            <td><button @click="deleteTemplate(t.template_id)" class="btn btn-sm btn-danger">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="activeTab === 'import'" class="tab-content">
      <h3>导入环境描述文件</h3>
      <p class="hint">支持 JSON 和 XML 格式的环境描述文件</p>
      <form @submit.prevent="importEnvironment">
        <div class="form-group"><label>项目</label>
          <select v-model.number="importForm.project_id" required><option value="">请选择项目</option><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.project_name }}</option></select>
        </div>
        <div class="form-group"><label>环境名称</label><input type="text" v-model="importForm.env_name" required></div>
        <div class="form-group"><label>选择文件</label><input type="file" accept=".json,.xml" required></div>
        <div class="form-actions"><button type="submit" class="btn btn-primary">导入</button></div>
      </form>
    </div>
    <div v-if="showCreateTemplateModal" class="modal-overlay" @click.self="showCreateTemplateModal = false">
      <div class="modal-card">
        <div class="modal-header"><h3>创建模板</h3><button @click="showCreateTemplateModal = false" class="close-btn">&times;</button></div>
        <form @submit.prevent="saveTemplate">
          <div class="form-group"><label>模板名称</label><input type="text" v-model="templateForm.name" required></div>
          <div class="form-row">
            <div class="form-group half"><label>类型</label><select v-model="templateForm.type"><option value="fixed_wing">固定翼</option><option value="rotor">旋翼</option><option value="drone">无人机</option></select></div>
            <div class="form-group half"><label>复杂度</label><select v-model="templateForm.complexity"><option value="basic">基础</option><option value="medium">中等</option><option value="advanced">高级</option></select></div>
          </div>
          <div class="modal-footer"><button type="submit" class="btn btn-primary">保存</button><button type="button" @click="showCreateTemplateModal = false" class="btn btn-secondary">取消</button></div>
        </form>
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
      projects: [
        { id: 1, project_name: '无人机避障训练' },
        { id: 2, project_name: '固定翼导航测试' },
        { id: 3, project_name: '旋翼控制优化' }
      ],
      templates: [
        { id: 1, name: '基础旋翼环境', template_id: 'TPL-001', type: 'rotor', complexity: 'basic' },
        { id: 2, name: '中等固定翼环境', template_id: 'TPL-002', type: 'fixed_wing', complexity: 'medium' },
        { id: 3, name: '高级无人机环境', template_id: 'TPL-003', type: 'drone', complexity: 'advanced' }
      ],
      genForm: {
        project_id: '', env_name: '', template_id: '', batch_count: 1, desc_format: 'json',
        config: { scenario: { terrain: 'flat', weather: 'clear', obstacles: [] }, physics: { flight_dynamics: 'basic', aerodynamics: 'basic', collision_detection: 'enabled' }, reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 } }
      },
      terrainOptions: [{ value: 'flat', label: '平坦地形' }, { value: 'hilly', label: '丘陵地形' }, { value: 'mountainous', label: '山地地形' }, { value: 'urban', label: '城市地形' }, { value: 'forest', label: '森林地形' }],
      weatherOptions: [{ value: 'clear', label: '晴朗' }, { value: 'windy', label: '有风' }, { value: 'light_rain', label: '小雨' }, { value: 'heavy_rain', label: '大雨' }, { value: 'storm', label: '风暴' }],
      obstacleOptions: [{ value: 'building', label: '建筑物' }, { value: 'tree', label: '树木' }, { value: 'lamp_post', label: '路灯' }, { value: 'wind_turbine', label: '风力发电机' }, { value: 'power_line', label: '电线' }, { value: 'bird', label: '鸟类' }],
      dynamicsOptions: [{ value: 'basic', label: '基础' }, { value: 'medium', label: '中等' }, { value: 'advanced', label: '高级' }],
      aeroOptions: [{ value: 'basic', label: '基础' }, { value: 'medium', label: '中等' }, { value: 'detailed', label: '详细' }, { value: 'precise', label: '精确' }],
      penaltyOptions: [{ value: 'collision', label: '碰撞' }, { value: 'out_of_bounds', label: '越界' }, { value: 'fault', label: '故障' }, { value: 'timeout', label: '超时' }],
      importForm: { project_id: '', env_name: '' },
      previewData: null,
      showCreateTemplateModal: false,
      templateForm: { name: '', type: 'fixed_wing', complexity: 'basic' }
    }
  },
  methods: {
    loadTemplate() {
      const tpl = this.templates.find(t => t.template_id === this.genForm.template_id)
      if (tpl) {
        const complexityMap = { basic: 'basic', medium: 'medium', advanced: 'advanced' }
        this.genForm.config = { scenario: { terrain: 'flat', weather: 'clear', obstacles: [] }, physics: { flight_dynamics: complexityMap[tpl.complexity] || 'basic', aerodynamics: complexityMap[tpl.complexity] || 'basic', collision_detection: 'enabled' }, reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 } }
      }
    },
    previewConfig() {
      const c = this.genForm.config
      const complexity = ((c.scenario.obstacles.length * 0.1) + (c.physics.flight_dynamics === 'advanced' ? 0.3 : c.physics.flight_dynamics === 'medium' ? 0.15 : 0) + (c.scenario.weather === 'storm' ? 0.3 : c.scenario.weather === 'heavy_rain' ? 0.2 : 0.1) + (c.physics.aerodynamics === 'precise' ? 0.2 : 0.1))
      this.previewData = {
        terrain: this.terrainOptions.find(o => o.value === c.scenario.terrain)?.label || c.scenario.terrain,
        weather: this.weatherOptions.find(o => o.value === c.scenario.weather)?.label || c.scenario.weather,
        obstacles: c.scenario.obstacles.map(o => this.obstacleOptions.find(op => op.value === o)?.label || o).join(', ') || '无',
        flight_dynamics: this.dynamicsOptions.find(o => o.value === c.physics.flight_dynamics)?.label || c.physics.flight_dynamics,
        aerodynamics: this.aeroOptions.find(o => o.value === c.physics.aerodynamics)?.label || c.physics.aerodynamics,
        reward_value: c.reward.reward_value,
        penalty_rules: c.reward.penalty_rules.join(', '),
        complexity: Math.min(complexity, 1)
      }
    },
    generateEnvironment() {
      if (!this.genForm.project_id) { alert('请选择项目'); return }
      alert('环境生成成功！（前端演示，无后端）')
      this.previewData = null
    },
    resetForm() {
      this.genForm = { project_id: '', env_name: '', template_id: '', batch_count: 1, desc_format: 'json', config: { scenario: { terrain: 'flat', weather: 'clear', obstacles: [] }, physics: { flight_dynamics: 'basic', aerodynamics: 'basic', collision_detection: 'enabled' }, reward: { reward_value: 10, penalty_rules: ['collision', 'out_of_bounds'], target_threshold: 0.1 } } }
      this.previewData = null
    },
    importEnvironment() { alert('环境导入成功！（前端演示，无后端）') },
    openCreateTemplateModal() { this.templateForm = { name: '', type: 'fixed_wing', complexity: 'basic' }; this.showCreateTemplateModal = true },
    saveTemplate() {
      this.templates.push({ id: Date.now(), name: this.templateForm.name, template_id: 'TPL-' + String(this.templates.length + 1).padStart(3, '0'), type: this.templateForm.type, complexity: this.templateForm.complexity })
      this.showCreateTemplateModal = false
    },
    deleteTemplate(id) { if (confirm('确定删除模板？')) this.templates = this.templates.filter(t => t.template_id !== id) }
  }
}
</script>

<style scoped>
.env-gen { max-width: 1000px; margin: 0 auto; padding: 24px; }
h2 { color: #1a237e; font-size: 1.5rem; margin-bottom: 16px; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; }
.tab-button { padding: 8px 20px; border: none; background: #e0e0e0; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
.tab-button.active { background: #1a237e; color: white; }
.tab-content { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.form-row { display: flex; gap: 16px; margin-bottom: 0; }
.form-group { margin-bottom: 16px; }
.form-group.half { flex: 1; }
.form-group.third { flex: 1; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #3f51b5; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 12px; }
.checkbox-group label { display: flex; align-items: center; gap: 4px; font-size: 0.85rem; cursor: pointer; }
.config-section { margin: 20px 0; }
.config-section h3 { color: #1a237e; margin-bottom: 12px; font-size: 1.1rem; }
.config-group { background: #fafafa; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.config-group h4 { color: #333; margin-bottom: 10px; font-size: 0.95rem; }
.form-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #1a237e, #283593); color: white; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-preview { background: #0097A7; color: white; }
.btn-sm { padding: 4px 10px; font-size: 0.8rem; }
.btn-danger { background: #d32f2f; color: white; }
.preview-section { margin-top: 24px; padding: 20px; background: #f8f9ff; border-radius: 12px; }
.preview-section h3 { color: #1a237e; margin-bottom: 12px; }
.preview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.preview-card { background: white; border-radius: 8px; padding: 14px; }
.preview-card.highlight { border: 2px solid #1a237e; }
.preview-card h4 { color: #1a237e; margin-bottom: 8px; font-size: 0.9rem; }
.preview-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.85rem; }
.preview-item label { color: #666; }
.complexity-bar { height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; margin: 8px 0; }
.complexity-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #FF9800, #f44336); border-radius: 4px; }
.complexity-value { font-weight: 700; color: #1a237e; }
.templates-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.data-table th { background: #fafafa; font-weight: 600; font-size: 0.85rem; }
.hint { color: #666; font-size: 0.85rem; margin-bottom: 16px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; border-radius: 12px; width: 100%; max-width: 480px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #f0f0f0; }
.modal-header h3 { color: #1a237e; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
form { padding: 24px; }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
</style>
