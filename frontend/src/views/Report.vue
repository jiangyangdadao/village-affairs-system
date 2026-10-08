<template>
  <div>
    <div class="page-pad">
      <template v-if="!hid">
        <van-search v-model="q" placeholder="搜索户主姓名 / 身份证" @search="onSearch" />
        <van-cell-group inset>
          <van-cell v-for="h in houses" :key="h.id" :title="h.hz_name"
                    :label="h.address" is-link @click="$router.push(`/report/${h.id}`)" />
        </van-cell-group>
        <div class="load-more" v-if="houses.length < total">
          <van-button size="small" plain :loading="loading" @click="loadMore">加载更多</van-button>
        </div>
      </template>
      <template v-else>
        <div class="report">
          <div class="rhead"><h3>{{ villageName }} 户 情 报 告</h3><p>生成时间：{{ now }}</p></div>
          <h4>一、户基本信息</h4>
          <div class="tbl-wrap"><table><tr><th>户主</th><td>{{ data.household?.hz_name }}</td>
            <th>电话</th><td>{{ data.household?.phone }}</td></tr>
            <tr><th>住址</th><td>{{ data.household?.address }}</td>
            <th>人数</th><td>{{ data.household?.member_count }}</td></tr></table></div>
          <h4>二、家庭成员</h4>
          <div class="tbl-wrap"><table><tr><th>姓名</th><th>关系</th><th>性别</th><th>出生日期</th></tr>
            <tr v-for="m in data.members" :key="m.id"><td>{{ m.name }}</td><td>{{ m.relation }}</td>
              <td>{{ m.gender }}</td><td>{{ m.birth }}</td></tr></table></div>
          <h4>三、政策享受清单</h4>
          <div class="tbl-wrap"><table><tr><th>类别</th><th>状态</th><th>纳入时间</th><th>金额/说明</th></tr>
            <tr v-for="t in data.household_tags" :key="t.id">
              <td>{{ tagName(t.tag_type) }}</td><td>{{ t.status }}</td><td>{{ t.start_date }}</td>
              <td>{{ extraText(t.extra) }}</td></tr></table></div>
          <h4>四、收入合计（月）</h4>
          <div class="sum">合计 {{ data.income_summary?.total || 0 }} 元</div>
        </div>
        <van-button type="primary" block @click="exportPdf">导出 PDF</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../api'

const route = useRoute()
const hid = computed(() => route.params.hid ? Number(route.params.hid) : 0)
const q = ref('')
const houses = ref([])
const data = ref({})
const now = new Date().toLocaleDateString('sv-SE')  // 本地日期 YYYY-MM-DD，避免 UTC 跨日偏移
const villageName = ref('青山村')
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const PAGE_SIZE = 50

function tagName(t) {
  return { dibao: '低保户', tekun: '特困供养户', monitoring: '监测户',
           poverty_alleviated: '脱贫户' }[t] || t
}
function extraText(e) { return Object.entries(e || {}).map(([k, v]) => `${k}=${v}`).join('；') }
async function loadVillageName() {
  try { villageName.value = (await api.get('/api/village-profile')).village_name || '青山村' } catch (e) { /* ignore */ }
}
async function loadHouses(reset) {
  if (reset) { page.value = 1; houses.value = [] }
  loading.value = true
  try {
    const d = await api.get(`/api/households?q=${q.value}&page=${page.value}&page_size=${PAGE_SIZE}`)
    total.value = d.total
    houses.value = reset ? d.rows : [...houses.value, ...d.rows]
    page.value += 1
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
}
function onSearch() { loadHouses(true) }
function loadMore() { loadHouses(false) }
function exportPdf() { window.open(`/api/households/${hid.value}/report.pdf`) }
async function loadReport() {
  if (hid.value) {
    try { data.value = await api.get(`/api/households/${hid.value}/report`) } catch (e) { showToast(e.message) }
  } else {
    loadHouses(true)
  }
}
onMounted(() => { loadVillageName(); loadReport() })
// 列表→详情在同一个组件实例内切换（router-view 复用），onMounted 不会重跑：
// 必须监听路由参数重新加载，否则预览页空白
watch(() => route.params.hid, loadReport)
</script>
<style scoped>
.report { background: #fff; border: 1px solid #E7E9EE; padding: 22px; margin-bottom: 14px; }
.rhead { border-top: 3px solid #0E9F6E; padding-top: 10px; text-align: center; margin-bottom: 14px; }
.rhead h3 { margin: 0; font-size: 20px; letter-spacing: .3em; }
.rhead p { margin: 4px 0 0; font-size: 11px; color: #9BA1AC; }
h4 { border-left: 3px solid #0E9F6E; padding-left: 8px; font-size: 13.5px; margin: 14px 0 6px; }
.tbl-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px; }
th, td { border: 1px solid #E7E9EE; padding: 5px 8px; text-align: left; color: #1C1F26; }
th { background: #F4F6F8; color: #6A7280; font-weight: 500; }
.sum { background: #E2F5EC; border-radius: 8px; padding: 10px 14px; color: #0A7A52; font-size: 12.5px; }
.load-more { text-align: center; padding: 10px 0; }
@media (max-width: 767px) {
  .report { padding: 14px 12px; }
  .rhead h3 { font-size: 18px; }
}
</style>
