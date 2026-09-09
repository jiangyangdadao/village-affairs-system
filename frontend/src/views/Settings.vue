<template>
  <div>
    <div class="red-head">系统设置</div>
    <div class="page-pad form-wrap">
      <div class="card"><h4>修改管理密码</h4>
        <van-field v-model="oldPw" type="password" label="原密码" />
        <van-field v-model="newPw" type="password" label="新密码(≥8位)" />
        <van-button size="small" type="primary" @click="changePw">修改</van-button>
      </div>
      <div class="card"><h4>授权状态</h4>
        <p class="info">状态：{{ licText[lic.status] }}<template v-if="lic.status === 'trial'">（剩余 {{ lic.days_left }} 天）</template></p>
        <p class="info">机器指纹：<code>{{ lic.fingerprint }}</code>（购买激活码时发给开发者）</p>
        <van-field v-if="lic.status !== 'active'" v-model="code" placeholder="XXXX-XXXX-XXXX-XXXX" label="激活码" />
        <van-button v-if="lic.status !== 'active'" size="small" type="primary" @click="activate">激活</van-button>
      </div>
      <div class="card"><h4>访问海报与二维码</h4>
        <img :src="'/api/qr'" alt="访问二维码" class="qr" />
        <p class="info">当前地址：http://{{ info.lan_ip }}:{{ info.port }}</p>
        <van-button size="small" @click="downloadPoster">生成使用海报 PDF</van-button>
      </div>
      <div class="card"><h4>数据备份</h4>
        <van-button size="small" type="primary" @click="backup">立即备份</van-button>
        <van-cell-group style="margin-top:8px">
          <van-cell v-for="b in backups" :key="b.filename" :title="b.filename"
                    :label="`${(b.size / 1024 / 1024).toFixed(1)} MB`" />
        </van-cell-group>
        <p class="info">另可双击安装目录下的 备份.bat 手动备份；恢复操作请联系开发者远程协助。</p>
      </div>
      <div class="card"><h4>村情简介</h4>
        <van-field v-model="intro" label="简介" type="textarea" rows="3" autosize />
        <van-field v-model="phone" label="联系电话" />
        <van-button size="small" type="primary" @click="saveProfile">保存</van-button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { api } from '../api'

const oldPw = ref(''); const newPw = ref('')
const lic = ref({ status: '', fingerprint: '', days_left: 0 })
const code = ref('')
const info = ref({ lan_ip: '', port: 8080 })
const backups = ref([])
const intro = ref(''); const phone = ref('')

const licText = { trial: '试用中', active: '已激活', expired: '已到期', tampered: '异常（时间被回拨）' }

async function changePw() {
  try { await api.post('/api/change-password', { old_password: oldPw.value, new_password: newPw.value }); showToast('已修改') }
  catch (e) { showToast(e.message) }
}
async function activate() {
  try { await api.post('/api/license/activate', { code: code.value }); showToast('已永久激活'); load() }
  catch (e) { showToast(e.message) }
}
function downloadPoster() { window.open('/api/poster') }
async function backup() {
  const r = await api.post('/api/backup')
  showToast(`备份完成 ${r.filename}`)
  backups.value = await api.get('/api/backups')
}
async function saveProfile() {
  await api.put('/api/village-profile', { intro: intro.value, phone: phone.value })
  showToast('已保存')
}
async function load() {
  lic.value = await api.get('/api/license/status')
  info.value = await api.get('/api/system/info')
  backups.value = await api.get('/api/backups')
  const p = await api.get('/api/village-profile')
  intro.value = p.intro; phone.value = p.phone
}
onMounted(load)
</script>
<style scoped>
.form-wrap { max-width: 640px; }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.card h4 { margin: 0 0 10px; font-size: 14px; }
.info { font-size: 12.5px; color: #6B6F64; margin: 6px 0; }
.qr { width: 140px; height: 140px; display: block; margin: 6px 0; background: #fff; }
code { font-size: 12px; }
</style>
