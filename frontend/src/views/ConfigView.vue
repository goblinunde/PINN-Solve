<template>
  <div class="config-view">
    <section class="tech-card hero-card">
      <div>
        <h2 class="tech-title">{{ t('config.title') }}</h2>
        <p class="page-subtitle">{{ t('config.subtitle') }}</p>
      </div>
      <div class="hero-pills">
        <span class="pill">{{ currentPde?.name || '--' }}</span>
        <span class="pill">{{ optimizerLabel }}</span>
        <span class="pill">{{ networkSummary }}</span>
      </div>
    </section>

    <div v-if="error" class="error-box">{{ error }}</div>
    <div v-if="usingFallbackCatalog" class="note-box">{{ t('config.catalogFallback') }}</div>

    <div class="config-grid">
      <section class="tech-card panel-card">
        <div class="section-header">
          <div>
            <h3>{{ t('config.problemPreset') }}</h3>
            <p class="section-caption">{{ equationPreview }}</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-section wide">
            <label>{{ t('config.name') }}</label>
            <input
              v-model="form.name"
              :placeholder="t('config.namePlaceholder')"
              class="tech-input"
            />
          </div>

          <div class="form-section">
            <label>{{ t('config.problemPreset') }}</label>
            <select v-model="form.pde_kind" class="tech-input" @change="syncProblemDefaults">
              <option v-for="preset in pdePresets" :key="preset.key" :value="preset.key">
                {{ preset.name }}
              </option>
            </select>
          </div>

          <div class="form-section">
            <label>{{ t('config.optimizer') }}</label>
            <select v-model="form.optimizer" class="tech-input">
              <option v-for="option in optimizerOptions" :key="option.key" :value="option.key">
                {{ option.name }}
              </option>
            </select>
          </div>

          <div class="form-section">
            <label>{{ t('config.outputActivation') }}</label>
            <select v-model="form.output_activation" class="tech-input">
              <option v-for="option in outputActivationOptions" :key="option.key" :value="option.key">
                {{ option.name }}
              </option>
            </select>
          </div>

          <div class="form-section wide">
            <span class="field-note">{{ currentPde?.description || t('config.problemPresetHelp') }}</span>
          </div>

          <div v-if="form.pde_kind === 'poisson_2d'" class="form-section">
            <label>{{ t('config.sourceType') }}</label>
            <select v-model="form.source_type" class="tech-input">
              <option v-for="option in sourceTypeOptions" :key="option.key" :value="option.key">
                {{ option.name }}
              </option>
            </select>
          </div>

          <div v-if="form.pde_kind === 'heat_1d'" class="form-section">
            <label>{{ t('config.alpha') }}</label>
            <input v-model.number="form.alpha" type="number" step="0.01" min="0.001" class="tech-input" />
          </div>

          <div v-if="form.pde_kind === 'burgers_1d'" class="form-section">
            <label>{{ t('config.viscosity') }}</label>
            <input
              v-model.number="form.viscosity"
              type="number"
              step="0.001"
              min="0.0001"
              class="tech-input"
            />
          </div>
        </div>
      </section>

      <section class="tech-card panel-card">
        <div class="section-header">
          <div>
            <h3>{{ t('config.trainingParams') }}</h3>
            <p class="section-caption">{{ t('config.trainingParamsHelp') }}</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-section">
            <label>{{ t('config.epochs') }}</label>
            <input v-model.number="form.epochs" type="number" min="1" class="tech-input" />
          </div>

          <div class="form-section">
            <label>{{ t('config.learningRate') }}</label>
            <input v-model.number="form.learning_rate" type="number" step="0.0001" min="0.0001" class="tech-input" />
          </div>

          <div class="form-section">
            <label>{{ t('config.nPoints') }}</label>
            <input v-model.number="form.n_points" type="number" min="16" class="tech-input" />
          </div>

          <div class="form-section">
            <label>{{ t('config.nBoundary') }}</label>
            <input v-model.number="form.n_boundary" type="number" min="8" class="tech-input" />
          </div>

          <div class="form-section">
            <label>{{ t('config.collocationBatchSize') }}</label>
            <input
              v-model.number="form.collocation_batch_size"
              type="number"
              min="1"
              class="tech-input"
            />
          </div>

          <div class="form-section">
            <label>{{ t('config.lambdaBoundary') }}</label>
            <input v-model.number="form.lambda_boundary" type="number" step="0.5" min="0" class="tech-input" />
          </div>
        </div>
      </section>

      <section class="tech-card panel-card builder-card">
        <div class="section-header">
          <div>
            <h3>{{ t('config.networkBuilder') }}</h3>
            <p class="section-caption">{{ t('config.networkBuilderHelp') }}</p>
          </div>
          <button class="ghost-btn" type="button" @click="addLayer">
            {{ t('config.addBlock') }}
          </button>
        </div>

        <div class="preset-row">
          <button
            v-for="preset in networkPresets"
            :key="preset.key"
            type="button"
            class="preset-chip"
            @click="applyNetworkPreset(preset.key)"
          >
            {{ preset.name }}
          </button>
        </div>

        <div class="block-list">
          <article v-for="(layer, index) in hiddenLayers" :key="index" class="block-card">
            <div class="block-header">
              <strong>{{ t('config.block') }} {{ index + 1 }}</strong>
              <button
                type="button"
                class="text-btn"
                :disabled="hiddenLayers.length === 1"
                @click="removeLayer(index)"
              >
                {{ t('config.removeBlock') }}
              </button>
            </div>

            <div class="form-grid compact-grid">
              <div class="form-section">
                <label>{{ t('config.units') }}</label>
                <input v-model.number="layer.size" type="number" min="4" class="tech-input" />
              </div>

              <div class="form-section">
                <label>{{ t('config.activation') }}</label>
                <select v-model="layer.activation" class="tech-input">
                  <option v-for="option in activationOptions" :key="option.key" :value="option.key">
                    {{ option.name }}
                  </option>
                </select>
              </div>

              <label class="toggle-card">
                <span>{{ t('config.residual') }}</span>
                <input v-model="layer.residual" type="checkbox" />
              </label>
            </div>
          </article>
        </div>
      </section>

      <section class="tech-card panel-card summary-card">
        <div class="section-header">
          <div>
            <h3>{{ t('config.summary') }}</h3>
            <p class="section-caption">{{ t('config.summaryHelp') }}</p>
          </div>
        </div>

        <div class="summary-list">
          <div class="summary-item">
            <span>{{ t('config.equationPreview') }}</span>
            <strong>{{ equationPreview }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ t('config.network') }}</span>
            <strong>{{ networkSummary }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ t('config.hiddenBlocks') }}</span>
            <strong>{{ hiddenLayers.length }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ t('config.residualBlocks') }}</span>
            <strong>{{ residualBlocks }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ t('config.inputDim') }}</span>
            <strong>{{ currentPde?.input_dim || 2 }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ t('config.outputDim') }}</span>
            <strong>1</strong>
          </div>
        </div>
      </section>
    </div>

    <div class="footer-actions">
      <button @click="submitConfig" class="tech-btn" :disabled="loading || catalogLoading">
        <span class="btn-glow"></span>
        {{ loading ? t('config.training') : t('config.startTraining') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { i18n } from '../locales'
import {
  createTrainingTask,
  fetchProblemCatalog,
  getApiErrorMessage
} from '../api/tasks'

const router = useRouter()
const t = (key) => i18n.t(key)

const fallbackCatalog = {
  pde_presets: [
    {
      key: 'laplace_2d',
      name: '2D Laplace',
      description: 'Steady-state elliptic equation on the unit square.',
      display_equation: 'u_xx + u_yy = 0',
      input_dim: 2,
      defaults: { source_type: 'zero', alpha: 0.1, viscosity: 0.01 }
    },
    {
      key: 'poisson_2d',
      name: '2D Poisson',
      description: 'Elliptic equation with configurable source term.',
      display_equation: 'u_xx + u_yy = f(x, y)',
      input_dim: 2,
      defaults: { source_type: 'sine', alpha: 0.1, viscosity: 0.01 }
    },
    {
      key: 'heat_1d',
      name: '1D Heat',
      description: 'Transient diffusion in x-t space with zero boundary walls.',
      display_equation: 'u_t - alpha * u_xx = 0',
      input_dim: 2,
      defaults: { source_type: 'zero', alpha: 0.1, viscosity: 0.01 }
    },
    {
      key: 'burgers_1d',
      name: '1D Burgers',
      description: 'Nonlinear transport-diffusion benchmark in x-t space.',
      display_equation: 'u_t + u u_x - nu * u_xx = 0',
      input_dim: 2,
      defaults: { source_type: 'zero', alpha: 0.1, viscosity: 0.01 }
    }
  ],
  optimizers: [
    { key: 'adam', name: 'Adam' },
    { key: 'sgd', name: 'SGD' }
  ],
  activations: [
    { key: 'tanh', name: 'Tanh' },
    { key: 'relu', name: 'ReLU' },
    { key: 'sigmoid', name: 'Sigmoid' },
    { key: 'softplus', name: 'Softplus' },
    { key: 'linear', name: 'Linear' }
  ],
  source_types: [
    { key: 'zero', name: 'Zero' },
    { key: 'one', name: 'Constant One' },
    { key: 'sine', name: 'Sine Source' }
  ],
  output_activations: [
    { key: 'linear', name: 'Linear' },
    { key: 'tanh', name: 'Tanh' },
    { key: 'sigmoid', name: 'Sigmoid' }
  ],
  network_presets: [
    {
      key: 'baseline',
      name: 'Baseline',
      hidden_layers: [
        { size: 32, activation: 'tanh', residual: false },
        { size: 32, activation: 'tanh', residual: false }
      ]
    },
    {
      key: 'wide',
      name: 'Wide',
      hidden_layers: [
        { size: 64, activation: 'tanh', residual: false },
        { size: 64, activation: 'tanh', residual: false }
      ]
    },
    {
      key: 'deep',
      name: 'Deep',
      hidden_layers: [
        { size: 32, activation: 'tanh', residual: false },
        { size: 32, activation: 'tanh', residual: false },
        { size: 32, activation: 'tanh', residual: false },
        { size: 32, activation: 'tanh', residual: false }
      ]
    },
    {
      key: 'residual',
      name: 'Residual',
      hidden_layers: [
        { size: 48, activation: 'tanh', residual: false },
        { size: 48, activation: 'tanh', residual: true },
        { size: 48, activation: 'tanh', residual: true }
      ]
    }
  ]
}

const cloneLayers = (layers) => layers.map((layer) => ({ ...layer }))

const catalog = ref(fallbackCatalog)
const catalogLoading = ref(false)
const usingFallbackCatalog = ref(false)
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '2D Laplace',
  pde_kind: 'laplace_2d',
  optimizer: 'adam',
  output_activation: 'linear',
  epochs: 1000,
  learning_rate: 0.001,
  n_points: 256,
  n_boundary: 128,
  collocation_batch_size: 64,
  lambda_boundary: 10,
  source_type: 'zero',
  alpha: 0.1,
  viscosity: 0.01
})

