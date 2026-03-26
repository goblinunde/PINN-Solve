<template>
  <div class="results-view">
    <h2>求解结果</h2>
    <div class="info">
      <p>任务ID: {{ taskId }}</p>
    </div>
    <SolutionPlot :x="solution.x" :y="solution.y" :u="solution.u" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import SolutionPlot from '../components/SolutionPlot.vue'

const route = useRoute()
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
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.info {
  margin-bottom: 1rem;
  color: #7f8c8d;
}
</style>
