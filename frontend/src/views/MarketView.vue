<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <p class="text-sm text-slate-500">共 {{ accounts.length }} 个可购账号（本页）</p>
      <div class="flex gap-2">
        <button class="btn-secondary" :disabled="skip === 0" @click="prevPage">上一页</button>
        <button class="btn-secondary" :disabled="accounts.length < pageSize" @click="nextPage">下一页</button>
      </div>
    </div>
    <div v-if="loading" class="text-slate-500">加载中…</div>
    <div v-else class="grid gap-4 lg:grid-cols-2">
      <AccountCard v-for="a in accounts" :key="a.id" :account="a">
        <button class="btn-primary" :disabled="purchasing === a.id" @click="purchase(a.id)">
          {{ purchasing === a.id ? '购买中…' : '购买账号' }}
        </button>
      </AccountCard>
    </div>
    <p v-if="message" class="mt-4 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AccountCard from '@/components/AccountCard.vue'
import { api, type SocialAccount } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const accounts = ref<SocialAccount[]>([])
const loading = ref(true)
const skip = ref(0)
const pageSize = 20
const purchasing = ref<number | null>(null)
const message = ref('')

async function load() {
  if (!auth.token) return
  loading.value = true
  accounts.value = await api.marketAccounts(auth.token, skip.value, pageSize)
  loading.value = false
}

async function purchase(id: number) {
  if (!auth.token) return
  purchasing.value = id
  try {
    await api.purchase(auth.token, id)
    message.value = '购买成功，可在「我的账号」查看'
    await load()
  } catch (e) {
    message.value = e instanceof Error ? e.message : '购买失败'
  } finally {
    purchasing.value = null
  }
}

function prevPage() {
  skip.value = Math.max(0, skip.value - pageSize)
  load()
}

function nextPage() {
  skip.value += pageSize
  load()
}

onMounted(load)
</script>
