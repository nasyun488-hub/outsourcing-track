<template>
  <!-- 页面快捷操作：回到主页 router.push('/') | 设置中心 router.push('/settings') -->
  <div class="admin-factory-page">
    <QuickNavStrip />
    <van-nav-bar
      title="厂家协作控制台"
      left-arrow
      @click-left="router.back()"
    />

    <section class="console-hero">
      <div>
        <div class="eyebrow">厂家协作控制台</div>
        <h2>先审核合作方，再开放流转</h2>
        <p>新增厂家后可分配人员，联系人与手机号用于异常追踪和协作沟通。</p>
      </div>
      <van-button size="small" type="primary" round @click="showAddForm = true">新增厂家</van-button>
    </section>

    <section class="stats-row">
      <div class="stat-card warning">
        <strong>{{ pendingApplications.length }}</strong>
        <span>厂家审核队列</span>
      </div>
      <div class="stat-card">
        <strong>{{ activeFactoryCount }}</strong>
        <span>合作中</span>
      </div>
      <div class="stat-card">
        <strong>{{ factoryList.length }}</strong>
        <span>全部厂家</span>
      </div>
    </section>

    <section class="pending-section mobile-only">
      <div class="section-title">厂家审核队列</div>
      <template v-if="pendingApplications.length > 0">
        <div
          v-for="app in pendingApplications"
          :key="getFactoryId(app)"
          class="application-item"
        >
          <div class="app-info">
            <div class="app-name">{{ app.factory_name || app.name }}</div>
            <div class="app-meta">
              <van-tag type="warning" size="small">待审核</van-tag>
              <span class="app-contact">{{ app.contact || '未填联系人' }}</span>
              <span class="app-phone">{{ app.phone || '未填手机号' }}</span>
            </div>
          </div>
          <div class="app-actions">
            <van-button size="small" type="success" @click="handleReview(getFactoryId(app), true)">通过</van-button>
            <van-button size="small" type="danger" plain @click="handleReview(getFactoryId(app), false)">拒绝</van-button>
          </div>
        </div>
      </template>
      <van-empty v-else image-size="56" description="暂无待审核厂家" />
    </section>

    <section class="cooperation-tip mobile-only">
      <div class="section-title">合作状态</div>
      <div class="tip-text">启用代表可参与订单流转；禁用后仅保留历史追踪。新增厂家后可分配人员，请到人员权限控制台绑定操作员。</div>
      <van-button size="small" type="primary" plain @click="router.push('/admin/users')">去分配人员</van-button>
    </section>

    <section class="desktop-only pc-toolbar factory-toolbar">
      <div>
        <h3>厂家清单表</h3>
        <p>桌面端集中管理厂家合作状态、联系人与审核队列。</p>
      </div>
      <div class="pc-actions">
        <input v-model="keyword" class="pc-input" placeholder="搜索厂家/联系人/手机号" @keyup.enter="onRefresh" />
        <select v-model="filterStatus" class="pc-input" @change="onRefresh">
          <option value="">全部状态</option>
          <option value="pending">待审核</option>
          <option value="active">合作中</option>
          <option value="disabled">已停用</option>
        </select>
        <button type="button" :disabled="selectedFactoryIds.length === 0" @click="batchApproveSelected(true)">批量通过</button>
        <button type="button" :disabled="selectedFactoryIds.length === 0" @click="batchApproveSelected(false)">批量拒绝</button>
        <button type="button" class="primary" @click="showAddForm = true">新增厂家</button>
        <button type="button" @click="router.push('/admin/users')">去分配人员</button>
        <button type="button" @click="onRefresh">刷新</button>
      </div>
    </section>

    <section class="desktop-only pc-data-table">
      <table>
        <thead>
          <tr>
            <th>选择</th>
            <th>厂家名称</th>
            <th>联系人</th>
            <th>手机号</th>
            <th>状态</th>
            <th>审核</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="factory in factoryList" :key="getFactoryId(factory)">
            <td><input type="checkbox" :checked="selectedFactoryIds.includes(getFactoryId(factory))" @change="toggleFactorySelection(getFactoryId(factory))" /></td>
            <td>{{ factory.name || factory.factory_name }}</td>
            <td>{{ factory.contact || '未维护联系人' }}</td>
            <td>{{ factory.phone || '未维护手机号' }}</td>
            <td>{{ factory.status === 'pending' ? '待审核' : getCooperationText(factory) }}</td>
            <td>
              <template v-if="factory.status === 'pending'">
                <button type="button" class="link-btn" @click="handleReview(getFactoryId(factory), true)">通过</button>
                <button type="button" class="link-btn danger" @click="handleReview(getFactoryId(factory), false)">拒绝</button>
              </template>
              <span v-else>-</span>
            </td>
            <td><button type="button" class="link-btn" @click="router.push('/admin/users')">分配人员</button></td>
          </tr>
        </tbody>
      </table>
      <van-empty v-if="factoryList.length === 0 && !loading" description="暂无厂家" />
    </section>

    <div class="factory-list mobile-only">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          :finished-text="hasMore ? '加载更多' : '没有更多了'"
          @load="onLoad"
        >
          <div
            v-for="factory in factoryList"
            :key="getFactoryId(factory)"
            class="factory-item"
          >
            <div class="factory-info">
              <div class="factory-name">{{ factory.name || factory.factory_name }}</div>
              <div class="factory-meta-title">联系人与手机号</div>
              <div class="factory-meta">
                <span class="contact">{{ factory.contact || '未维护联系人' }}</span>
                <span class="phone">{{ factory.phone || '未维护手机号' }}</span>
              </div>
            </div>
            <div class="factory-status">
              <van-tag v-if="factory.status === 'pending'" type="warning" size="small">待审核</van-tag>
              <van-tag v-else-if="isFactoryActive(factory)" type="success" size="small">合作中</van-tag>
              <van-tag v-else type="danger" size="small">已停用</van-tag>
              <span class="status-caption">{{ getCooperationText(factory) }}</span>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>

      <van-empty v-if="factoryList.length === 0 && !loading" description="暂无厂家" />
    </div>

    <div class="add-btn-wrap mobile-only">
      <van-button type="primary" block round @click="showAddForm = true">
        添加厂家
      </van-button>
    </div>

    <van-popup v-model:show="showAddForm" position="bottom" round style="height: 66%">
      <div class="add-form-popup">
        <div class="popup-title">添加厂家</div>
        <div class="form-tip">新增厂家后可分配人员，请确保联系人与手机号准确。</div>
        <van-form @submit="handleAddFactory">
          <van-cell-group inset>
            <van-field
              v-model="addForm.name"
              name="name"
              label="厂家名称"
              placeholder="请输入厂家名称"
              :rules="[{ required: true, message: '请输入厂家名称' }]"
            />
            <van-field
              v-model="addForm.contact"
              name="contact"
              label="联系人"
              placeholder="请输入联系人"
              :rules="[{ required: true, message: '请输入联系人' }]"
            />
            <van-field
              v-model="addForm.phone"
              name="phone"
              label="联系电话"
              placeholder="请输入联系电话"
              type="tel"
              :rules="[
                { required: true, message: '请输入联系电话' },
                { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
              ]"
            />
          </van-cell-group>
          <div class="form-submit">
            <van-button type="primary" block native-type="submit">
              提交并继续分配人员
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { fetchFactories, createFactory, reviewFactoryAdminApplication } from '@/api/kanban'
import { useAuthStore } from '@/stores/auth'
import QuickNavStrip from '@/components/QuickNavStrip.vue'
const router = useRouter()

