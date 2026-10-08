<template>
  <div class="page-pad">
    <template v-if="resident">
      <p class="sec-t">基础信息</p>
      <div class="list">
        <router-link :to="`/ledger/${resident.key}`" class="li">
          <span class="ic">{{ chars[resident.key] }}</span>
          <span class="nm">{{ resident.name }}</span>
          <span class="cnt">{{ count(resident) }}</span>
          <span class="arr">›</span>
        </router-link>
      </div>
    </template>

    <p class="sec-t">户级台账</p>
    <div class="list">
      <router-link v-for="l in householdLedgers" :key="l.key" :to="`/ledger/${l.key}`" class="li">
        <span class="ic">{{ chars[l.key] }}</span>
        <span class="nm">{{ l.name }}</span>
        <span class="cnt">{{ count(l) }}</span>
        <span class="arr">›</span>
      </router-link>
    </div>

    <p class="sec-t">个人台账</p>
    <div class="list">
      <router-link v-for="l in personLedgers" :key="l.key" :to="`/ledger/${l.key}`" class="li">
        <span class="ic">{{ chars[l.key] }}</span>
        <span class="nm">{{ l.name }}</span>
        <span class="cnt">{{ count(l) }}</span>
        <span class="arr">›</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const ledgers = ref([])
const chars = { resident: '居', poverty_alleviated: '脱', monitoring: '监', dibao: '低',
  tekun: '特', disabled: '残', party: '党', veteran: '军', employment: '工',
  medical: '医', pension: '养', subsidy: '补', edu_aid: '教', med_aid: '救' }

const resident = computed(() => ledgers.value.find(l => l.key === 'resident'))
const householdLedgers = computed(() => ledgers.value.filter(l => l.scope === 'household'))
const personLedgers = computed(() => ledgers.value.filter(l => l.scope === 'person' && l.tag_type))

function count(l) {
  return `${l.count ?? 0} ${l.unit}`
}

onMounted(async () => {
  try {
    ledgers.value = await api.get('/api/ledgers')
  } catch (e) { /* ignore：目录页容错，静默降级为空列表 */ }
})
</script>

<style scoped>
.sec-t { font-size: 12px; color: var(--ink3); margin: 6px 2px 10px; }
.list {
  background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
  overflow: hidden; margin-bottom: 16px;
}
.li {
  display: flex; align-items: center; gap: 12px; padding: 13px 14px;
  border-bottom: 1px solid var(--line-soft); text-decoration: none; color: var(--ink);
}
.li:last-child { border-bottom: none; }
.li:active { background: var(--bg); }
.ic {
  width: 36px; height: 36px; border-radius: 9px; background: var(--primary-soft); color: var(--primary);
  display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700; flex-shrink: 0;
}
.nm { font-size: 14px; font-weight: 500; }
.cnt { font-size: 12px; color: var(--ink3); margin-left: auto; font-variant-numeric: tabular-nums; }
.arr { color: #C4C8D0; font-size: 14px; }
</style>
