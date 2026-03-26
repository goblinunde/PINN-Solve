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
    line: { color: '#3498db', width: 2 }
  }]
  
  const layout = {
    title: '训练损失曲线',
    xaxis: { title: 'Epoch' },
    yaxis: { title: 'Loss', type: 'log' },
    margin: { t: 40, r: 20, b: 40, l: 60 }
  }
  
  Plotly.newPlot(chartContainer.value, data, layout, { responsive: true })
}

onMounted(updateChart)
watch(() => props.losses, updateChart, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
}
</style>
