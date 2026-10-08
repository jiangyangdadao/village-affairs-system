import { ref } from 'vue'

// 单例响应式页面标题：动态标题页（台账列表/详情/编辑）在数据加载后 setTitle，
// 布局壳 topbar 读取；切换路由时由壳清空，回落到 route.meta.title。
const title = ref('')

export function usePageMeta() {
  function setTitle(t) {
    title.value = t
  }
  return { title, setTitle }
}