const hiddenLayers = ref(cloneLayers(fallbackCatalog.network_presets[0].hidden_layers))

const pdePresets = computed(() => catalog.value.pde_presets || [])
const optimizerOptions = computed(() => catalog.value.optimizers || [])
const activationOptions = computed(() => catalog.value.activations || [])
const sourceTypeOptions = computed(() => catalog.value.source_types || [])
const outputActivationOptions = computed(() => catalog.value.output_activations || [])
const networkPresets = computed(() => catalog.value.network_presets || [])
const currentPde = computed(() => pdePresets.value.find((preset) => preset.key === form.value.pde_kind))
const residualBlocks = computed(() => hiddenLayers.value.filter((layer) => layer.residual).length)
const networkSummary = computed(() => {
  const inputDim = currentPde.value?.input_dim || 2
  const blocks = hiddenLayers.value.map((layer) => (layer.residual ? `${layer.size}R` : `${layer.size}`))
  return [inputDim, ...blocks, 1].join(' -> ')
})
const optimizerLabel = computed(() => {
  return optimizerOptions.value.find((option) => option.key === form.value.optimizer)?.name || form.value.optimizer
})
const equationPreview = computed(() => {
  if (form.value.pde_kind === 'poisson_2d') {
    const sources = {
      zero: '0',
      one: '1',
      sine: 'sin(pi x) sin(pi y)'
    }
    return `u_xx + u_yy = ${sources[form.value.source_type] || 'f(x, y)'}`
  }

  if (form.value.pde_kind === 'heat_1d') {
    return `u_t - ${Number(form.value.alpha).toPrecision(3)} u_xx = 0`
  }

  if (form.value.pde_kind === 'burgers_1d') {
    return `u_t + u u_x - ${Number(form.value.viscosity).toPrecision(3)} u_xx = 0`
  }

  return currentPde.value?.display_equation || 'u_xx + u_yy = 0'
})

