<template>
  <div class="config-panel">
    <el-collapse v-model="activeNames">
      <el-collapse-item title="🌍 地形配置" name="terrain">
        <el-form-item label="地形类型">
          <el-select v-model="config.terrain.type" style="width:100%">
            <el-option label="平原" value="plain" />
            <el-option label="山地" value="mountain" />
            <el-option label="丘陵" value="hill" />
            <el-option label="海洋" value="ocean" />
            <el-option label="沙漠" value="desert" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低高度 (m)">
          <el-input-number v-model="config.terrain.elevation_min" :min="0" :max="5000" />
        </el-form-item>
        <el-form-item label="最高高度 (m)">
          <el-input-number v-model="config.terrain.elevation_max" :min="0" :max="10000" />
        </el-form-item>
        <el-form-item label="分辨率">
          <el-input-number v-model="config.terrain.resolution" :min="1" :max="100" />
        </el-form-item>
      </el-collapse-item>

      <el-collapse-item title="🌤️ 天气配置" name="weather">
        <el-form-item label="风速 (m/s)">
          <el-slider v-model="config.weather.wind_speed" :min="0" :max="50" show-input />
        </el-form-item>
        <el-form-item label="风向 (°)">
          <el-slider v-model="config.weather.wind_direction" :min="0" :max="360" show-input />
        </el-form-item>
        <el-form-item label="能见度 (km)">
          <el-slider v-model="config.weather.visibility" :min="0.1" :max="50" :step="0.1" show-input />
        </el-form-item>
      </el-collapse-item>

      <el-collapse-item title="✈️ 飞行动力学" name="dynamics">
        <el-form-item label="机型">
          <el-input v-model="config.flight_dynamics.aircraft_model" />
        </el-form-item>
        <el-form-item label="质量 (kg)">
          <el-input-number v-model="config.flight_dynamics.mass" :min="100" :max="100000" />
        </el-form-item>
        <el-form-item label="翼展 (m)">
          <el-input-number v-model="config.flight_dynamics.wingspan" :min="1" :max="100" :step="0.1" />
        </el-form-item>
      </el-collapse-item>

      <el-collapse-item title="⚙️ 奖励配置" name="rewards">
        <div v-for="(item, i) in config.rewards.reward_items" :key="i" class="reward-row">
          <el-input v-model="item.name" placeholder="奖励名称" style="width:40%" />
          <el-input-number v-model="item.coefficient" :min="0" :max="10" :step="0.1" style="width:30%" />
          <el-button type="danger" text @click="config.rewards.reward_items.splice(i, 1)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-button size="small" @click="config.rewards.reward_items.push({ name: '', coefficient: 1.0 })">
          + 添加奖励项
        </el-button>
      </el-collapse-item>

      <el-collapse-item title="🚧 障碍物配置" name="obstacles">
        <el-form-item label="障碍物数量">
          <el-input-number v-model="config.obstacles.count" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="密度">
          <el-slider v-model="config.obstacles.density" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="类型">
          <el-checkbox-group v-model="config.obstacles.types">
            <el-checkbox label="building">建筑</el-checkbox>
            <el-checkbox label="tree">树木</el-checkbox>
            <el-checkbox label="tower">塔架</el-checkbox>
            <el-checkbox label="powerline">电力线</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import type { EnvConfig } from '../../types'

const props = defineProps<{ config: EnvConfig }>()

const activeNames = ref(['terrain', 'weather'])
</script>

<style scoped>
.config-panel {
  padding: 8px 0;
}
.reward-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
