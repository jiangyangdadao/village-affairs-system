<template>
  <div>
    <div class="page-pad">
      <van-button v-if="!isMobile" size="small" type="primary" @click="editing = {}; showEdit = true">新增项目</van-button>
      <van-loading v-if="loading" size="20" style="margin-bottom:10px">加载中…</van-loading>
      <van-cell-group inset style="margin-top:10px">
        <van-cell v-for="p in list" :key="p.id" :title="p.name"
                  :label="`${p.category} · ${p.progress || '—'} · 投资 ${p.invest_amount || 0} 元`">
          <template #right-icon>
            <span v-if="!isMobile" class="op" @click="editing = { ...p }; showEdit = true">编辑</span>
            <span v-if="!isMobile" class="op del" @click="del(p)">删除</span>
          </template>
        </van-cell>
      </van-cell-group>
      <van-dialog v-model:show="showEdit" title="项目资料" @confirm="save">
        <van-field v-model="editing.name" label="名称" />
        <van-field v-model="editing.category" label="类别" />
        <van-field v-model="editing.invest_amount" label="投资金额(元)" type="number" />
        <van-field v-model="editing.progress" label="进度" />
        <van-field v-model="editing.content" label="建设内容" type="textarea" rows="2" />
      </van-dialog>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { api } from '../api'
import { useIsMobile } from '../composables/useIsMobile'

const isMobile = useIsMobile()
const list = ref([])
const showEdit = ref(false)
const editing = ref({})
const loading = ref(false)
async function load() {
  loading.value = true
  try { list.value = await api.get('/api/projects') }
  catch (e) { showToast(e.message) }
  finally { loading.value = false }
}
async function save() {
  if (editing.value.id) await api.put(`/api/projects/${editing.value.id}`, editing.value)
  else await api.post('/api/projects', editing.value)
  showToast('已保存')
  load()
}
async function del(p) {
  let ok = true
  try {
    ok = await showConfirmDialog({ title: `删除项目「${p.name}」？` })
  } catch (e) { ok = false }  // Vant 4 取消时 reject
  if (!ok) return
  await api.del(`/api/projects/${p.id}`)
  load()
}
onMounted(load)
</script>
<style scoped>
.op { color: #0A7A52; margin-left: 10px; }
.op.del { color: #DC2626; }
</style>
