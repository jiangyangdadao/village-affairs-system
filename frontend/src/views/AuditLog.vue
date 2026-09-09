<template>
  <div>
    <div class="red-head">操作日志<span class="sub">审计留痕</span></div>
    <div class="page-pad">
      <van-tabs v-model:active="tab">
        <van-tab title="操作日志">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in audit.items" :key="x.id" :title="`${x.op_type} · ${x.module}`"
                      :label="`${x.op_time} · ${x.note || ''} · IP ${x.ip}`" />
          </van-cell-group>
        </van-tab>
        <van-tab title="导入记录">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in imports.items" :key="x.id" :title="`${x.module} · ${x.filename}`"
                      :label="`${x.import_time} · 新增${x.added_rows} 更新${x.updated_rows} 失败${x.fail_rows}`" />
          </van-cell-group>
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const tab = ref(0)
const audit = ref({ items: [] })
const imports = ref({ items: [] })
onMounted(async () => {
  audit.value = await api.get('/api/audit?page_size=50')
  imports.value = await api.get('/api/imports?page_size=50')
})
</script>
