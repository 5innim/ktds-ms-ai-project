import { defineStore } from 'pinia'

export const useTokenValueStore = defineStore('tokenValueStore', {
  state: () => ({
    token: ''
  }),
  actions: {
    setToken(token: string) {
      this.token = token;
    }
  }
})


