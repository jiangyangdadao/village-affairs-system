<template>
  <div>
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
            <a v-if="!isMobile" class="del" @click="delAtt(a)">删除</a></span>
        </div>
        <input v-if="!isMobile" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp"
               class="file-input" @change="uploadAtt" />
      </div>
      <div class="actions" v-if="!isMobile">
        <van-button v-if="isHousehold" @click="$router.push(`/report/${householdId}`)">户情报告</van-button>
        <van-button @click="$router.push(`/ledger/${key}/${id}/edit`)">编辑</van-button>
        <van-button type="danger" @click="del">删除</van-button>
      </div>
      <p class="mobile-note" v-else>提示：编辑、删除、上传请在电脑端操作。</p>
    </div>
  </div>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { api } from '../api'
import { useIsMobile } from '../composables/useIsMobile'
import { usePageMeta } from '../composables/usePageMeta'

const isMobile = useIsMobile()
const { setTitle } = usePageMeta()
const route = useRoute()
const router = useRouter()
const key = computed(() => route.params.key || '')
const id = computed(() => Number(route.params.id))
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const row = ref({})
const members = ref([])
const attachments = ref([])

const title = computed(() => row.value.hz_name || row.value.name || defn.value.name)
const isHousehold = computed(() => defn.value.scope === 'household' && defn.value.tag_type !== null)
const householdId = ref(0)
// 附件归属：户级台账挂到户，个人（含居民信息/个人标签）挂到人
const bizType = computed(() => defn.value.scope === 'household' ? 'household' : 'person')
const bizId = computed(() => {
  if (defn.value.scope === 'household') return row.value.household_id || 0
  return row.value.person_id || row.value.id || 0
})
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
  defn.value = all.find(l => l.key === key.value) || defn.value
  const r = await api.get(`/api/ledgers/${key.value}/rows/${id.value}`)
  row.value = r
  householdId.value = r.household_id || 0
  members.value = householdId.value
    ? await api.get(`/api/households/${householdId.value}/members`)
    : []
  attachments.value = await api.get(`/api/attachments?biz_type=${bizType.value}&biz_id=${bizId.value}`)
  setTitle(title.value)
}
async function del() {
  let ok = true
  try {
    ok = await showConfirmDialog({ title: '确认删除该记录？' })
  } catch (e) { ok = false }  // Vant 4 取消时 reject
  if (!ok) return
  await api.del(`/api/ledgers/${key.value}/rows/${id.value}`)
  showToast('已删除')
  router.push(`/ledger/${key.value}`)
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
  form.append('biz_type', bizType.value)
  form.append('biz_id', String(bizId.value))
  await api.upload('/api/attachments', form)
  showToast('已上传')
  load()
}
watch(() => [route.params.key, route.params.id], load, { immediate: true })
</script>
<style scoped>
.card { background: #fff; border: 1px solid #E7E9EE; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.card h4 { margin: 0 0 6px; font-size: 14.5px; }
.row { display: flex; justify-content: space-between; padding: 8px 2px;
       border-bottom: 1px solid #F0F1F4; font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: #6A7280; } .v { font-weight: 500; text-align: right; }
.actions { display: flex; gap: 8px; }
.del { color: #DC2626; margin-left: 10px; }
.mobile-note { font-size: 11.5px; color: #9BA1AC; }
.file-input { padding: 10px 0; }
</style>
