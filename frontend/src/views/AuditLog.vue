<template>
  <div>
    <div class="page-pad">
      <van-tabs v-model:active="tab">
        <van-tab title="操作日志">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in audit.items" :key="x.id" :title="`${x.op_type} · ${x.module}`"
                      :label="`${x.op_time} · ${x.note || ''} · IP ${x.ip}`" />
          </van-cell-group>
          <div class="load-more" v-if="audit.items.length < audit.total">
            <van-button size="small" plain :loading="audit.loading" @click="loadAudit()">加载更多</van-button>
          </div>
        </van-tab>
        <van-tab title="导入记录">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in imports.items" :key="x.id" :title="`${x.module} · ${x.filename}`"
                      :label="`${x.import_time} · 新增${x.added_rows} 更新${x.updated_rows} 失败${x.fail_rows}`" />
          </van-cell-group>
          <div class="load-more" v-if="imports.items.length < imports.total">
            <van-button size="small" plain :loading="imports.loading" @click="loadImports()">加载更多</van-button>
          </div>
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { api } from '../api'

const tab = ref(0)
const audit = ref({ items: [], total: 0, page: 1, loading: false })
const imports = ref({ items: [], total: 0, page: 1, loading: false })
const PAGE_SIZE = 50

async function loadAudit(reset = false) {
  const s = audit.value
  if (reset) { s.page = 1; s.items = [] }
  s.loading = true
  try {
    const d = await api.get(`/api/audit?page=${s.page}&page_size=${PAGE_SIZE}`)
    s.total = d.total
    s.items = reset ? d.items : [...s.items, ...d.items]
    s.page += 1
  } catch (e) {
    showToast(e.message)
  } finally {
    s.loading = false
  }
}
async function loadImports(reset = false) {
  const s = imports.value
  if (reset) { s.page = 1; s.items = [] }
  s.loading = true
  try {
    const d = await api.get(`/api/imports?page=${s.page}&page_size=${PAGE_SIZE}`)
    s.total = d.total
    s.items = reset ? d.items : [...s.items, ...d.items]
    s.page += 1
  } catch (e) {
    showToast(e.message)
  } finally {
    s.loading = false
  }
}
onMounted(() => { loadAudit(true); loadImports(true) })
</script>
<style scoped>
.load-more { text-align: center; padding: 10px 0; }
</style>
