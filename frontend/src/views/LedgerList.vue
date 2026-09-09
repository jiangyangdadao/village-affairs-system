<template>
  <div>
    <div class="red-head">{{ defn.name }}台账<span class="sub">共 {{ total }} {{ defn.unit }}</span></div>
    <div class="page-pad">
      <van-search v-model="q" placeholder="搜索姓名 / 身份证" @search="load" />
      <div class="chips">
        <span v-for="s in statusOptions" :key="s.value" class="chip"
              :class="{ on: s.value === status }" @click="setStatus(s.value)">{{ s.label }}</span>
      </div>
      <template v-if="!isMobile()">
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
    </div>
    <van-dialog v-model:show="showImport" title="导入 Excel" @confirm="doImport">
      <input type="file" ref="fileInput" accept=".xlsx" class="file-input" @change="onFile" />
    </van-dialog>
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
const q = ref('')
const status = ref('')
const total = ref(0)
const rows = ref([])
const defn = ref({ name: '', unit: '户', scope: 'household', fields: [] })
const showImport = ref(false)
const fileInput = ref(null)
let pickedFile = null

const statusOptions = computed(() => defn.value.scope === 'household' && defn.value.tag_type
  ? [{ label: '全部', value: '' }, { label: '享受中', value: '享受中' }, { label: '已退出', value: '已退出' }]
  : [{ label: '全部', value: '' }])
const tableHeaders = computed(() => {
  const base = defn.value.scope === 'household'
    ? ['户主', '身份证号', '住址', '状态'] : ['姓名', '身份证号', '状态']
  return [...base, ...defn.value.fields.filter(f => ['monthly_amount','member_num','monitor_category','disability_category','disability_level','insured','receive_status','workplace'].includes(f.key)).map(f => f.label)]
})
const headerKeyMap = computed(() => {
  const m = {
    '户主': 'hz_name',
    '身份证号': defn.value.scope === 'household' ? 'hz_idcard' : 'idcard',
    '住址': 'address',
    '状态': 'status',
  }
  for (const f of defn.value.fields) m[f.label] = f.key
  return m
})

function rowTitle(row) { return row.hz_name || row.name || row.id }
function rowSub(row) {
  const parts = []
  if (row.address) parts.push(row.address)
  for (const f of ['monthly_amount', 'member_num', 'disability_level', 'insured', 'workplace']) {
    if (row[f] != null && row[f] !== '') parts.push(`${labelOf(f)} ${row[f]}`)
  }
  return parts.join(' · ') || ' '
}
function labelOf(k) { const f = defn.value.fields.find(x => x.key === k); return f ? f.label : k }

async function load() {
  const data = await api.get(`/api/ledgers/${key}?q=${q.value}&status=${status.value}&page=1&page_size=50`)
  total.value = data.total
  rows.value = data.rows
}
async function loadDefn() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
}
function setStatus(v) { status.value = v; load() }
async function del(row) {
  let ok = true
  try {
    ok = await showConfirmDialog({ title: '确认删除该记录？', message: '删除后可在操作日志中追溯恢复' })
  } catch (e) { ok = false }  // Vant 4 取消时 reject
  if (!ok) return
  await api.del(`/api/ledgers/${key}/rows/${row.id}`)
  showToast('已删除')
  load()
}
function downloadTemplate() { window.open(`/api/ledgers/${key}/template`) }
function exportExcel() { window.open(`/api/ledgers/${key}/export?q=${q.value}&status=${status.value}`) }
function openImport() { showImport.value = true }
function onFile(e) { pickedFile = e.target.files[0] || null }
async function doImport() {
  if (!pickedFile) { showToast('请选择 .xlsx 文件'); return }
  const form = new FormData()
  form.append('file', pickedFile)
  const result = await api.upload(`/api/ledgers/${key}/import`, form)
  showToast(`新增${result.added} 更新${result.updated} 失败${result.failed}`)
  if (result.errors.length) console.warn(result.errors)
  load()
}

onMounted(async () => { await loadDefn(); await load() })
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.chips { display: flex; gap: 8px; margin: 0 4px 12px; }
.chip { font-size: 12px; padding: 3px 12px; border-radius: 999px; background: #fff;
        border: 1px solid #E7E8E1; color: #6B6F64; }
.chip.on { background: #B01B2E; border-color: #B01B2E; color: #fff; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.desk-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: #fff; }
.desk-table th, .desk-table td { padding: 8px 10px; border-bottom: 1px solid #F0F1EC; text-align: left; }
.desk-table th { color: #8B8F82; font-weight: 500; font-size: 11.5px; }
.desk-table tr { cursor: pointer; }
.op { color: #A3771F; margin-right: 8px; }
.op.del { color: #B01B2E; }
.mobile-note { font-size: 11.5px; color: #8B8F82; padding: 8px 4px; }
.file-input { padding: 16px; }
</style>
