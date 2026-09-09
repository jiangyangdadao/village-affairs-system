<template>
  <div class="exp-wrap">
    <div class="exp-card">
      <div class="eyebrow">{{ villageName }} · 村务管理系统</div>
      <h2>试用已到期</h2>
      <p v-if="status === 'expired'">试用期已结束。您的数据已<b>完整保留</b>，可随时导出全部台账数据；
        或联系开发者购买后永久激活使用。</p>
      <p v-else-if="status === 'tampered'" class="tampered">检测到系统时间被回拨，已锁定保护数据。请恢复正确时间后重新启动。</p>
      <div class="btns" v-if="status === 'expired'">
        <van-button type="primary" @click="exportAll">导出全部数据 Excel</van-button>
        <van-button @click="contact">联系开发者</van-button>
      </div>
      <div class="act" v-if="status === 'expired'">
        <van-field v-model="code" placeholder="XXXX-XXXX-XXXX-XXXX" label="激活码" />
        <van-button type="primary" block @click="activate">激活（永久解锁）</van-button>
      </div>
      <p class="note">激活码由开发者提供，绑定本机，输入后永久解锁，无需联网。</p>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { api } from '../api'

const villageName = ref('青山村')
const status = ref('expired')
const code = ref('')
function contact() { showToast('开发者微信：cunwu-soft（示例，请替换）') }
function exportAll() { window.open('/api/export-all') }
async function activate() {
  try { await api.post('/api/license/activate', { code: code.value }); location.hash = '#/' }
  catch (e) { showToast(e.message) }
}
onMounted(async () => {
  const st = await api.get('/api/license/status')
  status.value = st.status
  if (st.status === 'active') location.hash = '#/'
})
</script>
<style scoped>
.exp-wrap { display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
.exp-card { width: 480px; background: #fff; border-top: 4px solid #B01B2E; border-radius: 0 0 10px 10px;
            padding: 28px 30px; box-shadow: 0 8px 24px rgba(20,22,18,.1); }
.eyebrow { font-size: 11.5px; letter-spacing: .2em; color: #B01B2E; }
h2 { font-family: "Noto Serif SC", serif; font-size: 24px; margin: 8px 0 12px; }
p { font-size: 13.5px; color: #595D52; line-height: 1.9; }
p b { color: #B01B2E; }
.tampered { color: #B01B2E; }
.btns { display: flex; gap: 10px; margin: 14px 0 18px; }
.act { border-top: 1px solid #E7E8E1; padding-top: 16px; }
.note { font-size: 11.5px; color: #8B8F82; margin-top: 10px; }
</style>
