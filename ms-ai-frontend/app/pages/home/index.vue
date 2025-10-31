<template>
  <div class="page-container">
    <header class="page-header">
      <h1>MS AI PROJECT</h1>
      <p>환영합니다! 토큰 등록 후 레포트를 받아보세요!</p>
    </header>


    <div class="bento-grid-container">
      <div class="grid-item grid-item-user">
        <div class="item-header">
          <h3>Account</h3>
          <v-icon>mdi-account-circle-outline</v-icon>
        </div>
        <!-- <v-btn to="/token" class="link" variant="text">Manage Token</v-btn> -->
        <router-link to="/token" class="link">Manage Token</router-link>
      </div>
      <!-- Main Item: Repository List -->
      <!-- <div class="grid-item grid-item-main">
        <div v-if="isLoading" class="loading-container">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        </div>
        <div v-else></div>
      </div> -->

    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted} from "vue";
import { useRouter } from "vue-router";
import { useUserInfoStore } from "@/store/user-info";

definePageMeta({
  layout: "transparent-header-layout",
});

const router = useRouter();
const userInfo = useUserInfoStore();
const repositories = ref([]);
const isLoading = ref(true);

onMounted(async () => {
});
</script>

<style scoped lang="scss">
@use "@/assets/scss/color.scss" as color;

.page-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

.page-header {
  margin-bottom: 2rem;

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: color.$text-primary;
  }

  p {
    font-size: 1.125rem;
    color: color.$text-secondary;
  }
}

.bento-grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: auto auto;
  gap: 1.5rem;
  min-width: 820px;
}

.grid-item {
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid color.$border-glass;
  border-radius: 16px;
  padding: 1.5rem;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  color: color.$text-secondary;

  h2 {
    font-size: 1.5rem;
    color: color.$text-primary;
    margin: 0;
  }

  h3 {
    font-size: 1.125rem;
    color: color.$text-primary;
    margin: 0;
  }
}

.grid-item-main {
  grid-column: span 2;
}

.repo-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1rem;
}

.grid-item-user {
  display: flex;
  flex-direction: column;

  .link {
    color: color.$accent-secondary;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
}

.grid-item-stats {
  .stat-number {
    font-size: 3rem;
    font-weight: 700;
    color: color.$text-primary;
  }
}

p,
.link {
  color: color.$text-secondary;
}

/* Scroll Animation */
.repo-card-container {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.repo-card-container.is-visible {
  opacity: 1;
  transform: translateY(0);
}
</style>
