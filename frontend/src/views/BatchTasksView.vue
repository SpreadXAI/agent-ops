<template>
  <div class="grid gap-6 lg:grid-cols-2">
    <div class="card space-y-4 p-6">
      <h2 class="font-semibold">创建批量任务</h2>
      <p class="text-sm text-slate-500">选择多个已购账号，在同一时间执行相同 Prompt</p>
      <div>
        <label class="mb-1 block text-sm font-medium">任务名称</label>
        <input v-model="form.name" class="input" required />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium">Prompt</label>
        <textarea v-model="form.prompt_text" class="input min-h-[100px] font-mono text-xs" />
      </div>
      <div class="flex gap-3">
        <div>
          <label class="mb-1 block text-xs text-slate-500">开始时间</label>
          <input v-model="form.start_time" class="input" type="time" />
        </div>
        <div>
          <label class="mb-1 block text-xs text-slate-500">时长(分)</label>
          <input v-model.number="form.duration_minutes" class="input w-24" type="number" min="1" max="60" />
        </div>
      </div>
      <div>
        <label class="mb-2 block text-sm font-medium">选择账号</label>
        <div v-if="!myAccounts.length" class="text-sm text-slate-500">请先在市场购买账号</div>
        <div v-else class="max-h-48 space-y-2 overflow-auto rounded-lg border border-slate-200 p-3">
          <label v-for="a in myAccounts" :key="a.id" class="flex cursor-pointer items-center gap-2 text-sm">
            <input v-model="form.account_ids" type="checkbox" :value="a.id" />
            <span>@{{ a.handle }}</span>
          </label>
        </div>
      </div>
      <button class="btn-primary" :disabled="submitting || !form.account_ids.length" @click="submit">
        {{ submitting ? '创建中…' : '创建批量任务' }}
      </button>
      <p v-if="msg" class="text-sm text-green-600">{{ msg }}</p>
    </div>

    <div class="card p-6">
      <h2 class="mb-4 font-semibold">已有批量任务</h2>
      <div v-if="loading" class="text-slate-500">加载中…</div>
      <div v-else-if="!tasks.length" class="text-sm text-slate-500">暂无批量任务</div>
      <div v-else class="space-y-3">
        <div v-for="t in tasks" :key="t.id" class="rounded-lg border border-slate-200 p-4 text-sm">
          <div class="font-medium">{{ t.name }}</div>
          <div class="mt-1 text-slate-500">每天 {{ t.start_time.slice(0, 5) }} · {{ t.duration_minutes }} 分钟</div>
          <div class="mt-1 text-slate-500">{{ t.account_ids.length }} 个账号</div>
          <p class="mt-2 line-clamp-2 text-xs text-slate-600">{{ t.prompt_text || '（无 Prompt）' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, type BatchTask, type SocialAccount } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const myAccounts = ref<SocialAccount[]>([])
const tasks = ref<BatchTask[]>([])
const loading = ref(true)
const submitting = ref(false)
const msg = ref('')
const form = reactive({
  name: '',
  prompt_text: '',
  start_time: '10:00',
  duration_minutes: 30,
  account_ids: [] as number[],
})

async function load() {
  if (!auth.token) return
  myAccounts.value = await api.myAccounts(auth.token)
  tasks.value = await api.batchTasks(auth.token)
  loading.value = false
}

async function submit() {
  if (!auth.token) return
  submitting.value = true
  msg.value = ''
  try {
    await api.createBatchTask(auth.token, {
      ...form,
      start_time: form.start_time + ':00',
      enabled: true,
    })
    msg.value = '批量任务已创建'
    form.name = ''
    form.prompt_text = ''
    form.account_ids = []
    tasks.value = await api.batchTasks(auth.token)
  } catch (e) {
    msg.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
