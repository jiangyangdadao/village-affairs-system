import { ref } from 'vue'

// 单例响应式：窗口宽度 <768 视为手机端，窗口缩放/旋转时自动更新
const mq = typeof window !== 'undefined' ? window.matchMedia('(max-width: 767px)') : null
const isMobile = ref(mq ? mq.matches : false)

if (mq) {
  mq.addEventListener('change', (e) => { isMobile.value = e.matches })
}

export function useIsMobile() {
  return isMobile
}