const factoryList = ref<any[]>([])
const pendingApplications = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 10
const keyword = ref('')
const filterStatus = ref('')
const selectedFactoryIds = ref<string[]>([])

const showAddForm = ref(false)
const addForm = ref({
  name: '',
  contact: '',
  phone: ''
})

const activeFactoryCount = computed(() => factoryList.value.filter(isFactoryActive).length)

async function fetchFactoryList() {
  try {
    const res: any = await fetchFactories({
      page: currentPage.value,
      page_size: pageSize,
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined
    })
    const data = normalizeList(res)
    
    if (currentPage.value === 1) {
      factoryList.value = data
    } else {
      factoryList.value.push(...data)
    }
    pendingApplications.value = factoryList.value.filter(factory => factory.status === 'pending')
    
    hasMore.value = data.length >= pageSize
    finished.value = !hasMore.value
  } catch (e) {
    console.error(e)
    showToast('厂家列表加载失败')
  }
}

function normalizeList(res: any): any[] {
  return res?.items || res?.data?.items || res?.data?.data || res?.data || []
}

async function onLoad() {
  if (!hasMore.value) {
    finished.value = true
    return
  }
  currentPage.value++
  await fetchFactoryList()
  loading.value = false
}

async function onRefresh() {
  currentPage.value = 1
  hasMore.value = true
  finished.value = false
  selectedFactoryIds.value = []
  await fetchFactoryList()
  refreshing.value = false
}

async function handleAddFactory() {
  try {
    await createFactory(addForm.value)
    showToast('添加成功，可继续分配人员')
    showAddForm.value = false
    addForm.value = { name: '', contact: '', phone: '' }
    await onRefresh()
  } catch (e) {
    console.error(e)
  }
}

