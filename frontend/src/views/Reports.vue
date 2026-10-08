<template>
  <div class="page-pad">
    <div class="toolbar">
      <span class="hint">迎检报表 · 数据实时汇总</span>
      <van-button size="small" plain @click="print">打印 / 导出 PDF</van-button>
    </div>

    <!-- 防返贫监测 -->
    <div class="card">
      <h3>防返贫监测</h3>
      <div class="kpis">
        <div class="kpi"><span class="n">{{ d.monitoring?.total ?? 0 }}</span><span class="l">监测对象总数</span></div>
        <div class="kpi hot"><span class="n">{{ d.monitoring?.unresolved ?? 0 }}</span><span class="l">风险未消除</span></div>
        <div class="kpi ok"><span class="n">{{ d.monitoring?.resolved ?? 0 }}</span><span class="l">风险已消除</span></div>
      </div>
      <table v-if="d.monitor_by_category?.length">
        <tr><th>监测类别</th><th>户数</th></tr>
        <tr v-for="c in d.monitor_by_category" :key="c.category"><td>{{ c.category }}</td><td>{{ c.count }}</td></tr>
      </table>
    </div>

    <!-- 低保 / 特困保障 -->
    <div class="card">
      <h3>低保 · 特困保障</h3>
      <table>
        <tr><th>项目</th><th>户数</th><th>保障人数</th><th>月保障金（元）</th></tr>
        <tr><td>低保</td><td>{{ d.relief?.dibao_households ?? 0 }}</td>
          <td>{{ d.relief?.dibao_members ?? 0 }}</td><td>{{ d.relief?.dibao_monthly ?? 0 }}</td></tr>
        <tr><td>特困供养</td><td>{{ d.relief?.tekun_households ?? 0 }}</td>
          <td>—</td><td>{{ d.relief?.tekun_monthly ?? 0 }}</td></tr>
      </table>
    </div>

    <!-- 惠民补贴发放 -->
    <div class="card">
      <h3>惠民补贴发放汇总</h3>
      <table v-if="d.subsidy_by_type?.length">
        <tr><th>补贴类型</th><th>笔数</th><th>金额合计（元）</th></tr>
        <tr v-for="s in d.subsidy_by_type" :key="s.type">
          <td>{{ s.type }}</td><td>{{ s.count }}</td><td>{{ s.amount }}</td>
        </tr>
      </table>
      <p v-else class="empty">暂无补贴发放记录</p>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { usePageMeta } from '../composables/usePageMeta'

const { setTitle } = usePageMeta()
const d = ref({})

function print() { window.print() }

onMounted(async () => {
  setTitle('统计报表')
  try { d.value = await api.get('/api/reports/summary') } catch (e) { /* 容错 */ }
})
</script>
<style scoped>
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.hint { font-size: 12px; color: var(--ink3); }

.card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 16px 18px; margin-bottom: 14px; }
.card h3 { margin: 0 0 12px; font-size: 15px; border-left: 3px solid var(--primary); padding-left: 8px; }

.kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
.kpi { background: var(--bg); border-radius: 10px; padding: 12px; text-align: center; }
.kpi .n { display: block; font-size: 24px; font-weight: 800; font-variant-numeric: tabular-nums; }
.kpi .l { display: block; font-size: 11px; color: var(--ink3); margin-top: 2px; }
.kpi.hot .n { color: var(--danger); }
.kpi.ok .n { color: var(--primary); }

table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th, td { border: 1px solid var(--line); padding: 7px 10px; text-align: left; font-variant-numeric: tabular-nums; }
th { background: var(--bg); color: var(--ink2); font-weight: 500; }
.empty { font-size: 12.5px; color: var(--ink3); text-align: center; padding: 12px 0; }

@media (max-width: 767px) {
  .kpis { grid-template-columns: repeat(3, 1fr); gap: 6px; }
  .card { padding: 14px; }
}
</style>
