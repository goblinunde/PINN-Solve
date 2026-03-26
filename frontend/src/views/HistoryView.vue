<template>
  <div class="history-view">
    <h2>历史记录</h2>
    <div class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-item">
        <span>{{ task.name }}</span>
        <span class="status">{{ task.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const tasks = ref([])
</script>

<style scoped>
.history-view {
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.status {
  color: #27ae60;
  font-weight: 600;
}
</style>
