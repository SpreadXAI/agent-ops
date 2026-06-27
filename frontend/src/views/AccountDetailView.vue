<template>
  <div v-if="loading" class="text-slate-500">加载中…</div>
  <div v-else-if="!account" class="text-red-600">账号不存在</div>
  <div v-else class="grid gap-6 lg:grid-cols-2">
    <AccountCard :account="account" />

    <div class="card space-y-4 p-6">
      <h2 class="font-semibold">Tactile 对接</h2>
      <p class="text-sm text-slate-500">
        填写 Twitter 会话 Cookie，保存后点「立即执行」将派发到 Tactile 生产环境执行。
      </p>
      <div>
        <label class="mb-1 block text-sm font-medium">Session Cookie</label>
        <textarea
          v-model="sessionCookie"
          class="input min-h-[80px] font-mono text-xs"
          placeholder="auth_token=...; ct0=..."
        />
        <p v-if="account.has_cookie" class="mt-1 text-xs text-green-600">已保存 Cookie</p>
        <p v-if="account.tactile_agent_id" class="mt-1 text-xs text-slate-500">
          专属 Tactile Agent: {{ account.tactile_agent_id }}
        </p>
        <p v-if="account.tactile_last_work_id" class="mt-1 text-xs text-slate-500">
          最近 Tactile work_id: {{ account.tactile_last_work_id }}
        </p>
      </div>
      <div class="flex flex-wrap gap-3">
        <button class="btn-primary" :disabled="savingCookie" @click="saveCookie">
          {{ savingCookie ? '保存中…' : '保存 Cookie' }}
        </button>
        <button
          class="rounded-lg border border-brand-600 px-4 py-2 text-sm font-medium text-brand-600 hover:bg-brand-50 disabled:opacity-50"
          :disabled="running || !account.has_cookie && !sessionCookie.trim()"
          @click="runNow"
        >
          {{ running ? '派发中…' : '立即执行' }}
        </button>
      </div>
      <p v-if="cookieMsg" class="text-sm text-green-600">{{ cookieMsg }}</p>
      <p v-if="runMsg" class="text-sm" :class="runError ? 'text-red-600' : 'text-green-600'">{{ runMsg }}</p>
    </div>

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
const sessionCookie = ref('')
const loading = ref(true)
const saving = ref(false)
const adding = ref(false)
const savingCookie = ref(false)
const running = ref(false)
const saveMsg = ref('')
const cookieMsg = ref('')
const runMsg = ref('')
const runError = ref(false)
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

async function saveCookie() {
  if (!auth.token || !sessionCookie.value.trim()) return
  savingCookie.value = true
  cookieMsg.value = ''
  try {
    account.value = await api.saveCookie(auth.token, accountId, sessionCookie.value.trim())
    cookieMsg.value = 'Cookie 已保存'
  } catch (e) {
    cookieMsg.value = e instanceof Error ? e.message : '保存失败'
  }
  savingCookie.value = false
}

async function runNow() {
  if (!auth.token) return
  if (!account.value?.has_cookie && !sessionCookie.value.trim()) return
  running.value = true
  runMsg.value = ''
  runError.value = false
  try {
    if (sessionCookie.value.trim() && !account.value?.has_cookie) {
      account.value = await api.saveCookie(auth.token, accountId, sessionCookie.value.trim())
    }
    const result = await api.runAccount(auth.token, accountId)
    runMsg.value = `已派发 work_id=${result.tactile_work_id ?? '—'} session=${result.tactile_session_id ?? '—'}`
    if (account.value && result.tactile_work_id) {
      account.value.tactile_last_work_id = result.tactile_work_id
    }
  } catch (e) {
    runError.value = true
    runMsg.value = e instanceof Error ? e.message : '执行失败'
  }
  running.value = false
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
