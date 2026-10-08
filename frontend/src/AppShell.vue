<template>
  <div class="shell">
    <!-- 电脑端侧边栏 -->
    <aside v-if="!isMobile" class="sidebar">
      <div class="logo">
        <span class="mark">村</span>
        <span class="nm">村务管理系统</span>
      </div>
      <nav class="nav">
        <router-link to="/" class="it" :class="{ on: navKey === 'home' }">
          <span class="dot">台</span>工作台
        </router-link>
        <div class="grp">
          <p class="grp-t">数据</p>
          <router-link to="/ledger" class="it" :class="{ on: ledgerCenterOn }">
            <span class="dot">册</span>台账中心
          </router-link>
        </div>
        <div class="grp">
          <p class="grp-t">监测与帮扶</p>
          <router-link to="/monitoring" class="it" :class="{ on: navKey === 'monitoring' }">
            <span class="dot">防</span>防返贫监测
          </router-link>
          <div class="sub">
            <router-link to="/ledger/subsidy" class="it" :class="{ on: activeLedger === 'subsidy' }">
              <span class="dot">补</span>惠民补贴
            </router-link>
            <router-link to="/ledger/edu_aid" class="it" :class="{ on: activeLedger === 'edu_aid' }">
              <span class="dot">教</span>教育资助
            </router-link>
            <router-link to="/ledger/med_aid" class="it" :class="{ on: activeLedger === 'med_aid' }">
              <span class="dot">救</span>医疗救助
            </router-link>
          </div>
        </div>
        <div class="grp">
          <p class="grp-t">报告</p>
          <router-link to="/report" class="it" :class="{ on: navKey === 'report' && !isReports }">
            <span class="dot">报</span>户情报告
          </router-link>
          <router-link to="/reports" class="it" :class="{ on: isReports }">
            <span class="dot">统</span>统计报表
          </router-link>
        </div>
        <div class="grp">
          <p class="grp-t">村务</p>
          <router-link to="/projects" class="it" :class="{ on: navKey === 'projects' }">
            <span class="dot">项</span>乡村项目
          </router-link>
          <span class="it disabled"><span class="dot">资</span>三资管理<span class="soon">二期</span></span>
        </div>
        <div class="grp">
          <p class="grp-t">系统</p>
          <router-link to="/audit" class="it" :class="{ on: navKey === 'audit' }">
            <span class="dot">志</span>操作日志
          </router-link>
          <router-link to="/settings" class="it" :class="{ on: navKey === 'settings' }">
            <span class="dot">设</span>系统设置
          </router-link>
        </div>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <div class="main">
      <header class="topbar">
        <div class="tb-left">
          <button v-if="isMobile && canBack" class="back" aria-label="返回" @click="goBack">‹</button>
          <span class="title">{{ title }}</span>
        </div>
        <span v-if="!isMobile" class="village">{{ villageName }}</span>
      </header>
      <div class="content">
        <router-view />
      </div>
    </div>

    <!-- 移动端底部 Tab -->
    <nav v-if="isMobile" class="tabbar">
      <router-link to="/" class="tab" :class="{ on: navKey === 'home' }">
        <span class="ico">⌂</span><span class="t">首页</span>
      </router-link>
      <router-link to="/ledger" class="tab" :class="{ on: navKey === 'ledger' }">
        <span class="ico">▤</span><span class="t">台账</span>
      </router-link>
      <router-link to="/settings" class="tab" :class="{ on: navKey === 'settings' }">
        <span class="ico">⚙</span><span class="t">设置</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api'
import { useIsMobile } from './composables/useIsMobile'
import { usePageMeta } from './composables/usePageMeta'

const isMobile = useIsMobile()
const route = useRoute()
const router = useRouter()
const { title: pageTitle } = usePageMeta()

const ledgers = ref([])
const villageName = ref('')

const navKey = computed(() => route.meta.nav || '')
const activeLedger = computed(() => route.params.key || '')
const isReports = computed(() => route.path === '/reports')
// 台账中心入口：在台账页且非惠民服务子项时高亮
const ledgerCenterOn = computed(() =>
  navKey.value === 'ledger' && !['subsidy', 'edu_aid', 'med_aid'].includes(activeLedger.value))
const title = computed(() => pageTitle.value || route.meta.title || '')
const canBack = computed(() => !['/', '/ledger', '/settings'].includes(route.path))

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

// 切换路由时清空动态标题，回落到 route.meta.title（动态页在数据加载后重新 setTitle）
watch(() => route.fullPath, () => { pageTitle.value = '' })

onMounted(async () => {
  try { villageName.value = (await api.get('/api/me')).village_name || '' } catch (e) { /* ignore */ }
})
</script>

<style scoped>
.shell { display: flex; min-height: 100vh; }

/* 侧边栏 */
.sidebar {
  width: 216px; background: var(--surface); border-right: 1px solid var(--line);
  display: flex; flex-direction: column; flex-shrink: 0; position: sticky; top: 0; height: 100vh;
}
.logo { display: flex; align-items: center; gap: 10px; padding: 18px 18px 16px; }
.mark {
  width: 30px; height: 30px; border-radius: 8px; background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700;
}
.nm { font-size: 14px; font-weight: 700; color: var(--ink); }
.nav { flex: 1; padding: 0 10px; overflow-y: auto; }
.grp { margin-bottom: 16px; }
.grp-t { font-size: 11px; color: var(--ink3); letter-spacing: .08em; padding: 0 10px; margin: 0 0 6px; }
.sub { padding-left: 10px; }
.it.disabled { color: var(--ink3); cursor: default; }
.it.disabled .dot { background: var(--line-soft); color: var(--ink3); }
.soon { margin-left: auto; font-size: 9px; color: var(--ink3); border: 1px solid var(--line);
        border-radius: 4px; padding: 0 4px; line-height: 14px; }
.it {
  display: flex; align-items: center; gap: 9px; padding: 7px 10px; border-radius: 7px;
  font-size: 13px; color: #4A4F58; margin-bottom: 1px; text-decoration: none;
}
.it:hover { background: var(--bg); }
.dot {
  width: 16px; height: 16px; border-radius: 5px; background: var(--primary-soft); color: var(--primary);
  display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; flex-shrink: 0;
}
.it.on { background: var(--primary-soft); color: var(--primary-deep); font-weight: 600; box-shadow: inset 2px 0 0 var(--primary); }
.it.on .dot { background: var(--primary); color: #fff; }

/* 主内容 */
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar {
  background: var(--surface); border-bottom: 1px solid var(--line); padding: 12px 20px;
  display: flex; align-items: center; justify-content: space-between;
}
.tb-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.title { font-size: 15px; font-weight: 700; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.village { font-size: 12px; color: var(--ink3); }
.back {
  width: 28px; height: 28px; border: none; background: transparent; color: var(--ink);
  font-size: 22px; line-height: 1; cursor: pointer; padding: 0; flex-shrink: 0;
}
.content { flex: 1; }

/* 移动端底部 Tab */
.tabbar {
  background: var(--surface); border-top: 1px solid var(--line); display: flex; padding: 7px 0 8px;
}
.tab { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px;
  font-size: 11px; color: var(--ink3); text-decoration: none; }
.tab .ico { font-size: 20px; line-height: 1; }
.tab.on { color: var(--primary); font-weight: 600; }

@media (max-width: 767px) {
  .shell { flex-direction: column; height: 100vh; }
  .main { flex: 1; min-height: 0; }
  .topbar { padding: 12px 14px; }
  .content { overflow-y: auto; }
  .tabbar { flex-shrink: 0; }
}
</style>
