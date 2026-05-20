<template>
  <div class="env-card" @click="$emit('click')">
    <div class="card-header">
      <h3 class="card-title">{{ env.name }}</h3>
      <StatusTag :status="env.status" />
    </div>
    <div class="card-meta">
      <div class="meta-row" v-if="env.config?.weather">
        <span class="meta-label">风速</span>
        <span class="meta-value">{{ env.config.weather.wind_speed }} m/s</span>
      </div>
      <div class="meta-row" v-if="env.config?.terrain">
        <span class="meta-label">地形</span>
        <span class="meta-value">{{ env.config.terrain.type }}</span>
      </div>
      <div class="meta-row" v-if="env.config?.obstacles">
        <span class="meta-label">障碍物</span>
        <span class="meta-value">{{ env.config.obstacles.count }} 个</span>
      </div>
    </div>
    <div class="card-footer">
      <span class="created-at">{{ formatDate(env.created_at) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusTag from '../common/StatusTag.vue'
import type { FlightEnv } from '../../types'

defineProps<{ env: FlightEnv }>()
defineEmits(['click'])

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.env-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.env-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  border-color: var(--border);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}
.card-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.meta-label { color: var(--text-muted); }
.meta-value { color: var(--text-primary); font-weight: 500; }
.card-footer {
  border-top: 1px solid var(--border-light);
  padding-top: 8px;
}
.created-at {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
