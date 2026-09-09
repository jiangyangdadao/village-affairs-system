<template>
  <div>
    <div class="red-head">{{ isNew ? '新增' : '编辑' }} · {{ defn.name }}</div>
    <div class="page-pad form-wrap">
      <p v-if="isMobile()" class="mobile-note">请在电脑端进行数据维护。</p>
      <template v-else>
        <van-field v-for="f in allFields" :key="f.key" :label="f.label"
                   :required="f.required" :type="f.kind === 'number' ? 'number' : 'text'"
                   v-model="form[f.key]" :placeholder="f.kind === 'date' ? '如 2020-03-01' : ''" />
        <van-button type="primary" block :loading="saving" @click="save">保存</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api, isMobile } from '../api'

const route = useRoute()
const router = useRouter()
const key = route.params.key
const id = route.params.id ? Number(route.params.id) : null
const isNew = id === null
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const form = ref({})
const saving = ref(false)

const allFields = computed(() => {
  const base = defn.value.scope === 'household'
    ? [{ key: 'hz_name', label: '户主姓名', required: true }, { key: 'hz_idcard', label: '户主身份证', required: true },
       { key: 'phone', label: '联系电话' }, { key: 'address', label: '住址' }]
    : [{ key: 'name', label: '姓名', required: true }, { key: 'idcard', label: '身份证', required: true },
       { key: 'gender', label: '性别' }, { key: 'birth', label: '出生日期', kind: 'date' },
       { key: 'relation', label: '与户主关系' }]
  const tag = defn.value.scope === 'household'
    ? [{ key: 'status', label: '状态' }, { key: 'start_date', label: '纳入时间', kind: 'date' },
       { key: 'end_date', label: '退出时间', kind: 'date' }]
    : [{ key: 'period', label: '年度' }, { key: 'start_date', label: '开始时间', kind: 'date' },
       { key: 'end_date', label: '结束时间', kind: 'date' }]
  return [...base, ...tag, ...defn.value.fields.map(f => ({ ...f }))]
})

async function load() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
  if (!isNew) {
    const r = await api.get(`/api/ledgers/${key}/rows/${id}`)
    form.value = { ...r }
  }
}
async function save() {
  saving.value = true
  try {
    if (isNew) await api.post(`/api/ledgers/${key}/rows`, form.value)
    else await api.put(`/api/ledgers/${key}/rows/${id}`, form.value)
    showToast('已保存')
    router.push(`/ledger/${key}`)
  } catch (e) {
    showToast(e.message)
  } finally {
    saving.value = false
  }
}
onMounted(load)
</script>
<style scoped>
.form-wrap { max-width: 640px; }
.mobile-note { color: #B01B2E; }
</style>
