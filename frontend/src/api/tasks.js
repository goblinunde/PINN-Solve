import axios from 'axios'

export const createTrainingTask = async (payload) => {
  const response = await axios.post('/api/train/', payload)
  return response.data
}

export const fetchProblemCatalog = async () => {
  const response = await axios.get('/api/problems/catalog')
  return response.data
}

export const listTrainingTasks = async () => {
  const response = await axios.get('/api/train/')
  return response.data
}

export const bulkDeleteTrainingTasks = async (taskIds) => {
  const response = await axios.post('/api/train/bulk-delete', {
    task_ids: taskIds
  })
  return response.data
}

export const fetchTrainingTask = async (taskId) => {
  const response = await axios.get(`/api/train/${taskId}`)
  return response.data
}

export const fetchTrainingStatus = async (taskId) => {
  const response = await axios.get(`/api/train/${taskId}/status`)
  return response.data
}

export const cancelTrainingTask = async (taskId) => {
  const response = await axios.post(`/api/train/${taskId}/cancel`)
  return response.data
}

export const retryTrainingTask = async (taskId) => {
  const response = await axios.post(`/api/train/${taskId}/retry`)
  return response.data
}

export const deleteTrainingTask = async (taskId) => {
  const response = await axios.delete(`/api/train/${taskId}`)
  return response.data
}

export const fetchTrainingResults = async (taskId) => {
  const response = await axios.get(`/api/results/${taskId}`)
  return response.data
}

export const fetchSystemOverview = async () => {
  const response = await axios.get('/api/system/overview')
  return response.data
}

export const getApiErrorMessage = (error) => {
  return error.response?.data?.detail || error.message || 'Request failed'
}
