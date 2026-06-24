<template>
  <div class="admin-user-page">
    <van-nav-bar
      title="人员权限控制台"
      left-arrow
      @click-left="router.back()"
    />

    <section class="console-hero">
      <div>
        <div class="eyebrow">人员权限控制台</div>
        <h2>先审人，再分配角色</h2>
        <p>操作员必须绑定厂家，角色变更和启用/禁用都在移动端完成确认。</p>
      </div>
      <van-button size="small" type="primary" round @click="showAddForm = true">新增人员</van-button>
    </section>

    <section class="stats-row">
      <div class="stat-card warning">
        <strong>{{ pendingApplications.length }}</strong>
        <span>待审核队列</span>
      </div>
      <div class="stat-card">
        <strong>{{ activeCount }}</strong>
        <span>已启用</span>
      </div>
      <div class="stat-card">
        <strong>{{ disabledCount }}</strong>
        <span>已禁用</span>
      </div>
    </section>

    <section class="role-guide mobile-only">
      <div class="section-title">角色权限说明</div>
      <div class="guide-grid">
        <div>企业管理员：维护厂家、审核人员、导出报表</div>
        <div>厂家管理员：查看本厂订单和操作员</div>
        <div>操作员必须绑定厂家：仅处理所属厂家接收/发出</div>
      </div>
    </section>

    <section class="pending-section compact mobile-only">
      <div class="section-title">待审核队列</div>
      <template v-if="pendingApplications.length > 0">
        <div
          v-for="app in pendingApplications"
          :key="getUserId(app)"
          class="application-item"
        >
          <div class="app-info">
            <div class="app-name">{{ app.username || app.name }}</div>
            <div class="app-meta">
              <van-tag type="warning" size="small">待审核</van-tag>
              <span class="app-role">{{ getRoleText(app.role) }}</span>
              <span v-if="app.factory_name" class="app-role">{{ app.factory_name }}</span>
            </div>
          </div>
          <div class="app-actions">
            <van-button size="small" type="success" @click="handleReview(getUserId(app), true)">通过</van-button>
            <van-button size="small" type="danger" plain @click="handleReview(getUserId(app), false)">拒绝</van-button>
          </div>
        </div>
      </template>
      <van-empty v-else image-size="56" description="暂无待审核人员" />
    </section>

    <section class="desktop-only pc-toolbar user-toolbar">
      <div>
        <h3>人员清单表</h3>
        <p>桌面端集中查看人员、角色、厂家绑定与审核状态。</p>
      </div>
      <div class="pc-actions">
        <input v-model="keyword" class="pc-input" placeholder="搜索姓名/手机号/用户ID" @keyup.enter="onRoleChange" />
        <select v-model="filterStatus" class="pc-input" @change="onRoleChange">
          <option value="">全部状态</option>
          <option value="pending">待审核</option>
          <option value="active">已启用</option>
          <option value="disabled">已禁用</option>
        </select>
        <button type="button" :class="{ active: filterRole === '' }" @click="filterRole = ''; onRoleChange()">全部</button>
        <button type="button" :class="{ active: filterRole === 'enterprise_admin' }" @click="filterRole = 'enterprise_admin'; onRoleChange()">企业管理员</button>
        <button type="button" :class="{ active: filterRole === 'factory_admin' }" @click="filterRole = 'factory_admin'; onRoleChange()">厂家管理员</button>
        <button type="button" :class="{ active: filterRole === 'operator' }" @click="filterRole = 'operator'; onRoleChange()">操作员</button>
        <button type="button" :disabled="selectedUserIds.length === 0" @click="batchApproveSelected(true)">批量通过</button>
        <button type="button" :disabled="selectedUserIds.length === 0" @click="batchApproveSelected(false)">批量拒绝</button>
        <button type="button" class="primary" @click="showAddForm = true">新增人员</button>
      </div>
    </section>

    <section class="desktop-only pc-data-table">
      <table>
        <thead>
          <tr>
            <th>选择</th>
            <th>用户名</th>
            <th>角色</th>
            <th>厂家</th>
            <th>状态</th>
            <th>审核</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in userList" :key="getUserId(user)">
            <td><input type="checkbox" :checked="selectedUserIds.includes(getUserId(user))" @change="toggleUserSelection(getUserId(user))" /></td>
            <td>{{ user.username || user.name }}</td>
            <td>{{ getRoleText(user.role) }}</td>
            <td>{{ user.factory_name || (user.role === 'operator' ? '未绑定厂家' : '-') }}</td>
            <td>{{ user.status === 'pending' ? '待审核' : (isUserActive(user) ? '已启用' : '已禁用') }}</td>
            <td>
              <template v-if="user.status === 'pending'">
                <button type="button" class="link-btn" @click="handleReview(getUserId(user), true)">通过</button>
                <button type="button" class="link-btn danger" @click="handleReview(getUserId(user), false)">拒绝</button>
              </template>
              <span v-else>-</span>
            </td>
            <td><button type="button" class="link-btn" @click="handleToggleStatus(user)">启用/禁用</button></td>
          </tr>
        </tbody>
      </table>
      <van-empty v-if="userList.length === 0 && !loading" description="暂无用户" />
    </section>

    <div class="filter-section mobile-only">
      <van-tabs v-model:active="filterRole" @change="onRoleChange">
        <van-tab title="全部" name="" />
        <van-tab title="企业管理员" name="enterprise_admin" />
        <van-tab title="厂家管理员" name="factory_admin" />
        <van-tab title="操作员" name="operator" />
      </van-tabs>
    </div>

    <div class="user-list mobile-only">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          :finished-text="hasMore ? '加载更多' : '没有更多了'"
          @load="onLoad"
        >
          <div
            v-for="user in userList"
            :key="getUserId(user)"
            class="user-item"
          >
            <div class="user-info">
              <div class="user-avatar">
                <van-icon name="user-o" size="24px" />
              </div>
              <div class="user-detail">
                <div class="user-name">{{ user.username || user.name }}</div>
                <div class="user-meta">
                  <van-tag :type="getRoleTagType(user.role)" size="small">
                    {{ getRoleText(user.role) }}
                  </van-tag>
                  <span v-if="user.factory_name" class="factory-name">{{ user.factory_name }}</span>
                  <span v-else-if="user.role === 'operator'" class="factory-name danger-text">未绑定厂家</span>
                </div>
              </div>
            </div>
            <div class="user-status">
              <van-tag v-if="user.status === 'pending'" type="warning" size="small">待审核</van-tag>
              <van-tag v-else-if="isUserActive(user)" type="success" size="small">已启用</van-tag>
              <van-tag v-else type="danger" size="small">已禁用</van-tag>
              <van-button size="mini" plain @click="handleToggleStatus(user)">
                启用/禁用
              </van-button>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>

      <van-empty v-if="userList.length === 0 && !loading" description="暂无用户" />
    </div>

    <div class="add-btn-wrap mobile-only">
      <van-button type="primary" block round @click="showAddForm = true">
        添加用户
      </van-button>
    </div>

    <van-popup v-model:show="showAddForm" position="bottom" round style="height: 72%">
      <div class="add-form-popup">
        <div class="popup-title">添加用户</div>
        <div class="form-tip">选择操作员时，操作员必须绑定厂家后才可提交。</div>
        <van-form @submit="handleAddUser">
          <van-cell-group inset>
            <van-field
              v-model="addForm.username"
              name="username"
              label="用户名"
              placeholder="请输入用户名"
              :rules="[{ required: true, message: '请输入用户名' }]"
            />
            <van-field
              v-model="addForm.password"
              type="password"
              name="password"
              label="密码"
              placeholder="请输入密码"
              :rules="[{ required: true, message: '请输入密码' }]"
            />
            <van-field
              :model-value="roleText"
              name="role"
              label="角色"
              readonly
              is-link
              placeholder="请选择角色"
              @click="showRolePicker = true"
              :rules="[{ required: true, message: '请选择角色' }]"
            />
            <van-field
              v-if="addForm.role === 'factory_admin' || addForm.role === 'operator'"
              :model-value="factoryText"
              name="factory_id"
              label="厂家"
              readonly
              is-link
              placeholder="请选择厂家"
              @click="showFactoryPicker = true"
              :rules="addForm.role === 'operator' ? [{ required: true, message: '操作员必须绑定厂家' }] : []"
            />
          </van-cell-group>
          <div class="form-submit">
            <van-button type="primary" block native-type="submit">
              提交并进入权限控制台
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <van-popup v-model:show="showRolePicker" position="bottom">
      <van-picker
        :columns="roleColumns"
        @confirm="onRoleConfirm"
        @cancel="showRolePicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showFactoryPicker" position="bottom">
      <van-picker
        :columns="factoryColumns"
        @confirm="onFactoryConfirm"
        @cancel="showFactoryPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { fetchUsers, createUser, reviewOperatorApplication, fetchFactories } from '../api/kanban'

