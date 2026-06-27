<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-900 via-slate-900 to-slate-800 p-4">
    <div class="card w-full max-w-md p-8">
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-bold text-slate-900">Agent Ops</h1>
        <p class="mt-2 text-sm text-slate-500">社交账号任务编排平台 · 测试环境</p>
      </div>
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">账号</label>
          <input v-model="username" class="input" type="text" required autocomplete="username" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">密码</label>
          <input v-model="password" class="input" type="password" required autocomplete="current-password" />
        </div>
        <p v-if="auth.error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{{ auth.error }}</p>
        <button class="btn-primary w-full" type="submit" :disabled="auth.loading">
          {{ auth.loading ? '登录中…' : '登录' }}
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-slate-500">
        还没有账号？
        <RouterLink to="/register" class="font-medium text-brand-600 hover:underline">立即注册</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')

async function onSubmit() {
  try {
    await auth.login(username.value, password.value)
    router.push({ name: 'dashboard' })
  } catch {
    /* error in store */
  }
}
</script>
