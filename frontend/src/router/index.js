import { createRouter, createWebHistory } from 'vue-router'
import ConfigView from '../views/ConfigView.vue'
import MonitorView from '../views/MonitorView.vue'
import ResultsView from '../views/ResultsView.vue'
import HistoryView from '../views/HistoryView.vue'
import DatabaseView from '../views/DatabaseView.vue'

const routes = [
  { path: '/', component: ConfigView },
  { path: '/monitor', component: MonitorView },
  { path: '/results', component: ResultsView },
  { path: '/history', component: HistoryView },
  { path: '/database', component: DatabaseView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
