<template>
  <div class="page-pad">
    <!-- 基本信息 -->
    <div class="card">
      <div class="hrow">
        <h4>{{ obj.household?.hz_name || '监测对象' }}</h4>
        <span class="badge" :class="obj.status === '风险已消除' ? 'g' : 'r'">{{ obj.status || '—' }}</span>
      </div>
      <div class="row"><span class="k">身份证</span><span class="v">{{ obj.household?.hz_idcard }}</span></div>
      <div class="row"><span class="k">电话</span><span class="v">{{ obj.household?.phone || '—' }}</span></div>
      <div class="row"><span class="k">住址</span><span class="v">{{ obj.household?.address || '—' }}</span></div>
      <div class="row"><span class="k">监测类别</span><span class="v">{{ obj.monitor_category || '—' }}</span></div>
      <div class="row"><span class="k">风险类型</span><span class="v">{{ obj.risk_type || '—' }}</span></div>
      <div class="row"><span class="k">纳入时间</span><span class="v">{{ obj.start_date || '—' }}</span></div>
      <div class="row" v-if="obj.risk_end_date"><span class="k">风险消除时间</span><span class="v">{{ obj.risk_end_date }}</span></div>
    </div>

    <!-- 走访记录 -->
    <div class="card">
      <div class="hrow">
        <h4>走访记录（{{ obj.visits?.length || 0 }} 次）</h4>
        <button v-if="!isMobile" class="add" @click="openForm">+ 添加走访</button>
      </div>
      <div v-if="!obj.visits?.length" class="empty">暂无走访记录</div>
      <div class="timeline">
        <div v-for="v in obj.visits" :key="v.id" class="tl">
          <span class="dot"></span>
          <div class="body">
            <div class="dt">{{ v.visit_date }} · {{ v.visitor }}
              <button v-if="!isMobile" class="del" @click="delVisit(v)">删除</button>
            </div>
            <div class="tag" v-if="v.risk_change">{{ v.risk_change }}<template v-if="v.need_help"> · 需帮扶</template></div>
            <div class="tx" v-if="v.note">{{ v.note }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作 -->
    <div v-if="!isMobile" class="actions">
      <van-button v-if="obj.status === '风险未消除'" type="primary" @click="resolve">申请风险消除</van-button>
    </div>
    <p v-else class="mobile-note">走访登记、风险消除请在电脑端操作。</p>

    <!-- 添加走访弹窗 -->
    <van-popup v-model:show="showForm" position="bottom" round>
      <div class="form">
        <h4>添加走访记录</h4>
        <van-field v-model="form.visit_date" label="走访时间" type="date" />
        <van-field v-model="form.visitor" label="走访人" placeholder="请输入走访人姓名" />
        <div class="field-label">风险变化</div>
        <van-radio-group v-model="form.risk_change" direction="horizontal" class="radio">
          <van-radio v-for="o in RISK_OPTIONS" :key="o" :name="o">{{ o }}</van-radio>
        </van-radio-group>
        <div class="field-label">是否需帮扶</div>
        <van-radio-group v-model="form.need_help" direction="horizontal" class="radio">
          <van-radio name="否">否</van-radio>
          <van-radio name="是">是</van-radio>
        </van-radio-group>
        <van-field v-model="form.note" label="情况说明" type="textarea" rows="3"
                   autosize placeholder="本次排查情况（选填）" />
        <van-button type="primary" block :loading="saving" @click="saveVisit">保存走访记录</van-button>
      </div>
    </van-popup>
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { api } from '../api'
import { useIsMobile } from '../composables/useIsMobile'
import { usePageMeta } from '../composables/usePageMeta'

const RISK_OPTIONS = ['无变化', '风险上升', '风险下降', '风险消除']

const isMobile = useIsMobile()
const { setTitle } = usePageMeta()
const route = useRoute()
const hid = computed(() => Number(route.params.hid))
const obj = ref({})
const showForm = ref(false)
const saving = ref(false)
const today = new Date().toLocaleDateString('sv-SE')
const form = ref({ visit_date: today, visitor: '', risk_change: '', need_help: '否', note: '' })

function resetForm() {
  form.value = { visit_date: today, visitor: '', risk_change: '', need_help: '否', note: '' }
}
async function load() {
  try {
    obj.value = await api.get(`/api/monitoring/${hid.value}`)
    setTitle(`监测户 · ${obj.value.household?.hz_name || ''}`)
  } catch (e) { showToast(e.message) }
}
function openForm() { resetForm(); showForm.value = true }
async function saveVisit() {
  if (!form.value.visitor.trim()) { showToast('请填写走访人'); return }
  saving.value = true
  try {
    await api.post(`/api/monitoring/${hid.value}/visits`, form.value)
    showToast('已记录')
    showForm.value = false
    await load()
  } catch (e) { showToast(e.message) } finally { saving.value = false }
}
async function delVisit(v) {
  let ok = true
  try { ok = await showConfirmDialog({ title: '确认删除该走访记录？' }) } catch (e) { ok = false }
  if (!ok) return
  await api.del(`/api/monitoring/visits/${v.id}`)
  showToast('已删除')
  await load()
}
async function resolve() {
  let ok = true
  try { ok = await showConfirmDialog({ title: '确认该户风险已消除？', message: '消除后状态将标记为「风险已消除」' }) } catch (e) { ok = false }
  if (!ok) return
  await api.post(`/api/monitoring/${hid.value}/resolve`, { end_date: today })
  showToast('已标记风险消除')
  await load()
}
onMounted(load)
watch(() => route.params.hid, load)
</script>
<style scoped>
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 14px 16px; margin-bottom: 12px; }
.hrow { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.hrow h4 { margin: 0; font-size: 14.5px; }
.row { display: flex; justify-content: space-between; padding: 8px 2px;
       border-bottom: 1px solid var(--line-soft); font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: var(--ink2); } .v { font-weight: 500; text-align: right; }
.badge { font-size: 11px; padding: 2px 10px; border-radius: 999px; }
.badge.r { background: var(--danger-soft); color: var(--danger); }
.badge.g { background: var(--primary-soft); color: var(--primary-deep); }
.add { border: 1px solid var(--primary); color: var(--primary); background: transparent;
       border-radius: 7px; padding: 4px 12px; font-size: 12px; cursor: pointer; }
.empty { font-size: 12.5px; color: var(--ink3); text-align: center; padding: 14px 0; }

.timeline { padding: 8px 2px 2px; }
.tl { position: relative; padding: 0 0 16px 18px; border-left: 2px solid var(--line); }
.tl:last-child { border-left-color: transparent; }
.tl .dot { position: absolute; left: -6px; top: 3px; width: 10px; height: 10px; border-radius: 50%;
           background: var(--primary); border: 2px solid var(--surface); }
.tl .dt { font-size: 12px; color: var(--ink2); display: flex; align-items: center; gap: 8px; }
.tl .del { border: none; background: transparent; color: var(--danger); font-size: 11px; cursor: pointer; padding: 0; }
.tl .tag { display: inline-block; font-size: 11px; color: var(--primary-deep); background: var(--primary-soft);
           border-radius: 4px; padding: 1px 6px; margin-top: 4px; }
.tl .tx { font-size: 12.5px; margin-top: 4px; color: var(--ink); white-space: pre-wrap; }

.actions { display: flex; gap: 8px; margin-top: 4px; }
.mobile-note { font-size: 11.5px; color: var(--ink3); }

.form { padding: 18px 16px 20px; }
.form h4 { margin: 0 0 12px; font-size: 15px; }
.field-label { font-size: 12px; color: var(--ink3); padding: 10px 16px 4px; }
.radio { padding: 0 16px; }
.form .van-button { margin-top: 16px; }
</style>
