<template>
  <div class="history-view">
    <h2 class="tech-title">{{ t('history.title') }}</h2>
    <div class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-item tech-card">
        <div class="task-icon">📋</div>
        <div class="task-info">
          <span class="task-name">{{ task.name }}</span>
          <span class="task-time">{{ task.time }}</span>
        </div>
        <span class="status-badge" :class="task.status">{{ task.status }}</span>
      </div>
      <div v-if="tasks.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p>No history records yet</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { i18n } from '../locales'

const t = (key) => i18n.t(key)

const tasks = ref([
  { id: 1, name: '2D Laplace Equation', status: 'completed', time: '2026-03-26 21:00' },
  { id: 2, name: 'Heat Equation', status: 'running', time: '2026-03-26 21:15' }
])
</script>

<style scoped>
.history-view {
  max-width: 1000px;
  margin: 0 auto;
}

.tech-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff 0%, #0096ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 2rem;
  text-align: center;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  transition: all 0.3s;
  cursor: pointer;
}

.task-item:hover {
  transform: translateX(10px);
  border-color: rgba(0, 150, 255, 0.6);
  box-shadow: 0 8px 30px rgba(0, 150, 255, 0.3);
}

.tech-card {
  background: rgba(26, 31, 58, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.task-icon {
  font-size: 2rem;
  filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
}

.task-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.task-name {
  color: #e0e0e0;
  font-weight: 600;
  font-size: 1.1rem;
}

.task-time {
  color: #a0a0a0;
  font-size: 0.9rem;
}

.status-badge {
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.completed {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
  border: 1px solid rgba(0, 255, 136, 0.4);
}

.status-badge.running {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  border: 1px solid rgba(0, 212, 255, 0.4);
  animation: pulse 2s infinite;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #a0a0a0;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
