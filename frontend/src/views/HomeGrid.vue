<template>
  <div>
    <div class="red-head">管理首页<span class="sub">{{ villageName }} · 全部模块</span></div>
    <div class="page-pad">
      <div v-if="license.status === 'trial'" class="trial-tip">
        试用期剩余 {{ license.days_left }} 天 · 到期后仍可导出全部数据
      </div>
      <div class="grid">
        <div v-for="t in dataTiles" :key="t.key" class="tile" @click="openLedger(t.key)">
          <span class="ic ic-red">{{ t.char }}</span>
          <span class="n">{{ t.name }}</span>
          <span class="c">{{ t.count }} {{ t.unit }}</span>
        </div>
        <div class="tile" @click="$router.push('/report')"><span class="ic ic-gold">报</span><span class="n">户情报告</span><span class="c">按户生成</span></div>
        <div class="tile" @click="$router.push('/projects')"><span class="ic ic-gold">项</span><span class="n">乡村项目</span><span class="c">资料管理</span></div>
        <div class="tile" @click="$router.push('/audit')"><span class="ic ic-gold">志</span><span class="n">操作日志</span><span class="c">审计留痕</span></div>
        <div class="tile" @click="$router.push('/settings')"><span class="ic ic-gold">设</span><span class="n">系统设置</span><span class="c">备份/海报</span></div>
      </div>
      <div class="recent card">
        <h4>最近操作</h4>
        <div v-for="r in recent" :key="r.id" class="recent-row">
          <span>{{ fmt(r.op_time) }}</span><b>{{ r.op_type }}</b><span>{{ r.module }} {{ r.note }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const villageName = ref('')
const license = ref({ status: 'trial', days_left: 30 })
const stats = ref([])
const recent = ref([])

const CHARS = { resident: '居', poverty_alleviated: '脱', monitoring: '监', dibao: '低',
  tekun: '特', disabled: '残', party: '党', veteran: '军', employment: '工',
  medical: '医', pension: '养' }

const dataTiles = ref([])

function openLedger(key) { router.push(`/ledger/${key}`) }
function fmt(s) { return (s || '').slice(5, 16) }

onMounted(async () => {
  try { villageName.value = (await api.get('/api/me')).village_name } catch (e) { /* ignore */ }
  try { license.value = await api.get('/api/license/status') } catch (e) { /* ignore */ }
  const data = await api.get('/api/stats')
  stats.value = data.ledgers
  recent.value = data.recent
  dataTiles.value = data.ledgers.map(l => ({
    key: l.key, name: l.name, count: l.count, unit: l.unit,
    char: CHARS[l.key] || '册',
  }))
})
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.trial-tip { background: #F7EAE7; color: #B01B2E; border-radius: 8px; padding: 8px 14px;
             font-size: 12.5px; margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.tile { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 12px 4px 10px;
        text-align: center; cursor: pointer; }
.ic { width: 42px; height: 42px; border-radius: 11px; margin: 0 auto 7px; display: flex;
      align-items: center; justify-content: center; font-family: "Noto Serif SC", serif;
      font-size: 19px; font-weight: 700; box-shadow: inset 0 -2px 0 rgba(0,0,0,.18); }
.ic-red { background: #B01B2E; color: #fff; }
.ic-gold { background: #C9A227; color: #fff; }
.n { display: block; font-size: 12px; font-weight: 500; color: #23251F; }
.c { display: block; font-size: 10.5px; color: #8B8F82; margin-top: 1px; font-variant-numeric: tabular-nums; }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 10px; padding: 14px 16px; }
.card h4 { margin: 0 0 10px; font-size: 13.5px; }
.recent-row { display: flex; gap: 12px; font-size: 12.5px; color: #6B6F64;
              padding: 6px 0; border-bottom: 1px solid #F0F1EC; }
.recent-row:last-child { border-bottom: none; }
.recent-row b { color: #B01B2E; }
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(6, 1fr); }
  .n { font-size: 12.5px; }
}
</style>
