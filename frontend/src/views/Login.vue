<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="23" stroke="#0066cc" stroke-width="2"/>
            <path d="M16 28L24 16L32 28" stroke="#0066cc" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 32h24" stroke="#0066cc" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h1 class="login-title">飞行试验环境构建系统</h1>
        <p class="login-subtitle">Flight Test Environment Construction System</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #1d1d1f;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 48px 40px 40px;
  width: 400px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.3);
}
.logo-area {
  text-align: center;
  margin-bottom: 36px;
}
.logo-icon {
  margin-bottom: 20px;
}
.login-title {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0 0 8px;
  color: #1d1d1f;
}
.login-subtitle {
  font-size: 14px;
  color: #86868b;
  margin: 0;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 9999px !important;
  font-size: 16px;
  font-weight: 500;
  background: #0066cc !important;
  border-color: #0066cc !important;
}
.login-btn:hover {
  background: #0052a3 !important;
  border-color: #0052a3 !important;
}
</style>
