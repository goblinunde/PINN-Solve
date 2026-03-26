<template>
  <div class="monitor-view">
    <h2 class="tech-title">{{ t('monitor.title') }}</h2>
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon">📉</div>
        <h3>{{ t('monitor.currentLoss') }}</h3>
        <p class="metric-value">{{ currentLoss.toFixed(6) }}</p>
        <div class="metric-bar"></div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">⚡</div>
        <h3>{{ t('monitor.progress') }}</h3>
        <p class="metric-value">{{ (progress * 100).toFixed(0) }}%</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (progress * 100) + '%' }"></div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">🎯</div>
        <h3>{{ t('monitor.status') }}</h3>
        <p class="metric-value status" :class="status">
          {{ status === 'completed' ? t('monitor.statusCompleted') : t('monitor.statusRunning') }}
        </p>
        <div class="status-pulse" v-if="status !== 'completed'"></div>
      </div>
    </div>
    <div class="chart-container tech-card">
      <LossChart :losses="losses" />
    </div>
    <div class="actions" v-if="status === 'completed'">
      <button @click="viewResults" class="tech-btn">
        <span class="btn-glow"></span>
        {{ t('monitor.viewResults') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import LossChart from '../components/LossChart.vue'
import { i18n } from '../locales'

const route = useRoute()
const router = useRouter()
const t = (key) => i18n.t(key)

const taskId = ref(route.query.task_id || 'task-1')
const currentLoss = ref(0.0)
const progress = ref(0)
const status = ref('running')
const losses = ref([])

let intervalId = null

const fetchStatus = async () => {
  try {
    const response = await axios.get(`/api/train/${taskId.value}/status`)
    currentLoss.value = response.data.loss
    progress.value = response.data.progress
    status.value = response.data.status
    losses.value = response.data.losses || []
    
    if (status.value === 'completed') {
      clearInterval(intervalId)
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const viewResults = () => {
  router.push(`/results?task_id=${taskId.value}`)
}

onMounted(() => {
  fetchStatus()
  intervalId = setInterval(fetchStatus, 2000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
.monitor-view {
  max-width: 1200px;
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

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: rgba(26, 31, 58, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.3);
  border-radius: 16px;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 150, 255, 0.3);
  border-color: rgba(0, 150, 255, 0.6);
}

.metric-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
}

.metric-card h3 {
  margin: 0 0 0.5rem 0;
  color: #00d4ff;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.metric-value {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
  color: #00d4ff;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.metric-value.status {
  font-size: 1.5rem;
}

.metric-value.status.completed {
  color: #00ff88;
}

.metric-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #0096ff, #00d4ff);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.progress-bar {
  margin-top: 1rem;
  height: 8px;
  background: rgba(0, 20, 40, 0.5);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0096ff, #00d4ff);
  border-radius: 4px;
  transition: width 0.5s;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
}

.status-pulse {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 12px;
  height: 12px;
  background: #00d4ff;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.5);
  }
}

.chart-container {
  margin-bottom: 2rem;
}

.tech-card {
  background: rgba(26, 31, 58, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.3);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.actions {
  text-align: center;
}

.tech-btn {
  background: linear-gradient(135deg, #0096ff 0%, #00d4ff 100%);
  color: white;
  padding: 1rem 3rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 700;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.tech-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 150, 255, 0.5);
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.tech-btn:hover .btn-glow {
  left: 100%;
}
</style>
