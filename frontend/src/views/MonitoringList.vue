<template>
  <div class="page-pad">
    <div class="chips">
      <span v-for="s in statusOptions" :key="s.value" class="chip"
            :class="{ on: s.value === status }" @click="setStatus(s.value)">{{ s.label }}</span>
    </div>
    <p v-if="!isMobile && !rows.length" class="empty">暂无监测对象</p>

    <template v-if="!isMobile">
      <table class="desk-table">
        <thead><tr><th></th><th>户主</th><th>监测类别</th><th>风险类型</th><th>上次走访</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.household_id" @click="$router.push(`/monitoring/${r.household_id}`)">
            <td><span v-if="r.visit_overdue" class="dot-r" title="走访逾期"></span></td>
            <td class="hz">{{ r.hz_name }}<div class="sub">{{ r.hz_idcard }}</div></td>
            <td>{{ r.monitor_category }}</td>
            <td>{{ r.risk_type || '—' }}</td>
            <td>{{ r.last_visit_date || '从未走访' }}</td>
            <td><span class="badge" :class="r.status === '风险已消除' ? 'g' : 'r'">{{ r.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </template>
    <template v-else>
      <div v-for="r in rows" :key="r.household_id" class="mrow" @click="$router.push(`/monitoring/${r.household_id}`)">
        <span class="dot-r" :class="{ g: !r.visit_overdue }"></span>
        <div class="inf">
          <b>{{ r.hz_name }}</b>
          <div class="sub">{{ r.monitor_category }} · {{ r.risk_type || '未填风险类型' }}</div>
          <div class="sub">上次走访 {{ r.last_visit_date || '从未' }}</div>
        </div>
        <span class="badge" :class="r.status === '风险已消除' ? 'g' : 'r'">{{ r.status }}</span>
      </div>
      <p v-if="!rows.length" class="empty">暂无监测对象</p>
    </template>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { useIsMobile } from '../composables/useIsMobile'
import { usePageMeta } from '../composables/usePageMeta'

const isMobile = useIsMobile()
const { setTitle } = usePageMeta()
const status = ref('')
const rows = ref([])
const statusOptions = [
  { label: '全部', value: '' },
  { label: '风险未消除', value: '风险未消除' },
  { label: '风险已消除', value: '风险已消除' },
]

async function load() {
  setTitle('防返贫监测')
  try { rows.value = await api.get(`/api/monitoring/objects?status=${status.value}`) } catch (e) { /* 容错 */ }
}
function setStatus(v) { status.value = v; load() }
onMounted(load)
</script>
<style scoped>
.chips { display: flex; gap: 8px; margin: 0 4px 12px; }
.chip { font-size: 12px; padding: 3px 12px; border-radius: 999px; background: var(--surface);
        border: 1px solid var(--line); color: var(--ink2); cursor: pointer; }
.chip.on { background: var(--primary); border-color: var(--primary); color: #fff; }
.empty { font-size: 12.5px; color: var(--ink3); text-align: center; padding: 24px 0; }

.desk-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: var(--surface);
              border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.desk-table th, .desk-table td { padding: 10px 12px; border-bottom: 1px solid var(--line-soft); text-align: left; }
.desk-table th { color: var(--ink3); font-weight: 500; font-size: 11.5px; background: var(--bg); }
.desk-table tbody tr { cursor: pointer; }
.desk-table tbody tr:hover { background: var(--bg); }
.desk-table tbody tr:last-child td { border-bottom: none; }
.hz { font-weight: 600; }
.hz .sub { font-weight: 400; font-size: 11px; color: var(--ink3); }
.dot-r { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--danger); }
.dot-r.g { background: var(--primary); }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 999px; }
.badge.r { background: var(--danger-soft); color: var(--danger); }
.badge.g { background: var(--primary-soft); color: var(--primary-deep); }

.mrow { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 12px 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; }
.mrow .inf { flex: 1; }
.mrow .inf b { font-size: 14px; }
.mrow .inf .sub { font-size: 11px; color: var(--ink3); margin-top: 2px; }
</style>
