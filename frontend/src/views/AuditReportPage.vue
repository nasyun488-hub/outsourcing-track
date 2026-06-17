<template>
  <div class="audit-page">
    <van-nav-bar title="操作审计报表" left-arrow @click-left="router.back()" />

    <section class="summary-card">
      <div class="section-title">审计总览</div>
      <div class="summary-grid">
        <div class="summary-item">
          <div class="num">{{ summary.total_logs }}</div>
          <div class="label">总操作数</div>
        </div>
        <div class="summary-item">
          <div class="num">{{ Object.keys(summary.action_type_counts || {}).length }}</div>
          <div class="label">动作类型</div>
        </div>
      </div>
      <div class="action-tags">
        <van-tag v-for="(count, action) in summary.action_type_counts" :key="action" type="primary" plain>
          {{ action }}：{{ count }}
        </van-tag>
      </div>
    </section>

    <section class="filter-card">
      <van-field v-model="filters.action_type" label="动作" placeholder="如 RECEIVE / MOM_IMPORT" clearable />
      <van-field v-model="filters.user_id" label="用户ID" placeholder="按用户过滤" clearable />
      <div class="filter-actions">
        <van-button type="primary" block @click="loadData">查询</van-button>
        <van-button plain type="success" block @click="exportExcel">导出审计Excel</van-button>
      </div>
    </section>

    <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
      <van-cell v-for="log in logs" :key="log.log_id" :title="`${log.action_type} · ${log.target_table}`" :label="formatLog(log)">
        <template #value>{{ log.user_name || log.user_id }}</template>
      </van-cell>
    </van-list>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api'

const router = useRouter()
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const logs = ref<any[]>([])
const summary = reactive<any>({ total_logs: 0, action_type_counts: {}, user_counts: [] })
const filters = reactive({ action_type: '', user_id: '' })

const queryParams = () => ({
  action_type: filters.action_type || undefined,
  user_id: filters.user_id || undefined
})

const loadSummary = async () => {
  const data = await request.get('/audit/summary')
  Object.assign(summary, data)
}

const loadData = async () => {
  page.value = 1
  finished.value = false
  logs.value = []
  await loadMore()
  await loadSummary()
}

const loadMore = async () => {
  loading.value = true
  const data = await request.get('/audit/logs', { params: { page: page.value, page_size: 20, ...queryParams() } })
  logs.value.push(...(data.items || []))
  finished.value = logs.value.length >= data.total
  page.value += 1
  loading.value = false
}

const exportExcel = () => {
  const params = new URLSearchParams()
  Object.entries(queryParams()).forEach(([key, value]) => {
    if (value) params.set(key, String(value))
  })
  window.open(`/api/audit/export?${params.toString()}`, '_blank')
}

const formatLog = (log: any) => {
  return `${log.created_at || ''}｜对象 ${log.target_id}｜IP ${log.ip_address || '-'}`
}

onMounted(loadData)
</script>

<style scoped>
.audit-page { min-height: 100vh; background: #f5f7fb; padding-bottom: 20px; }
.summary-card, .filter-card { margin: 12px; padding: 14px; border-radius: 14px; background: #fff; }
.section-title { font-size: 17px; font-weight: 800; margin-bottom: 12px; color: #1f2d3d; }
.summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.summary-item { padding: 14px; text-align: center; border-radius: 12px; background: #f2f6ff; }
.num { font-size: 24px; font-weight: 900; color: #2f6bff; }
.label { margin-top: 4px; color: #7b8798; font-size: 12px; }
.action-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.filter-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }
</style>