const syncProblemDefaults = () => {
  const preset = currentPde.value
  if (!preset) return

  const defaults = preset.defaults || {}
  form.value.source_type = defaults.source_type || form.value.source_type
  form.value.alpha = defaults.alpha ?? form.value.alpha
  form.value.viscosity = defaults.viscosity ?? form.value.viscosity

  if (!form.value.name || pdePresets.value.some((item) => item.name === form.value.name)) {
    form.value.name = preset.name
  }
}

const applyNetworkPreset = (presetKey) => {
  const preset = networkPresets.value.find((item) => item.key === presetKey)
  if (!preset) return
  hiddenLayers.value = cloneLayers(preset.hidden_layers || [])
}

const addLayer = () => {
  hiddenLayers.value.push({
    size: 32,
    activation: 'tanh',
    residual: false
  })
}

const removeLayer = (index) => {
  if (hiddenLayers.value.length === 1) return
  hiddenLayers.value.splice(index, 1)
}

const loadCatalog = async () => {
  catalogLoading.value = true

  try {
    const response = await fetchProblemCatalog()
    catalog.value = response
    usingFallbackCatalog.value = false
    if (!pdePresets.value.some((preset) => preset.key === form.value.pde_kind)) {
      form.value.pde_kind = pdePresets.value[0]?.key || 'laplace_2d'
    }
    syncProblemDefaults()
  } catch (err) {
    usingFallbackCatalog.value = true
  } finally {
    catalogLoading.value = false
  }
}

