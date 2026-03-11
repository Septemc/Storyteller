<template>
  <div class="loading muted">{{ text }}</div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '加载中...',
  },
});
</script>

<style scoped>
.loading {
  padding: 12px;
  text-align: center;
}
</style>
