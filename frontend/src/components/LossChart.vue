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
      color: '#8be1ff',
      width: 3.5,
      shape: 'spline'
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(87, 184, 255, 0.14)'
  }]
  
  const layout = {
    title: {
      text: 'Training Loss Curve',
      font: { color: '#eff6ff', size: 20, family: 'Avenir Next' }
    },
    paper_bgcolor: 'rgba(0, 0, 0, 0)',
    plot_bgcolor: 'rgba(4, 10, 22, 0.48)',
    xaxis: { 
      title: 'Epoch',
      color: '#9cb3ce',
      gridcolor: 'rgba(255, 255, 255, 0.08)',
      zerolinecolor: 'rgba(255, 255, 255, 0.12)'
    },
    yaxis: { 
      title: 'Loss', 
      type: 'log',
      color: '#9cb3ce',
      gridcolor: 'rgba(255, 255, 255, 0.08)',
      zerolinecolor: 'rgba(255, 255, 255, 0.12)'
    },
    margin: { t: 50, r: 30, b: 50, l: 70 },
    font: { color: '#eff6ff' }
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
  height: 420px;
  border-radius: 18px;
  overflow: hidden;
}
</style>
