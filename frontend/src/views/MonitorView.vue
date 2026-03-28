<template>
  <div class="monitor-view page-shell">
    <section class="page-hero">
      <div class="page-header">
        <div>
          <span class="section-kicker">{{ t('nav.monitor') }}</span>
          <h2 class="page-title">{{ t('monitor.title') }}</h2>
          <p class="page-subtitle">{{ task?.name || taskId }}</p>
        </div>
        <div class="header-actions">
          <button class="ghost-btn" @click="loadTask()">{{ t('monitor.refresh') }}</button>
          <button class="ghost-btn" @click="viewTasks">{{ t('monitor.backToTasks') }}</button>
        </div>
      </div>

      <div class="metrics-grid hero-metrics">
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
    </section>

    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

    <section v-if="task" class="surface-card">
      <div class="detail-header">
        <p class="page-subtitle">{{ task?.name || taskId }}</p>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
        <span class="detail-label">{{ t('monitor.taskId') }}</span>
        <strong class="detail-value monospace">{{ task.task_id }}</strong>
        </div>
        <div class="detail-card">
        <span class="detail-label">{{ t('monitor.taskName') }}</span>
        <strong class="detail-value">{{ task.name }}</strong>
        </div>
        <div class="detail-card">
        <span class="detail-label">{{ t('monitor.pde') }}</span>
        <strong class="detail-value">{{ task.config?.pde || '--' }}</strong>
        </div>
        <div class="detail-card">
        <span class="detail-label">{{ t('monitor.network') }}</span>
        <strong class="detail-value">{{ formatLayers(task.config) }}</strong>
        </div>
        <div class="detail-card">
        <span class="detail-label">{{ t('monitor.epochs') }}</span>
        <strong class="detail-value">{{ task.config?.epochs ?? '--' }}</strong>
        </div>
      </div>

      <div v-if="task?.note" class="note-box inline-note">{{ task.note }}</div>
    </section>

    <section class="surface-card chart-container">
      <LossChart v-if="hasLosses" :losses="task.losses" />
      <div v-else class="chart-empty">{{ t('monitor.chartEmpty') }}</div>
    </section>

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
  if (task.value?.mode === 'python') return t('monitor.modePython')
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
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.hero-metrics {
  margin-bottom: 0;
}

.detail-header {
  margin-bottom: 1.25rem;
}

.header-actions,
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.ghost-btn,
.action-btn {
  border-radius: 16px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.25s ease;
}

.ghost-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  padding: 0.85rem 1.2rem;
}

.ghost-btn:hover,
.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
}

.error-box,
.note-box {
  margin-bottom: 1.25rem;
  padding: 1rem 1.2rem;
  border-radius: 18px;
}

.error-box {
  background: rgba(255, 143, 143, 0.12);
  border: 1px solid rgba(255, 143, 143, 0.28);
  color: var(--danger);
}

.note-box {
  background: rgba(255, 179, 107, 0.1);
  border: 1px solid rgba(255, 179, 107, 0.24);
  color: #ffd6ac;
}

.inline-note {
  margin-bottom: 0;
}

.metrics-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 1.5rem;
}

.metric-card,
.detail-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
}

.metric-card,
.detail-card {
  padding: 1.25rem;
}

.metric-label,
.detail-label {
  display: block;
  color: var(--text-dim);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.metric-value,
.detail-value {
  color: var(--text-main);
  font-size: 1.3rem;
  line-height: 1.5;
}

.metric-value.completed {
  color: var(--success);
}

.metric-value.failed,
.metric-value.cancelled {
  color: var(--danger);
}

.metric-value.running,
.metric-value.cancelling,
.metric-value.queued {
  color: var(--accent-strong);
}

.monospace {
  font-family: 'Courier New', monospace;
}

.progress-bar {
  margin-top: 1rem;
  height: 10px;
  background: rgba(4, 10, 22, 0.66);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-warm));
  box-shadow: 0 0 18px rgba(87, 184, 255, 0.38);
}

.chart-container {
  margin-bottom: 1.5rem;
}

.chart-empty {
  min-height: 240px;
  display: grid;
  place-items: center;
  color: var(--text-soft);
}

.action-btn {
  border: 1px solid transparent;
  padding: 0.95rem 1.2rem;
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--accent-warm) 0%, var(--accent) 100%);
  color: #07111f;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-main);
  border-color: var(--line-soft);
}

.action-btn.warning {
  background: rgba(255, 179, 107, 0.12);
  color: #ffd3a7;
  border-color: rgba(255, 179, 107, 0.24);
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
