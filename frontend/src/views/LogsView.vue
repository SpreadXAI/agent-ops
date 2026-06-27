<template>
  <div>
    <div v-if="loading" class="text-slate-500">加载中…</div>
    <div v-else-if="!logs.length" class="card p-8 text-center text-slate-500">
      暂无执行日志。购买账号并配置任务后，Tactile 接入后将在此展示关键步骤。
    </div>
    <div v-else class="space-y-3">
      <div v-for="log in logs" :key="log.id" class="card flex gap-4 p-4">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-lg">
          {{ stepIcon(log.step) }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-medium text-slate-900">{{ log.message }}</span>
            <span class="badge bg-slate-100 text-slate-600">{{ log.step }}</span>
            <span v-if="log.account_handle" class="text-xs text-brand-600">@{{ log.account_handle }}</span>
          </div>
          <div class="mt-1 text-xs text-slate-500">{{ formatTime(log.created_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type ExecutionLog } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const logs = ref<ExecutionLog[]>([])
const loading = ref(true)

function stepIcon(step: string) {
  const map: Record<string, string> = {
    login: '🔐',
    browse: '👀',
    action: '⚡',
    report: '📄',
  }
  return map[step] ?? '•'
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(async () => {
  if (!auth.token) return
  logs.value = await api.executionLogs(auth.token)
  loading.value = false
})
</script>
