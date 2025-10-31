import { useHistoryStore } from '@/store/history';

export default defineNuxtRouteMiddleware((to, from) => {
    const historyStore = useHistoryStore()

    console.log(from.fullPath)
    if (from.fullPath) {
        historyStore.setPrevRoute(from.fullPath)
    }
})
