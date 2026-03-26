<template>
  <div class="results-view">
    <div class="page-header">
      <div>
        <h2 class="tech-title">{{ t('results.title') }}</h2>
        <p class="page-subtitle">{{ task?.name || taskId }}</p>
      </div>
      <div class="header-actions">
        <button class="ghost-btn" @click="goToMonitor">{{ t('results.backToMonitor') }}</button>
        <button class="ghost-btn" @click="goToTasks">{{ t('results.backToTasks') }}</button>
      </div>
    </div>

    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

    <div v-if="task" class="info-grid">
      <div class="info-card tech-card">
        <span class="info-label">{{ t('results.taskId') }}</span>
        <strong class="info-value monospace">{{ task.task_id }}</strong>
      </div>
      <div class="info-card tech-card">
        <span class="info-label">{{ t('results.taskName') }}</span>
        <strong class="info-value">{{ task.name }}</strong>
      </div>
      <div class="info-card tech-card">
        <span class="info-label">{{ t('results.status') }}</span>
        <strong class="info-value">{{ formatStatus(task.status) }}</strong>
      </div>
      <div class="info-card tech-card">
        <span class="info-label">{{ t('results.mode') }}</span>
        <strong class="info-value">{{ formatMode(task.mode) }}</strong>
      </div>
    </div>

    <div v-if="solution.u.length > 0" class="viz-container tech-card">
      <h3 class="viz-title">{{ t('results.visualization') }}</h3>
      <SolutionPlot :x="solution.x" :y="solution.y" :u="solution.u" />
    </div>

    <div v-else class="waiting-box tech-card">
      <p>{{ t('results.waiting') }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SolutionPlot from '../components/SolutionPlot.vue'
import { i18n } from '../locales'
import {
  fetchTrainingResults,
  fetchTrainingTask,
  getApiErrorMessage
} from '../api/tasks'

const route = useRoute()
const router = useRouter()
const t = (key) => i18n.t(key)

const taskId = ref(route.query.task_id || '')
const task = ref(null)
const solution = ref({
  x: [],
  y: [],
  u: []
})
const errorMessage = ref('')

let intervalId = null

const formatMode = (mode) => {
  if (mode === 'native') return t('monitor.modeNative')
  if (mode === 'simulated') return t('monitor.modeSimulated')
  return t('monitor.modePending')
}

const formatStatus = (status) => {
  const labels = {
    queued: t('history.statusQueued'),
    running: t('history.statusRunning'),
    cancelling: t('history.statusCancelling'),
    completed: t('history.statusCompleted'),
    failed: t('history.statusFailed'),
    cancelled: t('history.statusCancelled')
  }
  return labels[status] || status
}

const stopPolling = () => {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

const loadResults = async () => {
  if (!taskId.value) {
    errorMessage.value = 'Missing task_id'
    return
  }

  try {
    task.value = await fetchTrainingTask(taskId.value)
    errorMessage.value = ''

    if (task.value.status !== 'completed') {
      solution.value = { x: [], y: [], u: [] }
      return
    }

    const results = await fetchTrainingResults(taskId.value)
    solution.value = results.solution
    stopPolling()
  } catch (err) {
    errorMessage.value = getApiErrorMessage(err)
  }
}

const goToMonitor = () => {
  router.push(`/monitor?task_id=${taskId.value}`)
}

const goToTasks = () => {
  router.push('/history')
}

onMounted(async () => {
  await loadResults()
  intervalId = setInterval(() => {
    if (task.value?.status !== 'completed') {
      loadResults()
    }
  }, 2000)
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.results-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.tech-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff 0%, #0096ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: #8aa1d6;
  line-height: 1.6;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.ghost-btn {
  background: rgba(0, 150, 255, 0.12);
  border: 1px solid rgba(0, 150, 255, 0.35);
  color: #00d4ff;
  padding: 0.8rem 1.2rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.ghost-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 150, 255, 0.18);
}

.error-box {
  margin-bottom: 1.25rem;
  padding: 1rem 1.2rem;
  background: rgba(255, 87, 87, 0.12);
  border: 1px solid rgba(255, 87, 87, 0.35);
  color: #ff8f8f;
  border-radius: 12px;
}

.tech-card {
  background: rgba(26, 31, 58, 0.72);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.22);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-card {
  padding: 1.25rem;
}

.info-label {
  display: block;
  color: #8aa1d6;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.info-value {
  color: #f4fbff;
  font-size: 1.2rem;
  line-height: 1.5;
}

.monospace {
  font-family: 'Courier New', monospace;
}

.viz-container,
.waiting-box {
  padding: 1.5rem;
}

.viz-title {
  color: #00d4ff;
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
}

.waiting-box {
  text-align: center;
  color: #94a8d6;
}

@media (max-width: 768px) {
  .page-header,
  .header-actions {
    flex-direction: column;
  }

  .ghost-btn {
    width: 100%;
  }
}
</style>
