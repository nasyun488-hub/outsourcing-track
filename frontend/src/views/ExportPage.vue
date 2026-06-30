<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="export-page">
    <QuickNavStrip />
    <van-nav-bar
      title="报表导出中心"
      left-arrow
      @click-left="router.back()"
    />

    <section class="export-hero">
      <div>
        <div class="eyebrow">报表导出中心</div>
        <h2>先预览范围，再生成文件</h2>
        <p>导出预览会展示时间、厂家和订单筛选，减少手机端反复下载。</p>
      </div>
      <van-icon name="description-o" size="34" />
    </section>

    <section class="desktop-only pc-toolbar export-workbench-toolbar">
      <div>
        <h3>导出工作台</h3>
        <p>桌面端先选报表、日期与厂家，再一键生成外协流转 Excel。</p>
      </div>
      <div class="pc-actions">
        <input v-model="orderKeyword" class="pc-input" placeholder="订单号快速输入" />
        <select v-model="filterForm.factory_id" class="pc-input">
          <option value="">全部厂家</option>
          <option v-for="factory in factoryList" :key="factory.id || factory.factory_id" :value="String(factory.id || factory.factory_id)">
            {{ factory.name || factory.factory_name }}
          </option>
        </select>
        <button type="button" :class="{ active: activeReport === 'flow' }" @click="selectReport('flow')">外协流转明细</button>
        <button type="button" :class="{ active: activeReport === 'exception' }" @click="selectReport('exception')">异常逾期报表</button>
        <button type="button" :class="{ active: quickRange === 'today' }" @click="setDateRange('today')">今天</button>
        <button type="button" :class="{ active: quickRange === 'week' }" @click="setDateRange('week')">本周</button>
        <button type="button" :class="{ active: quickRange === 'month' }" @click="setDateRange('month')">本月</button>
        <button type="button" class="primary" :disabled="!canExport || exporting" @click="handleExport">一键导出</button>
      </div>
    </section>

    <section class="desktop-only pc-data-table export-workbench-table">
      <div class="table-title">导出参数确认</div>
      <table>
        <thead>
          <tr>
            <th>报表类型</th>
            <th>时间范围</th>
            <th>厂家</th>
            <th>订单</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{{ activeReportName }}</td>
            <td>{{ datePreview }}</td>
            <td>{{ selectedFactoryName || filterForm.factory_name || '全部厂家' }}</td>
            <td>{{ orderKeyword || filterForm.order_id || '全部订单' }}</td>
            <td>{{ canExport ? '可导出' : '请选择日期范围' }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="common-reports mobile-only">
      <div class="section-title">常用报表</div>
      <div class="report-grid">
        <button type="button" :class="{ active: activeReport === 'flow' }" @click="selectReport('flow')">
          <strong>外协流转明细</strong>
          <span>订单、厂家、工序、数量</span>
        </button>
        <button type="button" :class="{ active: activeReport === 'exception' }" @click="selectReport('exception')">
          <strong>异常逾期报表</strong>
          <span>逾期、待接收、待发出</span>
        </button>
      </div>
    </section>

    <div class="filter-form mobile-only">
      <van-cell-group inset>
        <van-field
          v-model="filterForm.start_date"
          is-link
          readonly
          name="start_date"
          label="开始日期"
          placeholder="请选择开始日期"
          @click="showStartDatePicker = true"
        />
        <van-field
          v-model="filterForm.end_date"
          is-link
          readonly
          name="end_date"
          label="结束日期"
          placeholder="请选择结束日期"
          @click="showEndDatePicker = true"
        />
        
        <van-field
          v-model="filterForm.order_id"
          name="order_id"
          label="订单号"
          placeholder="请输入订单号（可选）"
          clearable
        />
        
        <van-field
          v-model="filterForm.factory_name"
          is-link
          readonly
          name="factory_id"
          label="厂家"
          placeholder="请选择厂家（可选）"
          @click="showFactoryPicker = true"
        />
      </van-cell-group>
    </div>

    <div class="quick-dates mobile-only">
      <span class="quick-label">快捷选择:</span>
      <van-button size="small" :type="quickRange === 'today' ? 'primary' : 'default'" @click="setDateRange('today')">今天</van-button>
      <van-button size="small" :type="quickRange === 'week' ? 'primary' : 'default'" @click="setDateRange('week')">本周</van-button>
      <van-button size="small" :type="quickRange === 'month' ? 'primary' : 'default'" @click="setDateRange('month')">本月</van-button>
      <van-button size="small" @click="clearDateRange">清除</van-button>
    </div>

    <section class="preview-card mobile-only">
      <div class="section-title">导出预览</div>
      <div class="preview-line">
        <span>报表类型</span>
        <strong>{{ activeReportName }}</strong>
      </div>
      <div class="preview-line">
        <span>时间范围</span>
        <strong>{{ datePreview }}</strong>
      </div>
      <div class="preview-line">
        <span>厂家</span>
        <strong>{{ filterForm.factory_name || '全部厂家' }}</strong>
      </div>
      <div class="preview-line">
        <span>订单</span>
        <strong>{{ filterForm.order_id || '全部订单' }}</strong>
      </div>
    </section>

    <section class="file-contains mobile-only">
      <div class="section-title">导出文件包含</div>
      <div class="contains-tags">
        <van-tag plain type="primary">订单号</van-tag>
        <van-tag plain type="primary">厂家</van-tag>
        <van-tag plain type="primary">工序</van-tag>
        <van-tag plain type="primary">数量</van-tag>
        <van-tag plain type="primary">接收/发出时间</van-tag>
        <van-tag plain type="primary">异常状态</van-tag>
      </div>
    </section>

    <div class="export-btn-wrap mobile-only">
      <van-button
        type="primary"
        block
        round
        :loading="exporting"
        :disabled="!canExport"
        @click="handleExport"
      >
        导出Excel
      </van-button>
    </div>

    <van-popup v-model:show="showStartDatePicker" position="bottom">
      <van-date-picker
        v-model="startDateValue"
        title="选择开始日期"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onStartDateConfirm"
        @cancel="showStartDatePicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showEndDatePicker" position="bottom">
      <van-date-picker
        v-model="endDateValue"
        title="选择结束日期"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onEndDateConfirm"
        @cancel="showEndDatePicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showFactoryPicker" position="bottom">
      <van-picker
        :columns="factoryColumns"
        @confirm="onFactoryConfirm"
        @cancel="showFactoryPicker = false"
      />
    </van-popup>

    <div class="export-tip">
      <van-icon name="info-o" />
      <span>导出文件包含订单号、厂家、工序、数量、时间和异常状态；如数据量大，请优先选择今天、本周或本月。</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '@/stores/auth'
import request from '@/api'
import QuickNavStrip from '@/components/QuickNavStrip.vue'
const router = useRouter()

const filterForm = ref({
  start_date: '',
  end_date: '',
  order_id: '',
  factory_id: undefined as string | undefined,
  factory_name: ''
})

const activeReport = ref<'flow' | 'exception'>('flow')
const quickRange = ref<'today' | 'week' | 'month' | ''>('')
const orderKeyword = ref('')

const showStartDatePicker = ref(false)
const showEndDatePicker = ref(false)
const startDateValue = ref<string[]>([])
const endDateValue = ref<string[]>([])
const minDate = new Date('2020-01-01')
const maxDate = new Date()

const showFactoryPicker = ref(false)
const factoryList = ref<any[]>([])
const factoryColumns = computed(() => {
  return [
    { text: '全部厂家', value: '' },
    ...factoryList.value.map(f => ({ text: f.name || f.factory_name, value: String(f.id || f.factory_id) }))
  ]
})

const exporting = ref(false)

const canExport = computed(() => {
  return Boolean(filterForm.value.start_date && filterForm.value.end_date)
})

const activeReportName = computed(() => activeReport.value === 'flow' ? '外协流转明细' : '异常逾期报表')
const selectedFactoryName = computed(() => {
  const factoryId = filterForm.value.factory_id
  if (!factoryId) return ''
  const found = factoryList.value.find(f => String(f.id || f.factory_id) === factoryId)
  return found ? (found.name || found.factory_name) : ''
})
const datePreview = computed(() => {
  if (!filterForm.value.start_date || !filterForm.value.end_date) return '请选择日期范围'
  return `${filterForm.value.start_date} 至 ${filterForm.value.end_date}`
})

function selectReport(type: 'flow' | 'exception') {
  activeReport.value = type
  if (type === 'exception' && !filterForm.value.start_date) {
    setDateRange('week')
  }
}

function setDateRange(type: 'today' | 'week' | 'month') {
  const now = new Date()
  let start: Date
  const end: Date = now

  switch (type) {
    case 'today':
      start = new Date(now)
      break
    case 'week': {
      const dayOfWeek = now.getDay() || 7
      start = new Date(now)
      start.setDate(now.getDate() - dayOfWeek + 1)
      break
    }
    case 'month':
      start = new Date(now.getFullYear(), now.getMonth(), 1)
      break
  }

  quickRange.value = type
  filterForm.value.start_date = formatDate(start)
  filterForm.value.end_date = formatDate(end)
  startDateValue.value = formatDateForPicker(start)
  endDateValue.value = formatDateForPicker(end)
}

function clearDateRange() {
  quickRange.value = ''
  filterForm.value.start_date = ''
  filterForm.value.end_date = ''
  startDateValue.value = []
  endDateValue.value = []
}

function onStartDateConfirm({ selectedValues }: any) {
  quickRange.value = ''
  filterForm.value.start_date = selectedValues.join('-')
  startDateValue.value = selectedValues
  showStartDatePicker.value = false
}

function onEndDateConfirm({ selectedValues }: any) {
  quickRange.value = ''
  filterForm.value.end_date = selectedValues.join('-')
  endDateValue.value = selectedValues
  showEndDatePicker.value = false
}

function onFactoryConfirm({ selectedOptions }: any) {
  const selected = selectedOptions[0]
  filterForm.value.factory_id = selected.value || undefined
  filterForm.value.factory_name = selected.value ? selected.text : ''
  showFactoryPicker.value = false
}

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDateForPicker(date: Date): string[] {
  return [
    String(date.getFullYear()),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0')
  ]
}

async function fetchFactoryList() {
  try {
    const res: any = await fetchFactories({ page_size: 100 })
    factoryList.value = res?.items || res?.data?.items || res?.data?.data || res?.data || []
  } catch (e) {
    console.error(e)
  }
}

async function handleExport() {
  if (!canExport.value) {
    showToast('请选择开始和结束日期')
    return
  }

  exporting.value = true
  try {
    const params: any = {
      start_date: filterForm.value.start_date,
      end_date: filterForm.value.end_date,
      report_type: activeReport.value
    }
    
    if (orderKeyword.value || filterForm.value.order_id) {
      params.order_id = orderKeyword.value || filterForm.value.order_id
    }
    
    if (filterForm.value.factory_id) {
      params.factory_id = filterForm.value.factory_id
    }

    const blob: any = await exportExcel(params)
    
    const downloadBlob = blob instanceof Blob ? blob : new Blob([blob], { type: 'application/vnd.ms-excel' })
    const url = window.URL.createObjectURL(downloadBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${activeReportName.value}_${filterForm.value.start_date}_${filterForm.value.end_date}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showToast('导出成功')
  } catch (e: any) {
    console.error(e)
    showToast(e?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

fetchFactoryList()
</script>

<style scoped>
.export-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding-bottom: 20px;
}

.export-hero {
  margin: 12px;
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #1989fa, #00a870);
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.eyebrow {
  font-size: 12px;
  opacity: 0.86;
}

.export-hero h2 {
  margin: 4px 0 6px;
  font-size: 20px;
}

.export-hero p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.common-reports,
.preview-card,
.file-contains {
  margin: 0 12px 12px;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #323233;
  margin-bottom: 10px;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.report-grid button {
  border: 1px solid #ebedf0;
  background: #fff;
  border-radius: 10px;
  padding: 10px;
  text-align: left;
}

.report-grid button.active {
  border-color: #1989fa;
  background: #ecf6ff;
}

.report-grid strong,
.report-grid span {
  display: block;
}

.report-grid strong {
  font-size: 14px;
  color: #323233;
  margin-bottom: 4px;
}

.report-grid span {
  font-size: 12px;
  color: #969799;
  line-height: 1.35;
}

.filter-form {
  margin-top: 12px;
}

.quick-dates {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  flex-wrap: wrap;
}

.quick-label {
  font-size: 13px;
  color: #666;
}

.preview-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f2f3f5;
  font-size: 13px;
}

.preview-line:last-child {
  border-bottom: 0;
}

.preview-line span {
  color: #969799;
}

.preview-line strong {
  color: #323233;
  text-align: right;
}

.contains-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.export-btn-wrap {
  padding: 8px 16px 16px;
}

.export-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #999;
  background: #fff;
  margin: 0 16px;
  border-radius: 8px;
}

.export-tip :deep(.van-icon) {
  flex-shrink: 0;
  margin-top: 2px;
}

.desktop-only { display: block; }
.mobile-only { display: none; }
.pc-toolbar,
.pc-data-table { margin: 16px 24px; padding: 18px; border-radius: 16px; background: #fff; box-shadow: 0 8px 24px rgba(31, 45, 61, 0.08); }
.pc-toolbar { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.pc-toolbar h3 { margin: 0 0 6px; font-size: 20px; color: #1f2937; }
.pc-toolbar p { margin: 0; color: #667085; font-size: 13px; }
.pc-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.pc-actions button,
.pc-input { border: 1px solid #d0d5dd; background: #fff; border-radius: 8px; padding: 8px 12px; color: #344054; cursor: pointer; }
.pc-actions button.active,
.pc-actions button.primary { color: #fff; border-color: #1e63ff; background: #1e63ff; }
.pc-actions button:disabled { opacity: 0.55; cursor: not-allowed; }
.table-title { margin-bottom: 12px; font-weight: 800; color: #1f2937; }
.pc-data-table table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pc-data-table th,
.pc-data-table td { padding: 12px; border-bottom: 1px solid #eef2f7; text-align: left; }
.pc-data-table th { color: #667085; background: #f8fafc; font-weight: 700; }
@media (max-width: 900px) {
  .desktop-only { display: none !important; }
  .mobile-only { display: block; }
}
</style>
