<template>
  <div>
    <div class="page-pad form-wrap">
      <p v-if="isMobile" class="mobile-note">请在电脑端进行数据维护。</p>
      <template v-else>
        <template v-for="f in allFields" :key="f.key">
          <van-field v-if="f.kind === 'select'" :label="f.label" :required="f.required"
                     :model-value="form[f.key]" readonly is-link placeholder="请选择"
                     @click="openPicker(f)" />
          <van-field v-else-if="f.kind === 'date'" :label="f.label" :required="f.required"
                     :model-value="form[f.key]" readonly is-link placeholder="如 2020-03-01"
                     @click="openDatePicker(f)" />
          <van-field v-else :label="f.label" :required="f.required"
                     :type="f.kind === 'number' ? 'number' : 'text'" v-model="form[f.key]" />
        </template>
        <van-popup v-model:show="showPicker" position="bottom" round>
          <van-picker :columns="pickerColumns" @confirm="onPickerConfirm" @cancel="showPicker = false" />
        </van-popup>
        <van-popup v-model:show="showDatePicker" position="bottom" round>
          <van-date-picker v-model="datePickerValue" :min-date="minDate" :max-date="maxDate"
                           @confirm="onDateConfirm" @cancel="showDatePicker = false" />
        </van-popup>
        <van-button type="primary" block :loading="saving" @click="save">保存</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../api'
import { useIsMobile } from '../composables/useIsMobile'
import { usePageMeta } from '../composables/usePageMeta'

const isMobile = useIsMobile()
const { setTitle } = usePageMeta()
const route = useRoute()
const router = useRouter()
const key = computed(() => route.params.key || '')
const id = computed(() => route.params.id ? Number(route.params.id) : null)
const isNew = computed(() => id.value === null)
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const form = ref({})
const saving = ref(false)
const showPicker = ref(false)
const showDatePicker = ref(false)
const pickerField = ref(null)
const pickerColumns = ref([])
const datePickerField = ref(null)
const datePickerValue = ref(['2020', '01', '01'])
const minDate = new Date(1900, 0, 1)
const maxDate = new Date(2100, 11, 31)

function openPicker(f) {
  pickerField.value = f
  pickerColumns.value = (f.options || []).map(o => ({ text: o, value: o }))
  showPicker.value = true
}
function onPickerConfirm({ selectedOptions }) {
  form.value[pickerField.value.key] = selectedOptions[0].value
  showPicker.value = false
}
function openDatePicker(f) {
  datePickerField.value = f
  const v = form.value[f.key]
  datePickerValue.value = v ? String(v).slice(0, 10).split('-') : ['2020', '01', '01']
  showDatePicker.value = true
}
function onDateConfirm({ selectedValues }) {
  form.value[datePickerField.value.key] = selectedValues.join('-')
  showDatePicker.value = false
}

const allFields = computed(() => {
  const isResident = defn.value.scope === 'person' && defn.value.tag_type === null
  const base = defn.value.scope === 'household'
    ? [{ key: 'hz_name', label: '户主姓名', required: true }, { key: 'hz_idcard', label: '户主身份证', required: true },
       { key: 'phone', label: '联系电话' }, { key: 'address', label: '住址' }]
    : [
        ...(isResident ? [{ key: 'hz_idcard', label: '户主身份证' }] : []),
        { key: 'name', label: '姓名', required: true }, { key: 'idcard', label: '身份证', required: true },
        { key: 'gender', label: '性别' }, { key: 'birth', label: '出生日期', kind: 'date' },
        { key: 'relation', label: '与户主关系' },
      ]
  const tag = defn.value.scope === 'household'
    ? [{ key: 'status', label: '状态' }, { key: 'start_date', label: '纳入时间', kind: 'date' },
       { key: 'end_date', label: '退出时间', kind: 'date' }]
    : [{ key: 'period', label: '年度' }, { key: 'start_date', label: '开始时间', kind: 'date' },
       { key: 'end_date', label: '结束时间', kind: 'date' }]
  return [...base, ...tag, ...defn.value.fields.map(f => ({ ...f }))]
})

async function load() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key.value) || defn.value
  if (!isNew.value) {
    const r = await api.get(`/api/ledgers/${key.value}/rows/${id.value}`)
    form.value = { ...r }
  }
  setTitle(`${isNew.value ? '新增' : '编辑'} · ${defn.value.name}`)
}
async function save() {
  for (const f of allFields.value) {
    if (f.required && (form.value[f.key] == null || form.value[f.key] === '')) {
      showToast(`请填写${f.label}`)
      return
    }
  }
  saving.value = true
  try {
    if (isNew.value) await api.post(`/api/ledgers/${key.value}/rows`, form.value)
    else await api.put(`/api/ledgers/${key.value}/rows/${id.value}`, form.value)
    showToast('已保存')
    router.push(`/ledger/${key.value}`)
  } catch (e) {
    showToast(e.message)
  } finally {
    saving.value = false
  }
}
watch(() => [route.params.key, route.params.id], () => {
  form.value = {}
  load()
}, { immediate: true })
</script>
<style scoped>
.form-wrap { max-width: 640px; }
.mobile-note { color: #9BA1AC; }
</style>
