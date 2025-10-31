<template>
</template>

<script lang="ts" setup>
import { useRouter } from "vue-router";
import { onMounted } from "vue";
import { useUserInfoStore } from "@/store/user-info";

const router = useRouter();

onMounted(async () => {
  try {
    router.push('/home');
  } catch (error) {
    console.log('페이지 접근 불가')
  };
})

</script>

<style></style>
