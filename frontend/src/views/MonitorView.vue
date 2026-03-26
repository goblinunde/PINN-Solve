<template>
  <div class="monitor-view">
    <h2>训练监控</h2>
    <div class="metrics">
      <div class="metric-card">
        <h3>当前损失</h3>
        <p class="metric-value">{{ currentLoss.toFixed(6) }}</p>
      </div>
      <div class="metric-card">
        <h3>训练进度</h3>
        <p class="metric-value">{{ (progress * 100).toFixed(0) }}%</p>
      </div>
      <div class="metric-card">
        <h3>状态</h3>
        <p class="metric-value status">{{ status }}</p>
      </div>
    </div>
    <LossChart :losses="losses" />
    <div class="actions">
      <button @click="viewResults" class="btn-primary" v-if="status === 'completed'">
        查看结果
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import LossChart from '../components/LossChart.vue'

const route = useRoute()
const router = useRouter()

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
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
}

.metric-card h3 {
  margin: 0 0 0.5rem 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.metric-value {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
  color: #3498db;
}

.metric-value.status {
  text-transform: capitalize;
  color: #27ae60;
}

.actions {
  margin-top: 2rem;
  text-align: center;
}

.btn-primary {
  background: #27ae60;
  color: white;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
}

.btn-primary:hover {
  background: #229954;
}
</style>
