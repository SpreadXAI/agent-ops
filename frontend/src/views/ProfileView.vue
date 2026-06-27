<template>
  <div class="card max-w-lg p-6">
    <dl class="space-y-4 text-sm">
      <div class="flex justify-between border-b border-slate-100 pb-3">
        <dt class="text-slate-500">登录账号</dt>
        <dd class="font-medium">{{ auth.user?.username }}</dd>
      </div>
      <div class="flex justify-between border-b border-slate-100 pb-3">
        <dt class="text-slate-500">显示昵称</dt>
        <dd class="font-medium">{{ auth.user?.display_name }}</dd>
      </div>
      <div class="flex justify-between border-b border-slate-100 pb-3">
        <dt class="text-slate-500">邮箱</dt>
        <dd class="font-medium">{{ auth.user?.email || '—' }}</dd>
      </div>
      <div class="flex justify-between border-b border-slate-100 pb-3">
        <dt class="text-slate-500">用户 ID</dt>
        <dd class="font-medium">{{ auth.user?.id }}</dd>
      </div>
      <div class="flex justify-between">
        <dt class="text-slate-500">注册时间</dt>
        <dd class="font-medium">{{ auth.user ? formatTime(auth.user.created_at) : '—' }}</dd>
      </div>
    </dl>
    <p class="mt-6 text-xs text-slate-500">以上为注册时填写的信息，登录后可在各模块查看业务数据。</p>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>
