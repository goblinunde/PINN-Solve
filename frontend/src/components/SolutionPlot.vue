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
      [0, '#08111d'],
      [0.18, '#123152'],
      [0.42, '#2f79b6'],
      [0.65, '#8be1ff'],
      [0.84, '#ffd08d'],
      [1, '#fff1d1']
    ],
    contours: {
      z: {
        show: true,
        usecolormap: true,
        highlightcolor: '#ffd08d',
        project: { z: true }
      }
    }
  }]
  
  const layout = {
    title: {
      text: 'PDE Solution 3D Visualization',
      font: { color: '#eff6ff', size: 20, family: 'Avenir Next' }
    },
    paper_bgcolor: 'rgba(0, 0, 0, 0)',
    plot_bgcolor: 'rgba(4, 10, 22, 0.48)',
    scene: {
      xaxis: { 
        title: 'x',
        color: '#9cb3ce',
        gridcolor: 'rgba(255, 255, 255, 0.1)',
        backgroundcolor: 'rgba(4, 10, 22, 0.44)'
      },
      yaxis: { 
        title: 'y',
        color: '#9cb3ce',
        gridcolor: 'rgba(255, 255, 255, 0.1)',
        backgroundcolor: 'rgba(4, 10, 22, 0.44)'
      },
      zaxis: { 
        title: 'u',
        color: '#9cb3ce',
        gridcolor: 'rgba(255, 255, 255, 0.1)',
        backgroundcolor: 'rgba(4, 10, 22, 0.44)'
      },
      bgcolor: 'rgba(4, 10, 22, 0.48)'
    },
    margin: { t: 50, r: 0, b: 0, l: 0 },
    font: { color: '#eff6ff' }
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
  border-radius: 18px;
  overflow: hidden;
}
</style>
