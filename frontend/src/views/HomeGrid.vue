<template>
  <div class="page-pad">
    <div v-if="license.status === 'trial'" class="trial-tip">
      试用期剩余 {{ license.days_left }} 天 · 到期后仍可导出全部数据
    </div>

    <!-- 村情速览 -->
    <div class="stats">
      <div class="stat" @click="$router.push('/ledger/resident')">
        <span class="lb">常住人口</span>
        <span class="num">{{ overview.resident ?? '—' }}<small>人</small></span>
      </div>
      <div class="stat" @click="$router.push('/report')">
        <span class="lb">户数</span>
        <span class="num">{{ overview.household ?? '—' }}<small>户</small></span>
      </div>
      <div class="stat hot" @click="$router.push('/monitoring')">
        <span class="lb">监测对象</span>
        <span class="num">{{ overview.monitoring ?? '—' }}<small>户</small></span>
        <span class="dlt" v-if="overview.monitoring_unresolved">{{ overview.monitoring_unresolved }} 户未消除</span>
      </div>
      <div class="stat" @click="$router.push('/ledger/dibao')">
        <span class="lb">低保 · 特困</span>
        <span class="num">{{ overview.dibao_tekun ?? '—' }}<small>户</small></span>
      </div>
    </div>

    <!-- 待办提醒 -->
    <div class="panel">
      <div class="panel-head"><b>待办提醒</b><span v-if="todos.length" class="cnt">{{ todos.length }} 项</span></div>
      <div v-if="!todos.length" class="empty">暂无待办事项</div>
      <div v-for="(t, i) in todos" :key="i" class="todo" @click="openTodo(t)">
        <span class="ic" :class="t.type === 'unresolved' ? 'r' : 'w'">{{ todoChar(t.type) }}</span>
        <span class="tx">{{ t.text }}</span>
        <span class="arr">›</span>
      </div>
    </div>

    <!-- 台账数据概览 -->
    <div class="panel">
      <div class="panel-head"><b>台账数据概览</b></div>
      <div class="bars">
        <div v-for="l in ledgerStats" :key="l.key" class="bar-row">
          <span class="bar-name">{{ l.name }}</span>
          <span class="bar-track"><span class="bar-fill" :style="{ width: barWidth(l.count) }"></span></span>
          <span class="bar-count">{{ l.count }}</span>
        </div>
      </div>
    </div>

    <!-- 最近操作 -->
    <div class="panel">
      <div class="panel-head"><b>最近操作</b></div>
      <div v-if="!recent.length" class="empty">暂无操作记录</div>
      <div v-for="r in recent" :key="r.id" class="recent-row">
        <span class="t">{{ fmt(r.op_time) }}</span>
        <b>{{ r.op_type }}</b>
        <span class="m">{{ r.module }}<template v-if="r.note"> · {{ r.note }}</template></span>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const license = ref({ status: 'trial', days_left: 30 })
const overview = ref({})
const todos = ref([])
const recent = ref([])
const ledgers = ref([])

// 台账数据概览：排除「居民信息」（基础信息），按记录数降序
const ledgerStats = computed(() =>
  ledgers.value.filter(l => l.key !== 'resident').slice().sort((a, b) => b.count - a.count))
const maxLedgerCount = computed(() => Math.max(1, ...ledgerStats.value.map(l => l.count)))
function barWidth(count) { return `${(count / maxLedgerCount.value) * 100}%` }

function fmt(s) { return (s || '').slice(5, 16) }
function todoChar(type) { return { visit: '访', unresolved: '险', medical: '缴' }[type] || '办' }
function openTodo(t) {
  if (t.target) router.push(t.target)
}

onMounted(async () => {
  try { license.value = await api.get('/api/license/status') } catch (e) { /* ignore */ }
  try {
    const data = await api.get('/api/stats')
    overview.value = data.overview || {}
    todos.value = data.todos || []
    recent.value = data.recent || []
    ledgers.value = data.ledgers || []
  } catch (e) { /* 工作台容错，静默降级 */ }
})
</script>
<style scoped>
.trial-tip { background: var(--primary-soft); color: var(--primary-deep); border-radius: 8px;
             padding: 8px 14px; font-size: 12.5px; margin-bottom: 14px; }

/* 村情速览 */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }
.stat { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 14px 16px; cursor: pointer; transition: border-color .15s; }
.stat:hover { border-color: var(--primary); }
.lb { display: block; font-size: 12px; color: var(--ink3); }
.num { display: block; font-size: 26px; font-weight: 800; margin-top: 4px; font-variant-numeric: tabular-nums; }
.num small { font-size: 12px; color: var(--ink3); font-weight: 400; margin-left: 2px; }
.dlt { display: block; font-size: 11px; color: var(--danger); margin-top: 3px; }
.stat.hot .num { color: var(--danger); }

/* 面板 */
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; margin-bottom: 14px; overflow: hidden; }
.panel-head { display: flex; align-items: center; justify-content: space-between;
               padding: 11px 16px; border-bottom: 1px solid var(--line-soft); }
.panel-head b { font-size: 13.5px; }
.cnt { font-size: 11px; color: var(--danger); background: var(--danger-soft); border-radius: 999px; padding: 1px 8px; }
.empty { padding: 16px; font-size: 12.5px; color: var(--ink3); text-align: center; }
.todo { display: flex; align-items: center; gap: 10px; padding: 11px 16px;
        border-bottom: 1px solid var(--line-soft); font-size: 13px; cursor: pointer; }
.todo:last-child { border-bottom: none; }
.todo:hover { background: var(--bg); }
.todo .ic { width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center;
            justify-content: center; font-size: 12px; flex-shrink: 0; }
.todo .ic.w { background: var(--warn-soft); color: var(--warn); }
.todo .ic.r { background: var(--danger-soft); color: var(--danger); }
.todo .tx { flex: 1; }
.todo .arr { color: #C4C8D0; }

/* 台账数据概览条形图 */
.bars { padding: 4px 16px 12px; }
.bar-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.bar-name { width: 80px; flex-shrink: 0; font-size: 12.5px; color: var(--ink);
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 10px; border-radius: 999px; background: var(--line-soft); overflow: hidden; }
.bar-fill { display: block; height: 100%; border-radius: 999px; background: var(--primary); }
.bar-count { width: 30px; flex-shrink: 0; text-align: right; font-size: 12px;
             color: var(--ink2); font-variant-numeric: tabular-nums; }

/* 最近操作 */
.recent-row { display: flex; gap: 10px; align-items: center; padding: 10px 16px;
              border-bottom: 1px solid var(--line-soft); font-size: 12.5px; }
.recent-row:last-child { border-bottom: none; }
.recent-row .t { color: var(--ink3); font-variant-numeric: tabular-nums; flex-shrink: 0; }
.recent-row b { color: var(--primary); }
.recent-row .m { color: var(--ink2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 767px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