const router = useRouter()

const userList = ref<any[]>([])
const pendingApplications = ref<any[]>([])
const factoryList = ref<any[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 10

const filterRole = ref('')
const filterStatus = ref('')
const keyword = ref('')
const selectedUserIds = ref<string[]>([])

const showAddForm = ref(false)
const showRolePicker = ref(false)
const showFactoryPicker = ref(false)
const addForm = ref({
  username: '',
  password: '',
  role: '',
  factory_id: undefined as string | undefined
})

const roleColumns = [
  { text: '企业管理员', value: 'enterprise_admin' },
  { text: '厂家管理员', value: 'factory_admin' },
  { text: '操作员', value: 'operator' }
]

const factoryColumns = computed(() => factoryList.value.map(factory => ({
  text: factory.name || factory.factory_name,
  value: String(factory.id || factory.factory_id)
})))

const roleText = computed(() => getRoleText(addForm.value.role))
const factoryText = computed(() => {
  const found = factoryList.value.find(factory => String(factory.id || factory.factory_id) === addForm.value.factory_id)
  return found ? (found.name || found.factory_name) : ''
})
const activeCount = computed(() => userList.value.filter(isUserActive).length)
const disabledCount = computed(() => userList.value.filter(user => user.status && !isUserActive(user) && user.status !== 'pending').length)

async function fetchUserList() {
  try {
    const res: any = await fetchUsers({
      page: currentPage.value,
      page_size: pageSize,
      role: normalizeRoleFilter(filterRole.value) || undefined,
      status: filterStatus.value || undefined,
      keyword: keyword.value || undefined
    })
    const data = normalizeList(res)
    
    if (currentPage.value === 1) {
      userList.value = data
    } else {
      userList.value.push(...data)
    }
    pendingApplications.value = userList.value.filter(user => user.status === 'pending')
    
    hasMore.value = data.length >= pageSize
    finished.value = !hasMore.value
  } catch (e) {
    console.error(e)
    showToast('用户列表加载失败')
  }
}

async function fetchFactoryList() {
  try {
    const res: any = await fetchFactories({ page_size: 100 })
    factoryList.value = normalizeList(res)
  } catch (e) {
    console.error(e)
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
  await fetchUserList()
  loading.value = false
}

async function onRefresh() {
  currentPage.value = 1
  hasMore.value = true
  finished.value = false
  await fetchUserList()
  refreshing.value = false
}

async function onRoleChange() {
  currentPage.value = 1
  hasMore.value = true
  finished.value = false
  selectedUserIds.value = []
  await fetchUserList()
}

function normalizeRoleFilter(role: string): string {
  const roleMap: Record<string, string> = {
    factory_admin: 'cooperative_admin',
    operator: 'cooperative_operator'
  }
  return roleMap[role] || role
}

function toggleUserSelection(userId: string) {
  selectedUserIds.value = selectedUserIds.value.includes(userId)
    ? selectedUserIds.value.filter(id => id !== userId)
    : [...selectedUserIds.value, userId]
}

async function batchApproveSelected(approved: boolean) {
  const ids = [...selectedUserIds.value]
  if (ids.length === 0) return
  try {
    await showConfirmDialog({ title: '批量审核', message: `确定要批量${approved ? '通过' : '拒绝'} ${ids.length} 人吗？` })
    for (const userId of ids) {
      await reviewOperatorApplication(userId, approved)
    }
    selectedUserIds.value = []
    showToast('批量审核完成')
    await onRefresh()
  } catch (e) {
    // 用户取消或单条失败
  }
}

async function handleAddUser() {
  if (addForm.value.role === 'operator' && !addForm.value.factory_id) {
    showToast('操作员必须绑定厂家')
    return
  }
  try {
    await createUser(addForm.value)
    showToast('添加成功')
    showAddForm.value = false
    addForm.value = { username: '', password: '', role: '', factory_id: undefined }
    await onRefresh()
  } catch (e) {
    console.error(e)
  }
}

function onRoleConfirm({ selectedOptions }: any) {
  addForm.value.role = selectedOptions[0].value
  if (addForm.value.role === 'enterprise_admin') {
    addForm.value.factory_id = undefined
  }
  showRolePicker.value = false
}

function onFactoryConfirm({ selectedOptions }: any) {
  addForm.value.factory_id = String(selectedOptions[0].value)
  showFactoryPicker.value = false
}

async function handleReview(userId: string, approved: boolean) {
  try {
    await showConfirmDialog({
      title: '确认操作',
      message: `确定要${approved ? '通过' : '拒绝'}该申请吗？`
    })
    await reviewOperatorApplication(userId, approved)
    showToast(approved ? '已通过' : '已拒绝')
    pendingApplications.value = pendingApplications.value.filter(a => getUserId(a) !== userId)
    userList.value = userList.value.map(user => getUserId(user) === userId ? { ...user, status: approved ? 'active' : 'disabled' } : user)
  } catch (e) {
    // 用户取消
  }
}

async function handleToggleStatus(user: any) {
  try {
    const nextActive = !isUserActive(user)
    await showConfirmDialog({
      title: '启用/禁用',
      message: `确定要${nextActive ? '启用' : '禁用'} ${user.username || user.name} 吗？`
    })
    user.status = nextActive ? 'active' : 'disabled'
    showToast(`已${nextActive ? '启用' : '禁用'}，请按后端权限接口同步`)
  } catch (e) {
    // 用户取消
  }
}

function isUserActive(user: any): boolean {
  return user.status === 'approved' || user.status === 'active' || user.status === 1 || user.status === true
}

function getUserId(user: any): string {
  return String(user.id || user.user_id || user.username)
}

function getRoleTagType(role: string) {
  const types: Record<string, 'danger' | 'warning' | 'primary' | 'success' | 'default'> = {
    enterprise_admin: 'danger',
    factory_admin: 'warning',
    operator: 'primary',
    primary_admin: 'danger',
    cooperative_admin: 'warning',
    primary_operator: 'primary',
    cooperative_operator: 'primary'
  }
  return types[role] || 'default'
}

function getRoleText(role: string) {
  const texts: Record<string, string> = {
    enterprise_admin: '企业管理员',
    factory_admin: '厂家管理员',
    operator: '操作员',
    primary_operator: '主厂操作员',
    cooperative_operator: '协作厂操作员',
    primary_admin: '主厂管理员',
    cooperative_admin: '协作厂管理员'
  }
  return texts[role] || role
}

onMounted(async () => {
  loading.value = true
  await Promise.all([fetchUserList(), fetchFactoryList()])
  loading.value = false
})
</script>

<style scoped>
.admin-user-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding-bottom: 88px;
}

.console-hero {
  margin: 12px;
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #1f6fff, #7b61ff);
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.eyebrow {
  font-size: 12px;
  opacity: 0.85;
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

.role-guide,
.pending-section {
  margin: 0 12px 12px;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}

.guide-grid {
  display: grid;
  gap: 8px;
  font-size: 13px;
  color: #646566;
  line-height: 1.45;
}

.filter-section {
  background: #fff;
  margin-bottom: 10px;
}

.user-list {
  padding: 0 12px;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  min-width: 0;
}

.user-avatar {
  width: 44px;
  height: 44px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  flex-shrink: 0;
}

.user-detail {
  margin-left: 12px;
  min-width: 0;
}

.user-name {
  font-weight: bold;
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
}

.user-meta,
.app-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.factory-name,
.app-role {
  font-size: 12px;
  color: #666;
}

.danger-text {
  color: #ee0a24;
}

.user-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
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
  background: #fff7e8;
  color: #ed6a0c;
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
.pc-actions button.active,
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
