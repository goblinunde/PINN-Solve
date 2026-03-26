<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  losses: { type: Array, default: () => [] }
})

const chartContainer = ref(null)

const updateChart = () => {
  if (!chartContainer.value || props.losses.length === 0) return
  
  const data = [{
    y: props.losses,
    type: 'scatter',
    mode: 'lines',
    line: { 
      color: '#00d4ff', 
      width: 3,
      shape: 'spline'
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(0, 212, 255, 0.1)'
  }]
  
  const layout = {
    title: {
      text: 'Training Loss Curve',
      font: { color: '#00d4ff', size: 18, family: 'Segoe UI' }
    },
    paper_bgcolor: 'rgba(0, 0, 0, 0)',
    plot_bgcolor: 'rgba(10, 14, 39, 0.5)',
    xaxis: { 
      title: 'Epoch',
      color: '#a0a0a0',
      gridcolor: 'rgba(0, 150, 255, 0.1)',
      zerolinecolor: 'rgba(0, 150, 255, 0.2)'
    },
    yaxis: { 
      title: 'Loss', 
      type: 'log',
      color: '#a0a0a0',
      gridcolor: 'rgba(0, 150, 255, 0.1)',
      zerolinecolor: 'rgba(0, 150, 255, 0.2)'
    },
    margin: { t: 50, r: 30, b: 50, l: 70 },
    font: { color: '#e0e0e0' }
  }
  
  const config = { 
    responsive: true,
    displayModeBar: false
  }
  
  Plotly.newPlot(chartContainer.value, data, layout, config)
}

onMounted(updateChart)
watch(() => props.losses, updateChart, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
}
</style>
