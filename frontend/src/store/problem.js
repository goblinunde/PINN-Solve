import { defineStore } from 'pinia'

export const useProblemStore = defineStore('problem', {
  state: () => ({
    currentProblem: null,
    problems: []
  }),
  actions: {
    setProblem(problem) {
      this.currentProblem = problem
    }
  }
})
