<template>
  <span class="tag-chip" :class="colorClass">{{ text }}</span>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ text: String, color: { type: String, default: 'red' } })
const colorClass = computed(() => `tc-${props.color}`)
</script>
<style scoped>
.tag-chip { display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 999px; margin-right: 5px; }
.tc-red { background: #F7EAE7; color: #B01B2E; }
.tc-grey { background: #EEF0EB; color: #7C8075; }
.tc-amber { background: #F7F0E4; color: #A35D12; }
.tc-green { background: #E9F3EC; color: #2E7D4F; }
</style>
