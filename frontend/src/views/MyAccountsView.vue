<template>
  <div>
    <div v-if="loading" class="text-slate-500">加载中…</div>
    <div v-else-if="accounts.length === 0" class="card p-8 text-center text-slate-500">
      暂无已购账号，请前往
      <RouterLink to="/market" class="text-brand-600 hover:underline">账号市场</RouterLink>
      购买
    </div>
    <div v-else class="grid gap-4 lg:grid-cols-2">
      <AccountCard v-for="a in accounts" :key="a.id" :account="a">
        <RouterLink :to="`/my-accounts/${a.id}`" class="btn-primary">管理任务</RouterLink>
      </AccountCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AccountCard from '@/components/AccountCard.vue'
import { api, type SocialAccount } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const accounts = ref<SocialAccount[]>([])
const loading = ref(true)

onMounted(async () => {
  if (!auth.token) return
  accounts.value = await api.myAccounts(auth.token)
  loading.value = false
})
</script>
