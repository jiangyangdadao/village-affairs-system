import { createRouter, createWebHashHistory } from 'vue-router'
import Login from './views/Login.vue'
import HomeGrid from './views/HomeGrid.vue'
import LedgerList from './views/LedgerList.vue'
import LedgerDetail from './views/LedgerDetail.vue'
import LedgerEdit from './views/LedgerEdit.vue'
import Report from './views/Report.vue'
import Projects from './views/Projects.vue'
import AuditLog from './views/AuditLog.vue'
import Settings from './views/Settings.vue'
import Expired from './views/Expired.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/expired', component: Expired },
  { path: '/', component: HomeGrid },
  { path: '/ledger/:key', component: LedgerList },
  { path: '/ledger/:key/new', component: LedgerEdit },
  { path: '/ledger/:key/:id(\\d+)', component: LedgerDetail },
  { path: '/ledger/:key/:id(\\d+)/edit', component: LedgerEdit },
  { path: '/report', component: Report },
  { path: '/report/:hid(\\d+)', component: Report },
  { path: '/projects', component: Projects },
  { path: '/audit', component: AuditLog },
  { path: '/settings', component: Settings },
]

export default createRouter({ history: createWebHashHistory(), routes })
