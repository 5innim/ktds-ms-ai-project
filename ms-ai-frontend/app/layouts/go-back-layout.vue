<template>
  <header>
    <v-icon size="30" @click="goBack" class="elm-1 etm-1" style="cursor: pointer;">
      mdi-arrow-left
    </v-icon>
  </header>
  <scroll-layout>
    <slot />
  </scroll-layout>
</template>

<script lang="ts" setup>
import { useRouter } from "vue-router";
import { useHistoryStore } from '@/store/history';
import ScrollLayout from "./scroll-layout.vue";

const router = useRouter();

const historyStore = useHistoryStore()
const prevRoute = computed(() => historyStore.prevRoute)

const goBack = () => {
  router.push(prevRoute.value)
}
</script>

<style scoped lang="scss">
@use "@/assets/scss/color.scss" as color; 

header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 1rem 1.5rem;

  // Glassmorphism Effect
  background-color: rgba(255, 255, 255, 1); // $bg-primary with alpha
  backdrop-filter: blur(10px);
  
  // Add a bottom border to distinguish from content
  border-bottom: 1px solid color.$border-glass;
}

.v-icon {
  color: color.$text-secondary;
  transition: color 0.2s ease;

  &:hover {
    color: color.$text-primary;
  }
}
</style>
