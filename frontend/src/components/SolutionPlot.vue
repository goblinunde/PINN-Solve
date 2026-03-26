<template>
  <div ref="plotContainer" class="plot-container"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  x: { type: Array, default: () => [] },
  y: { type: Array, default: () => [] },
  u: { type: Array, default: () => [] }
})

const plotContainer = ref(null)

const updatePlot = () => {
  if (!plotContainer.value || props.u.length === 0) return
  
  const data = [{
    x: props.x,
    y: props.y,
    z: props.u,
    type: 'surface',
    colorscale: 'Viridis'
  }]
  
  const layout = {
    title: 'PDE解的3D可视化',
    scene: {
      xaxis: { title: 'x' },
      yaxis: { title: 'y' },
      zaxis: { title: 'u' }
    },
    margin: { t: 40, r: 0, b: 0, l: 0 }
  }
  
  Plotly.newPlot(plotContainer.value, data, layout, { responsive: true })
}

onMounted(updatePlot)
watch(() => [props.x, props.y, props.u], updatePlot, { deep: true })
</script>

<style scoped>
.plot-container {
  width: 100%;
  height: 500px;
}
</style>
