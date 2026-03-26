export default {
  nav: {
    config: 'Configuration',
    monitor: 'Monitor',
    results: 'Results',
    history: 'History'
  },
  config: {
    title: 'Problem Configuration',
    name: 'Problem Name',
    namePlaceholder: 'e.g., 2D Laplace Equation',
    pde: 'PDE Equation',
    pdePlaceholder: 'e.g., u_xx + u_yy = 0',
    network: 'Network Structure',
    networkPlaceholder: 'e.g., 2,32,32,32,1',
    epochs: 'Training Epochs',
    learningRate: 'Learning Rate',
    startTraining: 'Start Training',
    training: 'Training...'
  },
  monitor: {
    title: 'Training Monitor',
    currentLoss: 'Current Loss',
    progress: 'Progress',
    status: 'Status',
    viewResults: 'View Results',
    statusRunning: 'Running',
    statusCompleted: 'Completed'
  },
  results: {
    title: 'Solution Results',
    taskId: 'Task ID',
    visualization: '3D Visualization'
  },
  history: {
    title: 'History',
    name: 'Name',
    status: 'Status'
  }
}
