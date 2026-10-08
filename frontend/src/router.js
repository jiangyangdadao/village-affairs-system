import { createRouter, createWebHashHistory } from 'vue-router'
import Login from './views/Login.vue'
import Expired from './views/Expired.vue'
import AppShell from './AppShell.vue'
import HomeGrid from './views/HomeGrid.vue'
import LedgerIndex from './views/LedgerIndex.vue'
import LedgerList from './views/LedgerList.vue'
import LedgerDetail from './views/LedgerDetail.vue'
import LedgerEdit from './views/LedgerEdit.vue'
import Report from './views/Report.vue'
import Reports from './views/Reports.vue'
import MonitoringList from './views/MonitoringList.vue'
import MonitoringDetail from './views/MonitoringDetail.vue'
import Projects from './views/Projects.vue'
import AuditLog from './views/AuditLog.vue'
import Settings from './views/Settings.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/expired', component: Expired },
  {
    path: '/',
    component: AppShell,
    children: [
      { path: '', component: HomeGrid, meta: { title: '管理首页', nav: 'home' } },
      { path: 'ledger', component: LedgerIndex, meta: { title: '台账', nav: 'ledger' } },
      { path: 'ledger/:key', component: LedgerList, meta: { nav: 'ledger' } },
      { path: 'ledger/:key/new', component: LedgerEdit, meta: { nav: 'ledger' } },
      { path: 'ledger/:key/:id(\\d+)', component: LedgerDetail, meta: { nav: 'ledger' } },
      { path: 'ledger/:key/:id(\\d+)/edit', component: LedgerEdit, meta: { nav: 'ledger' } },
      { path: 'report', component: Report, meta: { title: '户情报告', nav: 'report' } },
      { path: 'report/:hid(\\d+)', component: Report, meta: { title: '户情报告', nav: 'report' } },
      { path: 'reports', component: Reports, meta: { title: '统计报表', nav: 'report' } },
      { path: 'monitoring', component: MonitoringList, meta: { title: '防返贫监测', nav: 'monitoring' } },
      { path: 'monitoring/:hid(\\d+)', component: MonitoringDetail, meta: { nav: 'monitoring' } },
      { path: 'projects', component: Projects, meta: { title: '乡村项目', nav: 'projects' } },
      { path: 'audit', component: AuditLog, meta: { title: '操作日志', nav: 'audit' } },
      { path: 'settings', component: Settings, meta: { title: '系统设置', nav: 'settings' } },
    ],
  },
]

export default createRouter({ history: createWebHashHistory(), routes })
