<template>
  <div v-if="loading" class="text-slate-500">加载中…</div>
  <div v-else-if="!account" class="text-red-600">账号不存在</div>
  <div v-else class="grid gap-6 lg:grid-cols-2">
    <AccountCard :account="account" />

    <div class="card space-y-4 p-6">
      <h2 class="font-semibold">人设 & Prompt</h2>
      <div>
        <label class="mb-1 block text-sm font-medium">人设描述</label>
        <textarea v-model="persona" class="input min-h-[80px]" placeholder="例如：科技博主，语气专业友好" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium">执行 Prompt / Skill</label>
        <textarea
          v-model="promptText"
          class="input min-h-[120px] font-mono text-xs"
          placeholder="描述账号每天要执行的任务…"
        />
      </div>
      <button class="btn-primary" :disabled="saving" @click="savePrompt">
        {{ saving ? '保存中…' : '保存 Prompt' }}
      </button>
      <p v-if="saveMsg" class="text-sm text-green-600">{{ saveMsg }}</p>
    </div>

    <div class="card space-y-4 p-6 lg:col-span-2">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">定时任务（最多 3 个，每次 30 分钟）</h2>
        <span class="text-sm text-slate-500">{{ schedules.length }} / 3</span>
      </div>

      <div v-if="schedules.length" class="space-y-2">
        <div
          v-for="s in schedules"
          :key="s.id"
          class="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3 text-sm"
        >
          <div>
            <span class="font-medium">每天 {{ s.start_time.slice(0, 5) }}</span>
            <span class="ml-2 text-slate-500">持续 {{ s.duration_minutes }} 分钟</span>
            <span v-if="s.enabled" class="badge ml-2 bg-green-100 text-green-700">启用</span>
          </div>
          <button class="text-red-600 hover:underline" @click="removeSchedule(s.id)">删除</button>
        </div>
      </div>

      <form v-if="schedules.length < 3" class="flex flex-wrap items-end gap-3 border-t border-slate-100 pt-4" @submit.prevent="addSchedule">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">开始时间</label>
          <input v-model="newStart" class="input w-36" type="time" required />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">时长（分钟）</label>
          <input v-model.number="newDuration" class="input w-24" type="number" min="1" max="60" />
        </div>
        <button class="btn-primary" type="submit" :disabled="adding">添加定时</button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AccountCard from '@/components/AccountCard.vue'
import { api, type Schedule, type SocialAccount } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const accountId = Number(route.params.id)
const account = ref<SocialAccount | null>(null)
const schedules = ref<Schedule[]>([])
const persona = ref('')
const promptText = ref('')
const loading = ref(true)
const saving = ref(false)
const adding = ref(false)
const saveMsg = ref('')
const newStart = ref('09:00')
const newDuration = ref(30)

async function load() {
  if (!auth.token) return
  const mine = await api.myAccounts(auth.token)
  account.value = mine.find((a) => a.id === accountId) ?? null
  if (!account.value) {
    loading.value = false
    return
  }
  const p = await api.getPrompt(auth.token, accountId)
  if (p) {
    persona.value = p.persona
    promptText.value = p.prompt_text
  }
  schedules.value = await api.listSchedules(auth.token, accountId)
  loading.value = false
}

async function savePrompt() {
  if (!auth.token) return
  saving.value = true
  saveMsg.value = ''
  await api.savePrompt(auth.token, accountId, { persona: persona.value, prompt_text: promptText.value })
  saveMsg.value = '已保存'
  saving.value = false
}

async function addSchedule() {
  if (!auth.token) return
  adding.value = true
  await api.createSchedule(auth.token, accountId, {
    start_time: newStart.value + ':00',
    duration_minutes: newDuration.value,
    enabled: true,
  })
  schedules.value = await api.listSchedules(auth.token, accountId)
  adding.value = false
}

async function removeSchedule(id: number) {
  if (!auth.token) return
  await api.deleteSchedule(auth.token, accountId, id)
  schedules.value = await api.listSchedules(auth.token, accountId)
}

onMounted(load)
</script>
