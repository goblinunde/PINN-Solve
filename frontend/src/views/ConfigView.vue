<template>
  <div class="config-view">
    <h2>问题配置</h2>
    <div class="form-section">
      <label>问题名称</label>
      <input v-model="config.name" placeholder="例: 2D Laplace方程" />
    </div>
    <div class="form-section">
      <label>PDE方程</label>
      <input v-model="config.pde" placeholder="例: u_xx + u_yy = 0" />
    </div>
    <div class="form-section">
      <label>网络结构 (逗号分隔)</label>
      <input v-model="layersInput" placeholder="例: 2,32,32,32,1" />
    </div>
    <div class="form-section">
      <label>训练轮数</label>
      <input v-model.number="config.epochs" type="number" />
    </div>
    <div class="form-section">
      <label>学习率</label>
      <input v-model.number="config.learning_rate" type="number" step="0.0001" />
    </div>
    <button @click="submitConfig" class="btn-primary" :disabled="loading">
      {{ loading ? '训练中...' : '开始训练' }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = ref({
  name: '2D Laplace方程',
  pde: 'u_xx + u_yy = 0',
  epochs: 1000,
  learning_rate: 0.001,
  n_points: 100
})

const layersInput = ref('2,32,32,32,1')
const loading = ref(false)
const error = ref('')

const submitConfig = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const layers = layersInput.value.split(',').map(x => parseInt(x.trim()))
    
    const response = await axios.post('/api/train/', {
      layers,
      learning_rate: config.value.learning_rate,
      epochs: config.value.epochs,
      n_points: config.value.n_points
    })
    
    console.log('训练已启动:', response.data)
    router.push(`/monitor?task_id=${response.data.task_id}`)
  } catch (err) {
    error.value = '提交失败: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.config-view {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 600px;
}

.form-section {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.btn-primary {
  background: #3498db;
  color: white;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 1rem;
  background: #fee;
  color: #c33;
  border-radius: 4px;
}
</style>
