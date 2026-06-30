<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="audit-page">
    <QuickNavStrip />
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

    <section class="desktop-only pc-toolbar audit-toolbar">
      <div>
        <h3>审计明细表</h3>
        <p>按动作、用户追溯关键操作，桌面端集中查看时间、对象、用户与 IP。</p>
      </div>
      <div class="pc-actions">
        <input v-model="filters.action_type" class="pc-input" placeholder="动作类型" @keyup.enter="loadData" />
        <input v-model="filters.user_id" class="pc-input" placeholder="用户ID" @keyup.enter="loadData" />
        <button type="button" class="primary" @click="loadData">查询</button>
        <button type="button" @click="exportExcel">导出审计Excel</button>
      </div>
    </section>

    <section class="desktop-only pc-data-table">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>动作</th>
            <th>对象</th>
            <th>用户</th>
            <th>IP</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.log_id">
            <td>{{ log.created_at || '-' }}</td>
            <td>{{ log.action_type }}</td>
            <td>{{ log.target_table }} / {{ log.target_id || '-' }}</td>
            <td>{{ log.user_name || log.user_id || '-' }}</td>
            <td>{{ log.ip_address || '-' }}</td>
            <td><button type="button" class="link-btn" @click="openLogDetail(log)">查看</button></td>
          </tr>
        </tbody>
      </table>
      <van-empty v-if="logs.length === 0 && !loading" description="暂无审计记录" />
    </section>

    <van-list class="mobile-only" v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
      <van-cell v-for="log in logs" :key="log.log_id" :title="`${log.action_type} · ${log.target_table}`" :label="formatLog(log)" @click="openLogDetail(log)">
        <template #value>{{ log.user_name || log.user_id }}</template>
      </van-cell>
    </van-list>

    <van-popup v-model:show="showLogDetail" position="right" class="log-detail-drawer">
      <div class="drawer-head">
        <strong>审计详情</strong>
        <button type="button" class="link-btn" @click="closeLogDetail">关闭</button>
      </div>
      <div v-if="selectedLog" class="detail-grid">
        <span>时间</span><strong>{{ selectedLog.created_at || '-' }}</strong>
        <span>动作</span><strong>{{ selectedLog.action_type }}</strong>
        <span>对象表</span><strong>{{ selectedLog.target_table || '-' }}</strong>
        <span>对象ID</span><strong>{{ selectedLog.target_id || '-' }}</strong>
        <span>用户</span><strong>{{ selectedLog.user_name || selectedLog.user_id || '-' }}</strong>
        <span>IP</span><strong>{{ selectedLog.ip_address || '-' }}</strong>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api'
import QuickNavStrip from '@/components/QuickNavStrip.vue'

const router = useRouter()
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const logs = ref<any[]>([])
const summary = reactive<any>({ total_logs: 0, action_type_counts: {}, user_counts: [] })
const filters = reactive({ action_type: '', user_id: '' })
const selectedLog = ref<any | null>(null)
const showLogDetail = ref(false)

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

const openLogDetail = (log: any) => {
  selectedLog.value = log
  showLogDetail.value = true
}

const closeLogDetail = () => {
  showLogDetail.value = false
  selectedLog.value = null
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
.desktop-only { display: block; }
.mobile-only { display: none; }
.pc-toolbar,
.pc-data-table { margin: 16px 24px; padding: 18px; border-radius: 16px; background: #fff; box-shadow: 0 8px 24px rgba(31, 45, 61, 0.08); }
.pc-toolbar { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.pc-toolbar h3 { margin: 0 0 6px; font-size: 20px; color: #1f2937; }
.pc-toolbar p { margin: 0; color: #667085; font-size: 13px; }
.pc-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.pc-input { min-width: 180px; border: 1px solid #d0d5dd; border-radius: 8px; padding: 8px 10px; }
.pc-actions button,
.link-btn { border: 1px solid #d0d5dd; background: #fff; border-radius: 8px; padding: 8px 12px; color: #344054; cursor: pointer; }
.pc-actions button.primary { color: #fff; border-color: #1e63ff; background: #1e63ff; }
.pc-data-table table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pc-data-table th,
.pc-data-table td { padding: 12px; border-bottom: 1px solid #eef2f7; text-align: left; }
.pc-data-table th { color: #667085; background: #f8fafc; font-weight: 700; }
.link-btn { padding: 6px 10px; color: #1e63ff; border-color: #bfdbfe; }
.log-detail-drawer { width: 420px; max-width: 92vw; height: 100%; padding: 20px; box-sizing: border-box; }
.drawer-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-grid { display: grid; grid-template-columns: 90px 1fr; gap: 12px; font-size: 14px; }
.detail-grid span { color: #667085; }
.detail-grid strong { color: #1f2937; word-break: break-all; }
@media (max-width: 900px) {
  .desktop-only { display: none !important; }
  .mobile-only { display: block; }
}
</style>
