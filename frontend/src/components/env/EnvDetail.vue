<template>
  <el-dialog v-model="visible" :title="env?.name || '环境详情'" width="600px" @close="$emit('update:modelValue', false)">
    <div v-if="env" class="env-detail">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="ID">{{ env.id }}</el-descriptions-item>
        <el-descriptions-item label="状态"><StatusTag :status="env.status" /></el-descriptions-item>
        <el-descriptions-item label="风速">{{ env.config?.weather?.wind_speed }} m/s</el-descriptions-item>
        <el-descriptions-item label="风向">{{ env.config?.weather?.wind_direction }}°</el-descriptions-item>
        <el-descriptions-item label="能见度">{{ env.config?.weather?.visibility }} km</el-descriptions-item>
        <el-descriptions-item label="地形">{{ env.config?.terrain?.type }}</el-descriptions-item>
        <el-descriptions-item label="高度范围">{{ env.config?.terrain?.elevation_min }}-{{ env.config?.terrain?.elevation_max }}m</el-descriptions-item>
        <el-descriptions-item label="障碍物">{{ env.config?.obstacles?.count }} 个</el-descriptions-item>
        <el-descriptions-item label="航点数">{{ env.config?.waypoints?.length || 0 }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(env.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
      <el-button type="primary" @click="$emit('adjust', env)">调整</el-button>
      <el-button type="success" @click="$emit('evaluate', env)">评估</el-button>
      <el-button @click="$emit('export', env)">导出</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StatusTag from '../common/StatusTag.vue'
import type { FlightEnv } from '../../types'

const props = defineProps<{
  modelValue: boolean
  env: FlightEnv | null
}>()

defineEmits(['update:modelValue', 'adjust', 'evaluate', 'export'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => {}
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.env-detail {
  padding: 8px 0;
}
</style>
