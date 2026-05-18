<template>
  <el-tag :type="tagType" size="small" effect="light">{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const statusMap: Record<string, { type: string; label: string }> = {
  generating: { type: 'warning', label: '生成中' },
  active: { type: 'success', label: '活跃' },
  deprecated: { type: 'info', label: '已弃用' },
  running: { type: 'warning', label: '运行中' },
  completed: { type: 'success', label: '已完成' },
  failed: { type: 'danger', label: '失败' },
  pending: { type: 'info', label: '待处理' },
  stopped: { type: 'info', label: '已停止' },
}

const tagType = computed(() => (statusMap[props.status]?.type || 'info') as any)
const label = computed(() => statusMap[props.status]?.label || props.status)
</script>