async function handleReview(factoryId: string, approved: boolean) {
  try {
    await showConfirmDialog({
      title: '确认操作',
      message: `确定要${approved ? '通过' : '拒绝'}该厂家申请吗？`
    })
    await reviewFactoryAdminApplication(factoryId, approved)
    showToast(approved ? '已通过，可分配人员' : '已拒绝')
    pendingApplications.value = pendingApplications.value.filter(a => getFactoryId(a) !== factoryId)
    factoryList.value = factoryList.value.map(factory => getFactoryId(factory) === factoryId ? { ...factory, status: approved ? 'active' : 'disabled' } : factory)
  } catch (e) {
    // 用户取消
  }
}

function toggleFactorySelection(factoryId: string) {
  selectedFactoryIds.value = selectedFactoryIds.value.includes(factoryId)
    ? selectedFactoryIds.value.filter(id => id !== factoryId)
    : [...selectedFactoryIds.value, factoryId]
}

async function batchApproveSelected(approved: boolean) {
  const ids = [...selectedFactoryIds.value]
  if (ids.length === 0) return
  try {
    await showConfirmDialog({ title: '批量审核', message: `确定要批量${approved ? '通过' : '拒绝'} ${ids.length} 家厂家吗？` })
    for (const factoryId of ids) {
      await reviewFactoryAdminApplication(factoryId, approved)
    }
    selectedFactoryIds.value = []
    showToast('批量审核完成')
    await onRefresh()
  } catch (e) {
    // 用户取消或单条失败
  }
}

function getFactoryId(factory: any): string {
  return String(factory.id || factory.factory_id || factory.name || factory.factory_name)
}

function isFactoryActive(factory: any): boolean {
  return factory.status === 'approved' || factory.status === 'active' || factory.status === 1 || factory.status === true
}

function getCooperationText(factory: any): string {
  if (factory.status === 'pending') return '等待审核'
  return isFactoryActive(factory) ? '合作状态正常' : '合作状态停用'
}

onMounted(async () => {
  loading.value = true
  await fetchFactoryList()
  loading.value = false
})
</script>

<style scoped>
.admin-factory-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding-bottom: 88px;
}

.console-hero {
  margin: 12px;
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #00a870, #1989fa);
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.eyebrow {
  font-size: 12px;
  opacity: 0.86;
}

.console-hero h2 {
  margin: 4px 0 6px;
  font-size: 20px;
}

.console-hero p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 0 12px 12px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.stat-card strong {
  display: block;
  font-size: 20px;
  color: #323233;
}

.stat-card span {
  font-size: 12px;
  color: #969799;
}

.stat-card.warning strong {
  color: #ed6a0c;
}

.pending-section,
.cooperation-tip {
  margin: 0 12px 12px;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}

.tip-text {
  color: #646566;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 10px;
}

.factory-list {
  padding: 0 12px;
}

.factory-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}

.factory-info {
  min-width: 0;
}

.factory-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
}

.factory-meta-title {
  font-size: 12px;
  color: #969799;
  margin-bottom: 3px;
}

.factory-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #666;
}

.factory-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.status-caption {
  color: #969799;
  font-size: 12px;
}

.add-btn-wrap {
  position: fixed;
  bottom: 20px;
  left: 16px;
  right: 16px;
  z-index: 100;
}

.add-form-popup {
  padding: 20px 16px;
  height: 100%;
  box-sizing: border-box;
}

.popup-title {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 8px;
}

.form-tip {
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #eef9f5;
  color: #00a870;
  font-size: 12px;
}

.form-submit {
  margin-top: 20px;
  padding: 0 16px;
}

.section-title {
  font-size: 14px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 10px;
}

.application-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  background: #f7f8fa;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.app-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
}

.app-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.app-contact,
.app-phone {
  font-size: 12px;
  color: #666;
}

.app-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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
.pc-input,
.link-btn { border: 1px solid #d0d5dd; background: #fff; border-radius: 8px; padding: 8px 12px; color: #344054; cursor: pointer; }
.pc-actions button.primary { color: #fff; border-color: #1e63ff; background: #1e63ff; }
.pc-data-table table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pc-data-table th,
.pc-data-table td { padding: 12px; border-bottom: 1px solid #eef2f7; text-align: left; }
.pc-data-table th { color: #667085; background: #f8fafc; font-weight: 700; }
.link-btn { padding: 6px 10px; color: #1e63ff; border-color: #bfdbfe; }
.link-btn.danger { color: #d92d20; border-color: #fecaca; }
@media (max-width: 900px) {
  .desktop-only { display: none !important; }
  .mobile-only { display: block; }
}
</style>
