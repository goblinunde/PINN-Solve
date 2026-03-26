<template>
  <div class="monitor-view">
    <div class="page-header">
      <div>
        <h2 class="tech-title">{{ t('monitor.title') }}</h2>
        <p class="page-subtitle">{{ task?.name || taskId }}</p>
      </div>
      <div class="header-actions">
        <button class="ghost-btn" @click="loadTask()">{{ t('monitor.refresh') }}</button>
        <button class="ghost-btn" @click="viewTasks">{{ t('monitor.backToTasks') }}</button>
      </div>
    </div>

    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span class="metric-label">{{ t('monitor.currentLoss') }}</span>
        <strong class="metric-value">{{ formatLoss(task?.current_loss) }}</strong>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ t('monitor.progress') }}</span>
        <strong class="metric-value">{{ progressPercent }}%</strong>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
        </div>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ t('monitor.status') }}</span>
        <strong class="metric-value" :class="statusClass">{{ statusText }}</strong>
      </div>
      <div class="metric-card">
        <span class="metric-label">{{ t('monitor.mode') }}</span>
        <strong class="metric-value">{{ modeText }}</strong>
      </div>
    </div>

    <div v-if="task" class="detail-grid">
      <div class="detail-card tech-card">
        <span class="detail-label">{{ t('monitor.taskId') }}</span>
        <strong class="detail-value monospace">{{ task.task_id }}</strong>
      </div>
      <div class="detail-card tech-card">
        <span class="detail-label">{{ t('monitor.taskName') }}</span>
        <strong class="detail-value">{{ task.name }}</strong>
      </div>
      <div class="detail-card tech-card">
        <span class="detail-label">{{ t('monitor.pde') }}</span>
        <strong class="detail-value">{{ task.config?.pde || '--' }}</strong>
      </div>
      <div class="detail-card tech-card">
        <span class="detail-label">{{ t('monitor.network') }}</span>
        <strong class="detail-value">{{ formatLayers(task.config) }}</strong>
      </div>
      <div class="detail-card tech-card">
        <span class="detail-label">{{ t('monitor.epochs') }}</span>
        <strong class="detail-value">{{ task.config?.epochs ?? '--' }}</strong>
      </div>
    </div>

    <div v-if="task?.note" class="note-box">{{ task.note }}</div>

    <div class="chart-container tech-card">
      <LossChart v-if="hasLosses" :losses="task.losses" />
      <div v-else class="chart-empty">{{ t('monitor.chartEmpty') }}</div>
    </div>

    <div class="actions">
      <button v-if="task?.can_cancel" class="action-btn warning" @click="cancelTask">
        {{ t('monitor.cancelTask') }}
      </button>
      <button v-if="task?.has_results" class="action-btn primary" @click="viewResults">
        {{ t('monitor.viewResults') }}
      </button>
      <button class="action-btn secondary" @click="viewTasks">
        {{ t('monitor.backToTasks') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LossChart from '../components/LossChart.vue'
import { i18n } from '../locales'
import {
  cancelTrainingTask,
  fetchTrainingStatus,
  getApiErrorMessage
} from '../api/tasks'

const route = useRoute()
const router = useRouter()
const t = (key) => i18n.t(key)

const taskId = ref(route.query.task_id || '')
const task = ref(null)
const errorMessage = ref('')

let intervalId = null

const terminalStatuses = ['completed', 'failed', 'cancelled']

const progressPercent = computed(() => {
  return Math.round(((task.value?.progress) || 0) * 100)
})

const hasLosses = computed(() => Array.isArray(task.value?.losses) && task.value.losses.length > 0)
const statusClass = computed(() => task.value?.status || 'queued')

const statusText = computed(() => {
  const labels = {
    queued: t('monitor.statusQueued'),
    running: t('monitor.statusRunning'),
    cancelling: t('monitor.statusCancelling'),
    completed: t('monitor.statusCompleted'),
    failed: t('monitor.statusFailed'),
    cancelled: t('monitor.statusCancelled')
  }
  return labels[task.value?.status] || '--'
})

const modeText = computed(() => {
  if (task.value?.mode === 'native') return t('monitor.modeNative')
  if (task.value?.mode === 'simulated') return t('monitor.modeSimulated')
  return t('monitor.modePending')
})

const formatLoss = (value) => {
  return typeof value === 'number' ? value.toExponential(3) : '--'
}

const formatLayers = (config) => {
  const solverNetwork = config?.solver_config?.network
  if (solverNetwork) {
    const hiddenLayers = Array.isArray(solverNetwork.hidden_layers)
      ? solverNetwork.hidden_layers.map((layer) => (layer.residual ? `${layer.size}R` : `${layer.size}`))
      : []
    return [solverNetwork.input_dim || 2, ...hiddenLayers, solverNetwork.output_dim || 1].join(' -> ')
  }

  const layers = config?.layers
  return Array.isArray(layers) && layers.length > 0 ? layers.join(' -> ') : '--'
}

const stopPolling = () => {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

const loadTask = async () => {
  if (!taskId.value) {
    errorMessage.value = 'Missing task_id'
    return
  }

  try {
    const data = await fetchTrainingStatus(taskId.value)
    task.value = data
    errorMessage.value = ''

    if (terminalStatuses.includes(data.status)) {
      stopPolling()
    }
  } catch (err) {
    errorMessage.value = getApiErrorMessage(err)
    stopPolling()
  }
}

const cancelTask = async () => {
  try {
    await cancelTrainingTask(taskId.value)
    await loadTask()
  } catch (err) {
    errorMessage.value = getApiErrorMessage(err)
  }
}

const viewResults = () => {
  router.push(`/results?task_id=${taskId.value}`)
}

const viewTasks = () => {
  router.push('/history')
}

onMounted(async () => {
  await loadTask()
  intervalId = setInterval(() => {
    if (!terminalStatuses.includes(task.value?.status)) {
      loadTask()
    }
  }, 2000)
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.monitor-view {
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

.header-actions,
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.ghost-btn,
.action-btn {
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.ghost-btn {
  background: rgba(0, 150, 255, 0.12);
  border: 1px solid rgba(0, 150, 255, 0.35);
  color: #00d4ff;
  padding: 0.8rem 1.2rem;
}

.ghost-btn:hover,
.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 150, 255, 0.18);
}

.error-box,
.note-box {
  margin-bottom: 1.25rem;
  padding: 1rem 1.2rem;
  border-radius: 12px;
}

.error-box {
  background: rgba(255, 87, 87, 0.12);
  border: 1px solid rgba(255, 87, 87, 0.35);
  color: #ff8f8f;
}

.note-box {
  background: rgba(0, 150, 255, 0.12);
  border: 1px solid rgba(0, 150, 255, 0.3);
  color: #b5c7ee;
}

.metrics-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric-card,
.tech-card {
  background: rgba(26, 31, 58, 0.72);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.22);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
}

.metric-card,
.detail-card {
  padding: 1.25rem;
}

.metric-label,
.detail-label {
  display: block;
  color: #8aa1d6;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.metric-value,
.detail-value {
  color: #f4fbff;
  font-size: 1.3rem;
  line-height: 1.5;
}

.metric-value.completed {
  color: #00ff88;
}

.metric-value.failed,
.metric-value.cancelled {
  color: #ff7e7e;
}

.metric-value.running,
.metric-value.cancelling,
.metric-value.queued {
  color: #00d4ff;
}

.monospace {
  font-family: 'Courier New', monospace;
}

.progress-bar {
  margin-top: 1rem;
  height: 10px;
  background: rgba(10, 14, 39, 0.65);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0096ff, #00d4ff);
  box-shadow: 0 0 18px rgba(0, 212, 255, 0.5);
}

.chart-container {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.chart-empty {
  min-height: 240px;
  display: grid;
  place-items: center;
  color: #94a8d6;
}

.action-btn {
  border: none;
  padding: 0.85rem 1.1rem;
}

.action-btn.primary {
  background: linear-gradient(135deg, #0096ff 0%, #00d4ff 100%);
  color: #ffffff;
}

.action-btn.secondary {
  background: rgba(0, 150, 255, 0.12);
  color: #d7e5ff;
  border: 1px solid rgba(0, 150, 255, 0.24);
}

.action-btn.warning {
  background: rgba(255, 184, 107, 0.12);
  color: #ffd197;
  border: 1px solid rgba(255, 184, 107, 0.24);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .header-actions,
  .actions {
    width: 100%;
    flex-direction: column;
  }

  .ghost-btn,
  .action-btn {
    width: 100%;
  }
}
</style>
