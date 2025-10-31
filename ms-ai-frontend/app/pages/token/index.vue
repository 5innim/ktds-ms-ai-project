<template>
  <div class="page-container">
    <div class="token-card">
      <!-- Card Header -->
      <div class="card-header">
        <h1>{{ $t('token.registration') }}</h1>
        <p>{{ $t('token.description') }}</p>
      </div>

      <!-- Card Body -->
      <div class="card-body">
        <v-alert v-if="existingToken" type="warning" density="compact" variant="text" class="mb-4">
          {{ $t('token.existingTokenWarning') }}
        </v-alert>
        <label for="token-input" class="input-label font-mono">GitHub Personal Access Token</label>
        <v-text-field id="token-input" v-model="token" :label="$t('token.token')" variant="outlined" class="token-input"
          placeholder="ghp_..."></v-text-field>

        <v-btn :loading="loading" :disabled="loading || success" color="primary" block @click="register"
          class="register-btn">
          <v-icon v-if="success">mdi-check</v-icon>
          <span v-else>{{ $t('token.register') }}</span>
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { registerToken } from '@/utils/token-api';
import { useTokenValueStore } from "@/store/token-value";

definePageMeta({
  layout: "go-back-layout",
  middleware: ['route']
});

const router = useRouter();
const existingToken = ref(false);
const token = ref('');
const loading = ref(false);
const success = ref(false);
const invalidTokenError = ref(false);
const tokenValueStore = useTokenValueStore()

const $t = (key: string) => {
  const translations: { [key: string]: string } = {
    'token.registration': 'GitHub Token',
    'token.description': 'Register your Personal Access Token to get started.',
    'token.existingTokenWarning': '이미 사용중인 토큰이 있습니다. 재등록 시에 기존 사용하던 토큰은 삭제됩니다.',
    'token.token': 'Token',
    'token.register': '토큰 등록',
    'token.invalidTokenError': 'Invalid token. Please check and try again.',
  };
  return translations[key] || key;
};

if (tokenValueStore.token != '') {
  existingToken.value = true 
} else {
  existingToken.value = false
}


const register = async () => {
  if (!token.value) {
    return;
  }

  loading.value = true;
  success.value = false;
  invalidTokenError.value = false;

  try {
    tokenValueStore.setToken(token.value);
    await registerToken(token.value);
    success.value = true;
    // Redirect after a short delay to show success state
    setTimeout(() => router.push("/home"), 1000);

  } catch (error: any) {
    console.error('Error registering token:', error);

  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="scss">
@use "@/assets/scss/color.scss" as color;

.page-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.token-card {
  width: 100%;
  max-width: 550px;
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid color.$border-glass;
  border-radius: 16px;
  color: color.$text-primary;
  overflow: hidden; // Ensures child elements adhere to border radius
}

.card-header {
  padding: 2rem 2rem 1.5rem 2rem;
  border-bottom: 1px solid color.$border-glass;

  h1 {
    font-size: 1.75rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
  }

  p {
    font-size: 1rem;
    color: color.$text-secondary;
    margin: 0;
  }
}

.card-body {
  padding: 2rem;
}

.input-label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: color.$text-secondary;
}

.token-input {
  margin-bottom: 1.5rem;
}

.register-btn {
  height: 50px !important;
  font-size: 1rem;
  font-weight: 500;
  text-transform: none; // Prevents uppercase transformation
}

// Style overrides for Vuetify components
:deep(.v-field) {
  background-color: rgba(15, 23, 42, 0.7) !important;
  color: color.$text-primary;
}

:deep(.v-field__outline) {
  border-color: color.$border-glass !important;
}

:deep(label.v-label) {
  color: color.$text-secondary !important;
}

:deep(.v-alert) {
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
}
</style>
