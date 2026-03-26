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
    colorscale: [
      [0, '#0a0e27'],
      [0.2, '#1a1f3a'],
      [0.4, '#0096ff'],
      [0.6, '#00d4ff'],
      [0.8, '#00ff88'],
      [1, '#ffff00']
    ],
    contours: {
      z: {
        show: true,
        usecolormap: true,
        highlightcolor: '#00d4ff',
        project: { z: true }
      }
    }
  }]
  
  const layout = {
    title: {
      text: 'PDE Solution 3D Visualization',
      font: { color: '#00d4ff', size: 18 }
    },
    paper_bgcolor: 'rgba(0, 0, 0, 0)',
    plot_bgcolor: 'rgba(10, 14, 39, 0.5)',
    scene: {
      xaxis: { 
        title: 'x',
        color: '#a0a0a0',
        gridcolor: 'rgba(0, 150, 255, 0.2)',
        backgroundcolor: 'rgba(10, 14, 39, 0.5)'
      },
      yaxis: { 
        title: 'y',
        color: '#a0a0a0',
        gridcolor: 'rgba(0, 150, 255, 0.2)',
        backgroundcolor: 'rgba(10, 14, 39, 0.5)'
      },
      zaxis: { 
        title: 'u',
        color: '#a0a0a0',
        gridcolor: 'rgba(0, 150, 255, 0.2)',
        backgroundcolor: 'rgba(10, 14, 39, 0.5)'
      },
      bgcolor: 'rgba(10, 14, 39, 0.5)'
    },
    margin: { t: 50, r: 0, b: 0, l: 0 },
    font: { color: '#e0e0e0' }
  }
  
  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false
  }
  
  Plotly.newPlot(plotContainer.value, data, layout, config)
}

onMounted(updatePlot)
watch(() => [props.x, props.y, props.u], updatePlot, { deep: true })
</script>

<style scoped>
.plot-container {
  width: 100%;
  height: 600px;
  border-radius: 12px;
  overflow: hidden;
}
</style>
