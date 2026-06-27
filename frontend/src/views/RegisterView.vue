<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-900 via-slate-900 to-slate-800 p-4">
    <div class="card w-full max-w-md p-8">
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-bold text-slate-900">创建账号</h1>
        <p class="mt-2 text-sm text-slate-500">填写账号信息，无需验证码</p>
      </div>
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">登录账号 *</label>
          <input v-model="form.username" class="input" type="text" required minlength="3" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">显示昵称 *</label>
          <input v-model="form.display_name" class="input" type="text" required />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">邮箱（选填）</label>
          <input v-model="form.email" class="input" type="email" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">密码 *</label>
          <input v-model="form.password" class="input" type="password" required minlength="6" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">确认密码 *</label>
          <input v-model="confirmPassword" class="input" type="password" required />
        </div>
        <p v-if="localError" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{{ localError }}</p>
        <p v-else-if="auth.error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{{ auth.error }}</p>
        <button class="btn-primary w-full" type="submit" :disabled="auth.loading">
          {{ auth.loading ? '注册中…' : '注册并登录' }}
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-slate-500">
        已有账号？
        <RouterLink to="/login" class="font-medium text-brand-600 hover:underline">去登录</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const confirmPassword = ref('')
const localError = ref<string | null>(null)
const form = reactive({
  username: '',
  display_name: '',
  email: '',
  password: '',
})

async function onSubmit() {
  localError.value = null
  if (form.password !== confirmPassword.value) {
    localError.value = '两次密码不一致'
    return
  }
  try {
    await auth.register({
      username: form.username,
      password: form.password,
      display_name: form.display_name,
      email: form.email || undefined,
    })
    router.push({ name: 'dashboard' })
  } catch {
    /* store error */
  }
}
</script>
