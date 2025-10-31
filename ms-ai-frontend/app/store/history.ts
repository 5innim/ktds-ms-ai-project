import { defineStore } from 'pinia'

export const useHistoryStore = defineStore('historyStore', {
  state: () => ({
    prevRoute: ''
  }),
  actions: {
    setPrevRoute(route: string) {
      this.prevRoute = route;
    }
  }
});