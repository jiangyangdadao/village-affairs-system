<template>
  <div>
    <div class="red-head">{{ title }}<span class="sub">详情</span></div>
    <div class="page-pad">
      <div class="card" v-for="(item, i) in infoRows" :key="i">
        <h4>{{ item.title }}</h4>
        <div v-for="r in item.rows" :key="r[0]" class="row"><span class="k">{{ r[0] }}</span><span class="v">{{ r[1] }}</span></div>
      </div>
      <div class="card" v-if="members.length">
        <h4>家庭成员（{{ members.length }} 人）</h4>
        <div v-for="m in members" :key="m.id" class="row"><span class="k">{{ m.name }}</span><span class="v">{{ m.relation }}</span></div>
      </div>
      <div class="card">
        <h4>附件（{{ attachments.length }} 个）</h4>
        <div v-for="a in attachments" :key="a.id" class="row">
          <span class="k">{{ a.filename }}</span>
          <span class="v"><a :href="`/api/attachments/${a.id}`">下载</a>
            <a v-if="!isMobile()" class="del" @click="delAtt(a)">删除</a></span>
        </div>
        <input v-if="!isMobile()" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp"
               class="file-input" @change="uploadAtt" />
      </div>
      <div class="actions" v-if="!isMobile()">
        <van-button v-if="isHousehold" @click="$router.push(`/report/${householdId}`)">户情报告</van-button>
        <van-button @click="$router.push(`/ledger/${key}/${id}/edit`)">编辑</van-button>
        <van-button type="danger" @click="del">删除</van-button>
      </div>
      <p class="mobile-note" v-else>提示：编辑、删除、上传请在电脑端操作。</p>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { api, isMobile } from '../api'

const route = useRoute()
const router = useRouter()
const key = route.params.key
const id = Number(route.params.id)
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const row = ref({})
const members = ref([])
const attachments = ref([])

const title = computed(() => row.value.hz_name || row.value.name || defn.value.name)
const isHousehold = computed(() => defn.value.scope === 'household' && defn.value.tag_type !== null)
const householdId = ref(0)
const infoRows = computed(() => {
  const base = []
  if (row.value.hz_name) base.push({ title: '基本信息', rows: [
    ['户主', row.value.hz_name], ['身份证', row.value.hz_idcard || ''],
    ['电话', row.value.phone || ''], ['住址', row.value.address || '']] })
  if (row.value.name) base.push({ title: '基本信息', rows: [['姓名', row.value.name], ['身份证', row.value.idcard || '']] })
  const tag = []
  if (row.value.status) tag.push(['状态', row.value.status])
  if (row.value.start_date) tag.push(['纳入时间', row.value.start_date])
  if (row.value.period) tag.push(['年度', row.value.period])
  for (const f of defn.value.fields) {
    if (row.value[f.key] != null && row.value[f.key] !== '') tag.push([f.label, row.value[f.key]])
  }
  if (tag.length) base.push({ title: '台账信息', rows: tag })
  return base
})

async function load() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
  const r = await api.get(`/api/ledgers/${key}/rows/${id}`)
  row.value = r
  if (defn.value.scope === 'household' && defn.value.tag_type) {
    // 通过身份证反查户 id：详情接口返回的 tag 行不含 household_id，用列表接口反查
    const list = await api.get(`/api/ledgers/${key}?page=1&page_size=100`)
    const found = list.rows.find(x => x.id === id)
    if (found && found.hz_idcard) {
      const hs = await api.get(`/api/households?q=${encodeURIComponent(found.hz_idcard)}`)
      if (hs.rows.length) {
        householdId.value = hs.rows[0].id
        members.value = await api.get(`/api/households/${householdId.value}/members`)
      }
    }
  }
  attachments.value = await api.get(`/api/attachments?biz_type=household&biz_id=${householdId.value || id}`)
}
async function del() {
  if (!(await showConfirmDialog({ title: '确认删除该记录？' }))) return
  await api.del(`/api/ledgers/${key}/rows/${id}`)
  showToast('已删除')
  router.push(`/ledger/${key}`)
}
async function delAtt(a) {
  await api.del(`/api/attachments/${a.id}`)
  attachments.value = attachments.value.filter(x => x.id !== a.id)
}
async function uploadAtt(e) {
  const f = e.target.files[0]
  if (!f) return
  const form = new FormData()
  form.append('file', f)
  form.append('biz_type', 'household')
  form.append('biz_id', String(householdId.value || id))
  await api.upload('/api/attachments', form)
  showToast('已上传')
  load()
}
onMounted(load)
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.card h4 { margin: 0 0 6px; font-size: 14.5px; }
.row { display: flex; justify-content: space-between; padding: 8px 2px;
       border-bottom: 1px solid #F0F1EC; font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: #6B6F64; } .v { font-weight: 500; text-align: right; }
.actions { display: flex; gap: 8px; }
.del { color: #B01B2E; margin-left: 10px; }
.mobile-note { font-size: 11.5px; color: #8B8F82; }
.file-input { padding: 10px 0; }
</style>
