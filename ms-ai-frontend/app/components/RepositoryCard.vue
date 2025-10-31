<template>
  <div class="repo-card" @click="goToRepository">
    <div class="card-content">
      <div class="repo-info">
        <h3 class="repo-name font-mono">{{ repository.name }}</h3>
        <p class="repo-owner">{{ repository.owner }}</p>
      </div>
      <div class="repo-status">
        <v-tooltip :text="repository.emailSub ? '구독 중' : '미구독'">
          <template v-slot:activator="{ props }">
            <v-icon
              v-bind="props"
              :color="repository.emailSub ? '#30C8A2' : '#475569'"
              size="small"
            >
              {{ repository.emailSub ? 'mdi-email-check' : 'mdi-email-outline' }}
            </v-icon>
          </template>
        </v-tooltip>
      </div>
    </div>
    <div class="card-footer">
      <span>View Details</span>
      <v-icon>mdi-arrow-right</v-icon>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  repository: {
    type: Object,
    required: true,
  },
});

const goToRepository = () => {

  router.push('/repository/' + props.repository.id)
};
</script>

<style scoped lang="scss">
@use "@/assets/scss/color.scss" as color; 

.repo-card {
  background: rgba(30, 41, 59, 0.5); // $bg-secondary with alpha
  backdrop-filter: blur(10px);
  border: 1px solid color.$border-glass;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  }
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.repo-info {
  flex: 1;
}

.repo-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: color.$text-primary;
  margin: 0 0 0.25rem 0;
}

.repo-owner {
  font-size: 0.875rem;
  color: color.$text-secondary;
  margin: 0;
}

.repo-status {
  margin-left: 1rem;
}

.card-footer {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  font-size: 0.875rem;
  color: color.$text-secondary;
  opacity: 0;
  transition: opacity 0.3s ease;

  .repo-card:hover & {
    opacity: 1;
  }

  .v-icon {
    margin-left: 0.5rem;
    transition: transform 0.3s ease;
  }

  .repo-card:hover & .v-icon {
    transform: translateX(4px);
  }
}
</style>