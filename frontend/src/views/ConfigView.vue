<template>
  <div class="config-view tech-card">
    <h2 class="tech-title">{{ t('config.title') }}</h2>
    <div class="form-grid">
      <div class="form-section">
        <label>{{ t('config.name') }}</label>
        <input v-model="config.name" :placeholder="t('config.namePlaceholder')" class="tech-input" />
      </div>
      <div class="form-section">
        <label>{{ t('config.pde') }}</label>
        <input v-model="config.pde" :placeholder="t('config.pdePlaceholder')" class="tech-input" />
      </div>
      <div class="form-section">
        <label>{{ t('config.network') }}</label>
        <input v-model="layersInput" :placeholder="t('config.networkPlaceholder')" class="tech-input" />
      </div>
      <div class="form-section">
        <label>{{ t('config.epochs') }}</label>
        <input v-model.number="config.epochs" type="number" class="tech-input" />
      </div>
      <div class="form-section">
        <label>{{ t('config.learningRate') }}</label>
        <input v-model.number="config.learning_rate" type="number" step="0.0001" class="tech-input" />
      </div>
    </div>
    <button @click="submitConfig" class="tech-btn" :disabled="loading">
      <span class="btn-glow"></span>
      {{ loading ? t('config.training') : t('config.startTraining') }}
    </button>
    <div v-if="error" class="error-box">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { i18n } from '../locales'

const router = useRouter()
const t = (key) => i18n.t(key)

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
  max-width: 800px;
  margin: 0 auto;
}

.tech-card {
  background: rgba(26, 31, 58, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 150, 255, 0.3);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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

.form-grid {
  display: grid;
  gap: 1.5rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  color: #00d4ff;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.tech-input {
  background: rgba(0, 20, 40, 0.5);
  border: 1px solid rgba(0, 150, 255, 0.3);
  color: #e0e0e0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.tech-input:focus {
  outline: none;
  border-color: rgba(0, 150, 255, 0.8);
  box-shadow: 0 0 20px rgba(0, 150, 255, 0.3);
  background: rgba(0, 20, 40, 0.7);
}

.tech-btn {
  width: 100%;
  margin-top: 2rem;
  background: linear-gradient(135deg, #0096ff 0%, #00d4ff 100%);
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 700;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.tech-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 150, 255, 0.5);
}

.tech-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.error-box {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(255, 50, 50, 0.1);
  border: 1px solid rgba(255, 50, 50, 0.3);
  border-radius: 8px;
  color: #ff6b6b;
}
</style>
