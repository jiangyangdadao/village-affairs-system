<template>
  <div class="login-wrap">
    <div class="logo">村</div>
    <div class="title">村务管理系统</div>
    <div class="sub">{{ villageName }} · 数据存储于村内电脑</div>
    <van-field v-model="password" type="password" placeholder="请输入管理密码" class="pw" />
    <van-button type="primary" block round :loading="loading" @click="login">登录</van-button>
    <p class="note">仅供村务工作人员使用，所有操作将被记录。</p>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../api'

const router = useRouter()
const password = ref('')
const loading = ref(false)
const villageName = ref('青山村')

async function login() {
  loading.value = true
  try {
    await api.post('/api/login', { password: password.value })
    const me = await api.get('/api/me')
    villageName.value = me.village_name
    router.push('/')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.login-wrap { max-width: 360px; margin: 12vh auto 0; padding: 0 20px; text-align: center; }
.logo { width: 56px; height: 56px; border-radius: 14px; background: #B01B2E; color: #fff;
        margin: 0 auto 14px; display: flex; align-items: center; justify-content: center;
        font-family: "Noto Serif SC", serif; font-size: 22px; font-weight: 700; }
.title { font-size: 17px; font-weight: 700; }
.sub { font-size: 12px; color: #8B8F82; margin: 4px 0 20px; }
.pw { border: 1px solid #DFE1D8; border-radius: 10px; margin-bottom: 14px; background: #fff; }
.note { font-size: 11.5px; color: #8B8F82; margin-top: 16px; }
</style>
