<template>
  <div>
    <div class="page-pad">
      <div class="count">共 {{ total }} {{ defn.unit }}</div>
      <van-search v-model="q" placeholder="搜索姓名 / 身份证" @search="onSearch" />
      <div class="chips">
        <span v-for="s in statusOptions" :key="s.value" class="chip"
              :class="{ on: s.value === status }" @click="setStatus(s.value)">{{ s.label }}</span>
      </div>
      <template v-if="!isMobile">
        <div class="toolbar">
          <van-button size="small" @click="downloadTemplate">模板下载</van-button>
          <van-button size="small" @click="openImport">导入 Excel</van-button>
          <van-button size="small" @click="exportExcel">导出 Excel</van-button>
          <van-button size="small" type="primary" @click="$router.push(`/ledger/${key}/new`)">新增{{ defn.unit }}</van-button>
        </div>
        <table class="desk-table">
          <thead><tr><th v-for="h in tableHeaders" :key="h">{{ h }}</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" @click="$router.push(`/ledger/${key}/${row.id}`)">
              <td v-for="h in tableHeaders" :key="h">{{ row[headerKeyMap[h]] ?? '' }}</td>
              <td><span class="op" @click.stop="$router.push(`/ledger/${key}/${row.id}/edit`)">编辑</span> <span class="op del" @click.stop="del(row)">删除</span></td>
            </tr>
          </tbody>
        </table>
      </template>
      <template v-else>
        <van-cell-group inset>
          <van-cell v-for="row in rows" :key="row.id" :title="rowTitle(row)"
                    :label="rowSub(row)" is-link @click="$router.push(`/ledger/${key}/${row.id}`)" />
        </van-cell-group>
        <p class="mobile-note">提示：新增、编辑、导入导出请在电脑端操作。</p>
      </template>
      <div class="load-more" v-if="rows.length < total">
        <van-button size="small" plain :loading="loading" @click="loadMore">加载更多</van-button>
      </div>
    </div>
    <van-dialog v-model:show="showImport" title="导入 Excel" @confirm="doImport">
      <input type="file" ref="fileInput" accept=".xlsx" class="file-input" @change="onFile" />
    </van-dialog>
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
const q = ref('')
const status = ref('')
const total = ref(0)
const rows = ref([])
const page = ref(1)
const loading = ref(false)
const PAGE_SIZE = 20
const defn = ref({ name: '', unit: '户', scope: 'household', fields: [] })
const showImport = ref(false)
const fileInput = ref(null)
let pickedFile = null

const statusOptions = computed(() => {
  const opts = defn.value.status_options
  if (opts && opts.length) return [{ label: '全部', value: '' }, ...opts.map(o => ({ label: o, value: o }))]
  return defn.value.scope === 'household' && defn.value.tag_type
    ? [{ label: '全部', value: '' }, { label: '享受中', value: '享受中' }, { label: '已退出', value: '已退出' }]
    : [{ label: '全部', value: '' }]
})
const tableHeaders = computed(() => {
  const base = defn.value.scope === 'household'
    ? ['户主', '身份证号', '住址', '状态'] : ['姓名', '身份证号']
  const showKeys = ['monthly_amount', 'member_num', 'monitor_category', 'risk_type',
    'disability_category', 'disability_level', 'insured', 'receive_status', 'workplace',
    'subsidy_type', 'subsidy_amount', 'pay_status', 'edu_stage', 'aid_amount',
    'disease', 'total_cost', 'self_pay']
  return [...base, ...defn.value.fields.filter(f => showKeys.includes(f.key)).map(f => f.label)]
})
const headerKeyMap = computed(() => {
  const m = {
    '户主': 'hz_name',
    '姓名': 'name',
    '身份证号': defn.value.scope === 'household' ? 'hz_idcard' : 'idcard',
    '住址': 'address',
    '状态': 'status',
  }
  for (const f of defn.value.fields) m[f.label] = f.key
  return m
})

function rowTitle(row) { return row.hz_name || row.name || String(row.id) }
function rowSub(row) {
  const parts = []
  if (row.address) parts.push(row.address)
  for (const f of ['monthly_amount', 'member_num', 'disability_level', 'insured', 'workplace',
    'subsidy_type', 'subsidy_amount', 'pay_status', 'edu_stage', 'aid_amount', 'disease', 'total_cost']) {
    if (row[f] != null && row[f] !== '') parts.push(`${labelOf(f)} ${row[f]}`)
  }
  return parts.join(' · ') || ' '
}
function labelOf(k) { const f = defn.value.fields.find(x => x.key === k); return f ? f.label : k }

async function load(reset = false) {
  if (reset) { page.value = 1; rows.value = [] }
  loading.value = true
  try {
    const data = await api.get(`/api/ledgers/${key.value}?q=${q.value}&status=${status.value}&page=${page.value}&page_size=${PAGE_SIZE}`)
    total.value = data.total
    rows.value = reset ? data.rows : [...rows.value, ...data.rows]
    page.value += 1
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
}
function onSearch() { load(true) }
function loadMore() { load(false) }
async function loadDefn() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key.value) || defn.value
  setTitle(`${defn.value.name}台账`)
}
function setStatus(v) { status.value = v; load(true) }
async function del(row) {
  let ok = true
  try {
    ok = await showConfirmDialog({ title: '确认删除该记录？', message: '删除后可在操作日志中追溯恢复' })
  } catch (e) { ok = false }  // Vant 4 取消时 reject
  if (!ok) return
  await api.del(`/api/ledgers/${key.value}/rows/${row.id}`)
  showToast('已删除')
  load(true)
}
function downloadTemplate() { window.open(`/api/ledgers/${key.value}/template`) }
function exportExcel() { window.open(`/api/ledgers/${key.value}/export?q=${q.value}&status=${status.value}`) }
function openImport() { showImport.value = true }
function onFile(e) { pickedFile = e.target.files[0] || null }
async function doImport() {
  if (!pickedFile) { showToast('请选择 .xlsx 文件'); return }
  const form = new FormData()
  form.append('file', pickedFile)
  const result = await api.upload(`/api/ledgers/${key.value}/import`, form)
  showToast(`新增${result.added} 更新${result.updated} 失败${result.failed}`)
  if (result.errors.length) console.warn(result.errors)
  load(true)
}

watch(() => route.params.key, async () => {
  q.value = ''
  status.value = ''
  await loadDefn()
  await load(true)
}, { immediate: true })
</script>
<style scoped>
.count { font-size: 12px; color: #9BA1AC; margin: 0 4px 10px; }
.chips { display: flex; gap: 8px; margin: 0 4px 12px; }
.chip { font-size: 12px; padding: 3px 12px; border-radius: 999px; background: #fff;
        border: 1px solid #E7E9EE; color: #6A7280; }
.chip.on { background: #0E9F6E; border-color: #0E9F6E; color: #fff; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.desk-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: #fff; }
.desk-table th, .desk-table td { padding: 8px 10px; border-bottom: 1px solid #F0F1F4; text-align: left; }
.desk-table th { color: #9BA1AC; font-weight: 500; font-size: 11.5px; }
.desk-table tr { cursor: pointer; }
.op { color: #0A7A52; margin-right: 8px; }
.op.del { color: #DC2626; }
.mobile-note { font-size: 11.5px; color: #9BA1AC; padding: 8px 4px; }
.load-more { text-align: center; padding: 10px 0; }
.file-input { padding: 16px; }
</style>
