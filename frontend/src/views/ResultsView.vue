<template>
  <div class="results-view">
    <h2 class="tech-title">{{ t('results.title') }}</h2>
    <div class="info tech-card">
      <p><span class="label">{{ t('results.taskId') }}:</span> <span class="value">{{ taskId }}</span></p>
    </div>
    <div class="viz-container tech-card">
      <h3 class="viz-title">{{ t('results.visualization') }}</h3>
      <SolutionPlot :x="solution.x" :y="solution.y" :u="solution.u" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import SolutionPlot from '../components/SolutionPlot.vue'
import { i18n } from '../locales'

const route = useRoute()
const t = (key) => i18n.t(key)
const taskId = ref(route.query.task_id || 'task-1')

const solution = ref({
  x: [],
  y: [],
  u: []
})

const fetchResults = async () => {
  try {
    const response = await axios.get(`/api/results/${taskId.value}`)
    solution.value = response.data.solution
  } catch (error) {
    console.error('获取结果失败:', error)
  }
}

onMounted(fetchResults)
</script>

<style scoped>
.results-view {
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

.tech-card {
  background: rgba(26, 31, 58, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.3);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  margin-bottom: 2rem;
}

.info {
  padding: 1.5rem;
}

.info p {
  margin: 0;
  font-size: 1.1rem;
}

.label {
  color: #00d4ff;
  font-weight: 600;
}

.value {
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
}

.viz-container {
  padding: 2rem;
}

.viz-title {
  color: #00d4ff;
  margin: 0 0 1.5rem 0;
  font-size: 1.3rem;
  text-align: center;
}
</style>
