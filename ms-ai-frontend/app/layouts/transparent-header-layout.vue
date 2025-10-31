<template>
  <scroll-layout>
    <v-app-bar absolute color="transparent" elevation="0">
      <v-spacer></v-spacer>
    </v-app-bar>
    <v-container class="d-flex justify-center align-center fill-height etm-8">
      <slot />
    </v-container>
  </scroll-layout>
</template>

<script lang="ts" setup>
import ScrollLayout from "./scroll-layout.vue";

</script>

<style scoped>
</style>
