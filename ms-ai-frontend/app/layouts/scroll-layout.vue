<template>
  <div class="scroll-content">
      <slot />
  </div>
</template>

<script lang="ts" setup>

</script>

<style scoped>
/* 내부 요소에서만 스크롤 적용 */
.scroll-content {
  width: 100%;
  height: 100vh;
  overflow-y: scroll;
  /* 내부 스크롤 활성화 */
  scrollbar-width: none;
  /* Firefox에서 스크롤바 숨기기 */
  -ms-overflow-style: none;
  /* IE에서 스크롤바 숨기기 */
}

/* Chrome, Safari, Edge에서 스크롤바 숨기기 */
.scroll-content::-webkit-scrollbar {
  display: none;
}
</style>