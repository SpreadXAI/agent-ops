<template>
  <AccountCard v-for="a in accounts" :key="a.id" :account="a">
    <slot :account="a" />
  </AccountCard>
</template>

<script setup lang="ts">
import AccountCard from './AccountCard.vue'
import type { SocialAccount } from '@/api/client'

defineProps<{ accounts: SocialAccount[] }>()
</script>
