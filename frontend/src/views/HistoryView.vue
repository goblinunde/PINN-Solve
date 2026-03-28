<template>
  <div class="history-view page-shell">
    <section class="page-hero">
      <div class="page-header">
        <div>
          <span class="section-kicker">{{ t('nav.history') }}</span>
          <h2 class="page-title">{{ t('history.title') }}</h2>
          <p class="page-subtitle">{{ t('history.subtitle') }}</p>
        </div>
        <button class="ghost-btn" :disabled="loading || actionLoading" @click="loadTaskCenter()">
          {{ loading ? t('history.refreshing') : t('history.refresh') }}
        </button>
      </div>

      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">{{ t('history.total') }}</span>
          <strong class="summary-value">{{ totalCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">{{ t('history.active') }}</span>
          <strong class="summary-value">{{ activeCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">{{ t('history.completed') }}</span>
          <strong class="summary-value">{{ completedCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">{{ t('history.unhealthy') }}</span>
          <strong class="summary-value">{{ unhealthyCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">{{ t('history.onlineWorkers') }}</span>
          <strong class="summary-value">{{ onlineWorkerCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">{{ t('history.queueDepth') }}</span>
          <strong class="summary-value">{{ queueDepth }}</strong>
        </div>
      </div>
    </section>

    <div v-if="error" class="error-box">{{ error }}</div>

    <section class="worker-panel surface-card">
      <div class="panel-header">
        <h3>{{ t('history.workerTitle') }}</h3>
        <span class="worker-summary" :class="{ offline: onlineWorkerCount === 0 }">
          {{ onlineWorkerCount }}/{{ totalWorkers }} {{ t('history.onlineWorkers') }}
        </span>
      </div>

      <div v-if="workers.length > 0" class="worker-list">
        <article v-for="worker in workers" :key="worker.worker_id" class="worker-item">
          <div>
            <strong class="worker-name">{{ worker.worker_id }}</strong>
            <p class="worker-meta">
              {{ t('history.lastHeartbeat') }}: {{ formatTime(worker.last_heartbeat_at) }}
            </p>
          </div>
          <span class="status-badge" :class="worker.status">
            {{ worker.status === 'online' ? t('history.workerOnline') : t('history.workerOffline') }}
          </span>
        </article>
      </div>

      <p v-else class="worker-empty">{{ t('history.workerEmpty') }}</p>
    </section>

    <section class="toolbar surface-card">
      <div class="search-row">
        <input
          v-model="searchQuery"
          class="search-input"
          :placeholder="t('history.searchPlaceholder')"
        />
      </div>

      <div class="filter-row">
        <button
          v-for="filter in filters"
          :key="filter.value"
          class="filter-chip"
          :class="{ active: activeFilter === filter.value }"
          @click="activeFilter = filter.value"
        >
          {{ filter.label }}
        </button>
      </div>

      <div class="bulk-row">
        <button
          class="action-btn secondary"
          :disabled="deletableVisibleIds.length === 0"
          @click="toggleSelectVisible()"
        >
          {{ allVisibleSelected ? t('history.clearVisible') : t('history.selectVisible') }}
        </button>
        <button
          class="action-btn danger"
          :disabled="selectedTaskIds.length === 0 || actionLoading"
          @click="removeSelected"
        >
          {{ t('history.bulkDelete') }} ({{ selectedTaskIds.length }})
        </button>
      </div>
    </section>

    <div v-if="tasks.length === 0" class="empty-state surface-card">
      <p>{{ t('history.empty') }}</p>
    </div>

    <div v-else-if="filteredTasks.length === 0" class="empty-state surface-card">
      <p>{{ t('history.noMatch') }}</p>
    </div>

    <div v-else class="task-list">
      <article v-for="task in filteredTasks" :key="task.task_id" class="task-card surface-card">
        <div class="task-top">
          <div class="task-header-left">
            <label class="select-box" :class="{ disabled: !task.can_delete }">
              <input
                type="checkbox"
                :checked="selectedTaskIds.includes(task.task_id)"
                :disabled="!task.can_delete"
                @change="toggleSelection(task.task_id)"
              />
            </label>

            <div class="task-head">
              <h3>{{ task.name || task.task_id }}</h3>
              <p>{{ task.pde || task.task_id }}</p>
            </div>
          </div>

          <span class="status-badge" :class="task.status">
            {{ statusLabel(task.status) }}
          </span>
        </div>

        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">{{ t('history.taskId') }}</span>
            <span class="meta-value monospace">{{ task.task_id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">{{ t('history.mode') }}</span>
            <span class="meta-value">{{ formatMode(task.mode) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">{{ t('history.createdAt') }}</span>
            <span class="meta-value">{{ formatTime(task.created_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">{{ t('history.updatedAt') }}</span>
            <span class="meta-value">{{ formatTime(task.updated_at) }}</span>
          </div>
        </div>

        <div class="progress-row">
          <div class="progress-info">
            <span>{{ t('history.currentLoss') }}: {{ formatLoss(task.current_loss) }}</span>
            <span>{{ Math.round((task.progress || 0) * 100) }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${Math.round((task.progress || 0) * 100)}%` }"></div>
          </div>
        </div>

        <p v-if="task.note || task.error" class="task-note">
          {{ task.error || task.note }}
        </p>

        <div class="actions">
          <button class="action-btn secondary" @click="openMonitor(task.task_id)">
            {{ t('history.monitor') }}
          </button>
          <button v-if="task.has_results" class="action-btn primary" @click="openResults(task.task_id)">
            {{ t('history.viewResults') }}
          </button>
          <button v-if="task.can_cancel" class="action-btn warning" @click="requestCancel(task.task_id)">
            {{ t('history.cancel') }}
          </button>
          <button
            v-if="task.status === 'failed' || task.status === 'cancelled'"
            class="action-btn primary"
            @click="requestRetry(task.task_id)"
          >
            {{ t('history.retry') }}
          </button>
          <button v-if="task.can_delete" class="action-btn danger" @click="removeTask(task.task_id)">
            {{ t('history.delete') }}
          </button>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { i18n } from '../locales'
import {
  bulkDeleteTrainingTasks,
  cancelTrainingTask,
  deleteTrainingTask,
  fetchSystemOverview,
  getApiErrorMessage,
  listTrainingTasks,
  retryTrainingTask
} from '../api/tasks'

const router = useRouter()
const t = (key) => i18n.t(key)

const tasks = ref([])
const counts = ref({
  queued: 0,
  running: 0,
  cancelling: 0,
  completed: 0,
  failed: 0,
  cancelled: 0
})
const overview = ref({
  workers: [],
  queue: {
    total: 0,
    queued: 0,
    running: 0,
    cancelling: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
    online_workers: 0,
    workers: 0
  }
})
const searchQuery = ref('')
const activeFilter = ref('all')
const selectedTaskIds = ref([])
const loading = ref(false)
const actionLoading = ref(false)
const error = ref('')

let intervalId = null

const filters = computed(() => [
  { value: 'all', label: t('history.filterAll') },
  { value: 'active', label: t('history.filterActive') },
  { value: 'completed', label: t('history.filterCompleted') },
  { value: 'failed', label: t('history.filterFailed') }
])

const workers = computed(() => overview.value.workers || [])
const totalWorkers = computed(() => workers.value.length)
const onlineWorkerCount = computed(() => workers.value.filter(worker => worker.status === 'online').length)
const queueDepth = computed(() => overview.value.queue?.queued || 0)

const totalCount = computed(() => tasks.value.length)
const activeCount = computed(() => counts.value.queued + counts.value.running + counts.value.cancelling)
const completedCount = computed(() => counts.value.completed)
const unhealthyCount = computed(() => counts.value.failed + counts.value.cancelled)

const filteredTasks = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return tasks.value.filter(task => {
    const matchesSearch =
      query.length === 0 ||
      [task.name, task.pde, task.task_id]
        .filter(Boolean)
        .some(value => value.toLowerCase().includes(query))

    if (!matchesSearch) return false

    if (activeFilter.value === 'active') {
      return ['queued', 'running', 'cancelling'].includes(task.status)
    }
    if (activeFilter.value === 'completed') {
      return task.status === 'completed'
    }
    if (activeFilter.value === 'failed') {
      return ['failed', 'cancelled'].includes(task.status)
    }
    return true
  })
})

const deletableVisibleIds = computed(() => {
  return filteredTasks.value.filter(task => task.can_delete).map(task => task.task_id)
})

const allVisibleSelected = computed(() => {
  if (deletableVisibleIds.value.length === 0) return false
  return deletableVisibleIds.value.every(taskId => selectedTaskIds.value.includes(taskId))
})

const statusLabel = (status) => {
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

const formatMode = (mode) => {
  if (mode === 'native') return t('monitor.modeNative')
  if (mode === 'simulated') return t('monitor.modeSimulated')
  return t('monitor.modePending')
}

const formatTime = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

const formatLoss = (value) => {
  return typeof value === 'number' ? value.toExponential(3) : '--'
}

const syncSelection = () => {
  const deletableIds = new Set(tasks.value.filter(task => task.can_delete).map(task => task.task_id))
  selectedTaskIds.value = selectedTaskIds.value.filter(taskId => deletableIds.has(taskId))
}

const loadTaskCenter = async ({ silent = false } = {}) => {
  if (loading.value && silent) return

  if (!silent) {
    loading.value = true
  }
  error.value = ''

  try {
    const [taskData, systemData] = await Promise.all([
      listTrainingTasks(),
      fetchSystemOverview()
    ])

    tasks.value = taskData.items || []
    counts.value = {
      ...counts.value,
      ...(taskData.counts || {})
    }
    overview.value = systemData || overview.value
    syncSelection()
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const toggleSelection = (taskId) => {
  if (selectedTaskIds.value.includes(taskId)) {
    selectedTaskIds.value = selectedTaskIds.value.filter(id => id !== taskId)
    return
  }
  selectedTaskIds.value = [...selectedTaskIds.value, taskId]
}

const toggleSelectVisible = () => {
  if (allVisibleSelected.value) {
    const visibleIds = new Set(deletableVisibleIds.value)
    selectedTaskIds.value = selectedTaskIds.value.filter(taskId => !visibleIds.has(taskId))
    return
  }

  selectedTaskIds.value = Array.from(new Set([
    ...selectedTaskIds.value,
    ...deletableVisibleIds.value
  ]))
}

const openMonitor = (taskId) => {
  router.push(`/monitor?task_id=${taskId}`)
}

const openResults = (taskId) => {
  router.push(`/results?task_id=${taskId}`)
}

const requestCancel = async (taskId) => {
  if (!window.confirm(t('history.confirmCancel'))) return

  try {
    actionLoading.value = true
    await cancelTrainingTask(taskId)
    await loadTaskCenter()
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

const requestRetry = async (taskId) => {
  try {
    actionLoading.value = true
    const response = await retryTrainingTask(taskId)
    await loadTaskCenter()
    router.push(`/monitor?task_id=${response.task_id}`)
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

const removeTask = async (taskId) => {
  if (!window.confirm(t('history.confirmDelete'))) return

  try {
    actionLoading.value = true
    await deleteTrainingTask(taskId)
    await loadTaskCenter()
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

const removeSelected = async () => {
  if (selectedTaskIds.value.length === 0) return
  if (!window.confirm(t('history.confirmBulkDelete'))) return

  try {
    actionLoading.value = true
    await bulkDeleteTrainingTasks(selectedTaskIds.value)
    selectedTaskIds.value = []
    await loadTaskCenter()
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    actionLoading.value = false
  }
}

onMounted(async () => {
  await loadTaskCenter()
  intervalId = setInterval(() => {
    loadTaskCenter({ silent: true })
  }, 3000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.history-view {
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.ghost-btn,
.action-btn,
.filter-chip {
  border: none;
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

.ghost-btn:hover:not(:disabled),
.action-btn:hover,
.filter-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
}

.ghost-btn:disabled,
.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-box {
  padding: 1rem 1.2rem;
  background: rgba(255, 143, 143, 0.12);
  border: 1px solid rgba(255, 143, 143, 0.28);
  color: var(--danger);
  border-radius: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 0;
}

.summary-card {
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
}

.summary-label {
  display: block;
  color: var(--text-dim);
  margin-bottom: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}

.summary-value {
  font-size: 2rem;
  color: var(--text-main);
}

.worker-panel,
.toolbar {
  margin-bottom: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.panel-header h3 {
  color: var(--text-main);
  font-size: 1.1rem;
}

.worker-summary {
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  background: rgba(109, 240, 183, 0.12);
  color: var(--success);
  border: 1px solid rgba(109, 240, 183, 0.24);
}

.worker-summary.offline {
  background: rgba(255, 143, 143, 0.14);
  color: var(--danger);
  border-color: rgba(255, 143, 143, 0.28);
}

.worker-list {
  display: grid;
  gap: 0.75rem;
}

.worker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.95rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
}

.worker-name {
  display: block;
  color: var(--text-main);
  margin-bottom: 0.3rem;
}

.worker-meta,
.worker-empty {
  color: var(--text-soft);
}

.search-row,
.filter-row,
.bulk-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.filter-row,
.bulk-row {
  margin-top: 1rem;
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  padding: 0.9rem 1rem;
  border-radius: 16px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: rgba(139, 225, 255, 0.55);
  box-shadow: 0 0 0 4px rgba(87, 184, 255, 0.12);
}

.filter-chip {
  padding: 0.65rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-soft);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.filter-chip.active {
  background: linear-gradient(135deg, rgba(255, 179, 107, 0.18), rgba(87, 184, 255, 0.18));
  color: var(--text-main);
  border-color: rgba(255, 255, 255, 0.16);
}

.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--text-soft);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-card {
  padding: 1.4rem;
}

.task-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.task-header-left {
  display: flex;
  gap: 0.9rem;
  align-items: flex-start;
  flex: 1;
}

.select-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-top: 0.25rem;
}

.select-box.disabled {
  opacity: 0.4;
}

.task-head h3 {
  color: var(--text-main);
  margin-bottom: 0.35rem;
  font-size: 1.2rem;
}

.task-head p {
  color: var(--text-soft);
  line-height: 1.5;
}

.status-badge {
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-badge.queued {
  color: #ffd792;
  background: rgba(255, 179, 107, 0.16);
  border: 1px solid rgba(255, 179, 107, 0.26);
}

.status-badge.running,
.status-badge.online {
  color: var(--accent-strong);
  background: rgba(87, 184, 255, 0.16);
  border: 1px solid rgba(87, 184, 255, 0.26);
}

.status-badge.cancelling {
  color: #ffd3a7;
  background: rgba(255, 179, 107, 0.14);
  border: 1px solid rgba(255, 179, 107, 0.28);
}

.status-badge.completed {
  color: var(--success);
  background: rgba(109, 240, 183, 0.14);
  border: 1px solid rgba(109, 240, 183, 0.28);
}

.status-badge.failed,
.status-badge.cancelled,
.status-badge.offline {
  color: var(--danger);
  background: rgba(255, 143, 143, 0.14);
  border: 1px solid rgba(255, 143, 143, 0.28);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.meta-item {
  padding: 0.9rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.meta-label {
  display: block;
  color: var(--text-dim);
  font-size: 0.82rem;
  margin-bottom: 0.35rem;
}

.meta-value {
  color: var(--text-main);
  line-height: 1.5;
}

.monospace {
  font-family: 'Courier New', monospace;
}

.progress-row {
  margin-bottom: 1rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--text-main);
  margin-bottom: 0.55rem;
}

.progress-bar {
  height: 10px;
  background: rgba(4, 10, 22, 0.66);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-warm));
  box-shadow: 0 0 18px rgba(87, 184, 255, 0.4);
}

.task-note {
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border-left: 3px solid rgba(255, 179, 107, 0.55);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-soft);
  line-height: 1.6;
  border-radius: 14px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.action-btn {
  padding: 0.75rem 1rem;
  min-width: 96px;
  border: 1px solid transparent;
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
  color: #ffd7ae;
  border-color: rgba(255, 179, 107, 0.24);
}

.action-btn.danger {
  background: rgba(255, 143, 143, 0.12);
  color: #ffc1c1;
  border-color: rgba(255, 143, 143, 0.24);
}

@media (max-width: 768px) {
  .page-header,
  .panel-header,
  .task-top,
  .progress-info,
  .worker-item {
    flex-direction: column;
    align-items: stretch;
  }

  .actions,
  .filter-row,
  .bulk-row {
    flex-direction: column;
  }

  .action-btn,
  .ghost-btn,
  .filter-chip {
    width: 100%;
  }
}
</style>
