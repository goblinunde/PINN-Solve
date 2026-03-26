export default {
  nav: {
    config: '问题配置',
    monitor: '训练监控',
    results: '求解结果',
    history: '历史记录'
  },
  config: {
    title: '问题配置',
    name: '问题名称',
    namePlaceholder: '例: 2D Laplace方程',
    pde: 'PDE方程',
    pdePlaceholder: '例: u_xx + u_yy = 0',
    network: '网络结构',
    networkPlaceholder: '例: 2,32,32,32,1',
    epochs: '训练轮数',
    learningRate: '学习率',
    startTraining: '开始训练',
    training: '训练中...'
  },
  monitor: {
    title: '训练监控',
    currentLoss: '当前损失',
    progress: '训练进度',
    status: '状态',
    viewResults: '查看结果',
    statusRunning: '运行中',
    statusCompleted: '已完成'
  },
  results: {
    title: '求解结果',
    taskId: '任务ID',
    visualization: '3D可视化'
  },
  history: {
    title: '历史记录',
    name: '名称',
    status: '状态'
  }
}
