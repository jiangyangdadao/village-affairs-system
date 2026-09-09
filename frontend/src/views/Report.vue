<template>
  <div>
    <div class="red-head">户情报告<span class="sub">自动聚合自各台账</span></div>
    <div class="page-pad">
      <template v-if="!hid">
        <van-search v-model="q" placeholder="搜索户主姓名 / 身份证" @search="loadHouses" />
        <van-cell-group inset>
          <van-cell v-for="h in houses" :key="h.id" :title="h.hz_name"
                    :label="h.address" is-link @click="$router.push(`/report/${h.id}`)" />
        </van-cell-group>
      </template>
      <template v-else>
        <div class="report">
          <div class="rhead"><h3>青 山 村 户 情 报 告</h3><p>生成时间：{{ now }}</p></div>
          <h4>一、户基本信息</h4>
          <table><tr><th>户主</th><td>{{ data.household?.hz_name }}</td>
            <th>电话</th><td>{{ data.household?.phone }}</td></tr>
            <tr><th>住址</th><td>{{ data.household?.address }}</td>
            <th>人数</th><td>{{ data.household?.member_count }}</td></tr></table>
          <h4>二、家庭成员</h4>
          <table><tr><th>姓名</th><th>关系</th><th>性别</th><th>出生日期</th></tr>
            <tr v-for="m in data.members" :key="m.id"><td>{{ m.name }}</td><td>{{ m.relation }}</td>
              <td>{{ m.gender }}</td><td>{{ m.birth }}</td></tr></table>
          <h4>三、政策享受清单</h4>
          <table><tr><th>类别</th><th>状态</th><th>纳入时间</th><th>金额/说明</th></tr>
            <tr v-for="t in data.household_tags" :key="t.id">
              <td>{{ tagName(t.tag_type) }}</td><td>{{ t.status }}</td><td>{{ t.start_date }}</td>
              <td>{{ extraText(t.extra) }}</td></tr></table>
          <h4>四、收入合计（月）</h4>
          <div class="sum">合计 {{ data.income_summary?.total || 0 }} 元</div>
        </div>
        <van-button type="primary" block @click="exportPdf">导出 PDF</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const hid = computed(() => route.params.hid ? Number(route.params.hid) : 0)
const q = ref('')
const houses = ref([])
const data = ref({})
const now = new Date().toISOString().slice(0, 10)

function tagName(t) {
  return { dibao: '低保户', tekun: '特困供养户', monitoring: '监测户',
           poverty_alleviated: '脱贫户' }[t] || t
}
function extraText(e) { return Object.entries(e || {}).map(([k, v]) => `${k}=${v}`).join('；') }
async function loadHouses() {
  houses.value = (await api.get(`/api/households?q=${q.value}&page_size=50`)).rows
}
function exportPdf() { window.open(`/api/households/${hid.value}/report.pdf`) }
onMounted(async () => {
  if (hid.value) data.value = await api.get(`/api/households/${hid.value}/report`)
  else await loadHouses()
})
</script>
<style scoped>
.report { background: #fff; border: 1px solid #E2E3DA; padding: 22px; margin-bottom: 14px; }
.rhead { border-top: 3px solid #B01B2E; padding-top: 10px; text-align: center; margin-bottom: 14px; }
.rhead h3 { margin: 0; font-family: "Noto Serif SC", serif; font-size: 20px; letter-spacing: .3em; }
.rhead p { margin: 4px 0 0; font-size: 11px; color: #8B8F82; }
h4 { border-left: 3px solid #B01B2E; padding-left: 8px; font-size: 13.5px; margin: 14px 0 6px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px; }
th, td { border: 1px solid #D8DAD1; padding: 5px 8px; text-align: left; color: #3A3D34; }
th { background: #F4F5F1; color: #595D52; font-weight: 500; }
.sum { background: #F7EAE7; border-radius: 8px; padding: 10px 14px; color: #8A3A2C; font-size: 12.5px; }
</style>
