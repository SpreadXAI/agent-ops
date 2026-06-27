<template>
  <div class="card flex gap-4 p-4 transition hover:shadow-md">
    <img :src="account.avatar_url" :alt="account.handle" class="h-16 w-16 shrink-0 rounded-full bg-slate-100" />
    <div class="min-w-0 flex-1">
      <div class="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div class="font-semibold text-slate-900">{{ account.display_name }}</div>
          <a
            :href="account.profile_url"
            target="_blank"
            rel="noopener"
            class="text-sm text-brand-600 hover:underline"
          >
            @{{ account.handle }}
          </a>
        </div>
        <span class="badge" :class="tierClass">{{ tierLabel }}</span>
      </div>
      <p class="mt-2 line-clamp-2 text-sm text-slate-600">{{ account.bio }}</p>
      <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <span>{{ account.followers.toLocaleString() }} 粉丝</span>
        <span>¥{{ Number(account.price).toFixed(1) }}</span>
        <span class="capitalize">{{ account.platform }}</span>
      </div>
      <div v-if="$slots.default" class="mt-4">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SocialAccount } from '@/api/client'

const props = defineProps<{ account: SocialAccount }>()

const tierLabel = computed(() => {
  const map = { basic: '基础', standard: '标准', premium: '高级' }
  return map[props.account.tier]
})

const tierClass = computed(() => {
  const map = {
    basic: 'bg-slate-100 text-slate-700',
    standard: 'bg-blue-100 text-blue-700',
    premium: 'bg-amber-100 text-amber-800',
  }
  return map[props.account.tier]
})
</script>
