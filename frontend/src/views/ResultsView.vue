<template>
  <div class="results-view page-shell">
    <section class="page-hero">
      <div class="page-header">
        <div>
          <span class="section-kicker">{{ t('nav.results') }}</span>
          <h2 class="page-title">{{ t('results.title') }}</h2>
          <p class="page-subtitle">{{ task?.name || taskId }}</p>
        </div>
        <div class="header-actions">
          <button class="ghost-btn" @click="goToMonitor">{{ t('results.backToMonitor') }}</button>
          <button class="ghost-btn" @click="goToTasks">{{ t('results.backToTasks') }}</button>
        </div>
      </div>

      <div v-if="task" class="info-grid">
        <div class="info-card">
          <span class="info-label">{{ t('results.taskId') }}</span>
          <strong class="info-value monospace">{{ task.task_id }}</strong>
        </div>
        <div class="info-card">
          <span class="info-label">{{ t('results.taskName') }}</span>
          <strong class="info-value">{{ task.name }}</strong>
        </div>
        <div class="info-card">
          <span class="info-label">{{ t('results.status') }}</span>
          <strong class="info-value">{{ formatStatus(task.status) }}</strong>
        </div>
        <div class="info-card">
          <span class="info-label">{{ t('results.mode') }}</span>
          <strong class="info-value">{{ formatMode(task.mode) }}</strong>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

    <section v-if="solution.u.length > 0" class="surface-card viz-container">
      <h3 class="viz-title">{{ t('results.visualization') }}</h3>
      <SolutionPlot :x="solution.x" :y="solution.y" :u="solution.u" />
    </section>

    <section v-else class="surface-card waiting-box">
      <p>{{ t('results.waiting') }}</p>
    </section>
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
  if (mode === 'python') return t('monitor.modePython')
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
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.ghost-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  padding: 0.85rem 1.2rem;
  border-radius: 16px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.25s ease;
}

.ghost-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
}

.error-box {
  padding: 1rem 1.2rem;
  background: rgba(255, 143, 143, 0.12);
  border: 1px solid rgba(255, 143, 143, 0.28);
  color: var(--danger);
  border-radius: 18px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.info-card {
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
}

.info-label {
  display: block;
  color: var(--text-dim);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.info-value {
  color: var(--text-main);
  font-size: 1.2rem;
  line-height: 1.5;
}

.monospace {
  font-family: 'Courier New', monospace;
}

.viz-container,
.waiting-box {
  padding: 24px;
}

.viz-title {
  color: var(--accent-strong);
  margin: 0 0 1rem 0;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
}

.waiting-box {
  text-align: center;
  color: var(--text-soft);
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