const submitConfig = async () => {
  loading.value = true
  error.value = ''

  try {
    const normalizedLayers = hiddenLayers.value.map((layer) => ({
      size: Math.max(4, Number(layer.size) || 32),
      activation: layer.activation || 'tanh',
      residual: Boolean(layer.residual)
    }))
    const inputDim = currentPde.value?.input_dim || 2
    const layers = [inputDim, ...normalizedLayers.map((layer) => layer.size), 1]

    const solverConfig = {
      network: {
        input_dim: inputDim,
        hidden_layers: normalizedLayers,
        output_dim: 1,
        output_activation: form.value.output_activation
      },
      optimizer: form.value.optimizer,
      learning_rate: Number(form.value.learning_rate),
      pde: {
        kind: form.value.pde_kind,
        source_type: form.value.source_type,
        alpha: Number(form.value.alpha),
        viscosity: Number(form.value.viscosity)
      },
      epsilon: 0.0001,
      lambda_boundary: Number(form.value.lambda_boundary),
      collocation_batch_size: Math.max(1, Number(form.value.collocation_batch_size))
    }

    const response = await createTrainingTask({
      name: form.value.name || currentPde.value?.name || 'PINN Training Task',
      pde: equationPreview.value,
      layers,
      learning_rate: Number(form.value.learning_rate),
      epochs: Math.max(1, Number(form.value.epochs)),
      n_points: Math.max(16, Number(form.value.n_points)),
      n_boundary: Math.max(8, Number(form.value.n_boundary)),
      solver_config: solverConfig
    })

    router.push(`/monitor?task_id=${response.task_id}`)
  } catch (err) {
    error.value = `${t('config.submitFailed')}: ${getApiErrorMessage(err)}`
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  syncProblemDefaults()
  loadCatalog()
})
</script>

<style scoped>
.config-view {
  max-width: 1320px;
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

.hero-card,
.panel-card {
  margin-bottom: 1.5rem;
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

.page-subtitle,
.section-caption,
.field-note {
  color: #8aa1d6;
  line-height: 1.6;
}

.hero-pills,
.preset-row,
.footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-start;
}

.pill,
.preset-chip {
  background: rgba(0, 150, 255, 0.12);
  border: 1px solid rgba(0, 150, 255, 0.28);
  color: #dff6ff;
  border-radius: 999px;
  padding: 0.55rem 0.95rem;
  font-size: 0.9rem;
}

.preset-chip,
.ghost-btn,
.text-btn {
  cursor: pointer;
  transition: all 0.25s;
}

.preset-chip:hover,
.ghost-btn:hover,
.text-btn:hover {
  transform: translateY(-1px);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
}

.builder-card {
  grid-column: span 2;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  margin: 0;
  color: #f4fbff;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
}

.compact-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.wide {
  grid-column: span 2;
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

.ghost-btn,
.text-btn {
  border: 1px solid rgba(0, 150, 255, 0.3);
  background: rgba(0, 150, 255, 0.12);
  color: #00d4ff;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-weight: 600;
}

.text-btn {
  padding: 0.45rem 0.7rem;
}

.text-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.block-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.block-card,
.summary-item,
.toggle-card {
  background: rgba(9, 20, 45, 0.72);
  border: 1px solid rgba(0, 150, 255, 0.16);
  border-radius: 14px;
}

.block-card {
  padding: 1rem;
}

.block-header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
  color: #f4fbff;
}

.toggle-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 1rem;
  color: #dff6ff;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.summary-item {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  color: #8aa1d6;
}

.summary-item strong {
  color: #f4fbff;
  line-height: 1.5;
}

.tech-btn {
  min-width: 280px;
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

.error-box,
.note-box {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
}

.error-box {
  background: rgba(255, 50, 50, 0.1);
  border: 1px solid rgba(255, 50, 50, 0.3);
  color: #ff6b6b;
}

.note-box {
  background: rgba(255, 185, 40, 0.1);
  border: 1px solid rgba(255, 185, 40, 0.25);
  color: #ffd98a;
}

@media (max-width: 980px) {
  .config-grid,
  .form-grid,
  .compact-grid,
  .summary-list {
    grid-template-columns: 1fr;
  }

  .builder-card,
  .wide {
    grid-column: span 1;
  }

  .hero-card,
  .section-header {
    flex-direction: column;
  }
}
</style>
