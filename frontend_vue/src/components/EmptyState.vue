<template>
  <div class="empty panel">
    <p class="muted">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '暂无数据',
  },
});
</script>

<style scoped>
.empty {
  padding: 20px;
  text-align: center;
}
</style>
