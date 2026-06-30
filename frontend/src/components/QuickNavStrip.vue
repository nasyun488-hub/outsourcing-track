<template>
  <section class="quick-nav-strip" aria-label="页面快捷操作">
    <div class="quick-nav-title">页面快捷操作</div>
    <div class="quick-nav-actions">
      <button type="button" @click="goHome">回到主页</button>
      <button type="button" @click="goKanban">企业看板</button>
      <button type="button" @click="goScan">扫码录入</button>
      <button type="button" class="primary" @click="goSettings">设置中心</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goKanban() {
  router.push('/kanban')
}

function goScan() {
  router.push('/scan')
}

function goSettings() {
  router.push('/settings')
}
</script>

<style scoped>
.quick-nav-strip {
  margin: 12px;
  padding: 12px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(16, 35, 70, 0.08);
}

.quick-nav-title {
  margin-bottom: 8px;
  color: #6b778c;
  font-size: 12px;
  font-weight: 800;
}

.quick-nav-actions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.quick-nav-actions button {
  min-height: 34px;
  border: 1px solid #dbe4f3;
  border-radius: 999px;
  color: #344563;
  background: #f8fbff;
  font-size: 13px;
  cursor: pointer;
}

.quick-nav-actions button.primary {
  border-color: #2f6bff;
  color: #fff;
  background: #2f6bff;
}

@media (min-width: 901px) {
  .quick-nav-strip {
    display: none;
  }
}

@media (max-width: 430px) {
  .quick-nav-actions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
