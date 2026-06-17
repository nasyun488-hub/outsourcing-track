import { test, expect } from '@playwright/test'

test.describe('外协流转主路径', () => {
  test('扫码、看板、审计入口可访问', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('token', 'e2e-token')
      window.localStorage.setItem('userInfo', JSON.stringify({
        user_id: 'U-E2E',
        name: 'E2E管理员',
        role: 'enterprise_admin',
        factory_id: 'F001'
      }))
    })

    await page.goto('/')
    await expect(page.getByText('开始扫码录入').first()).toBeVisible()

    await page.goto('/scan')
    await expect(page.getByText(/扫码|扫描/).first()).toBeVisible()

    await page.goto('/kanban')
    await expect(page.getByText(/看板|流转|订单/).first()).toBeVisible()

    await page.route('**/api/audit/summary', route => route.fulfill({ json: { total_logs: 0, action_type_counts: {}, user_counts: [] } }))
    await page.route('**/api/audit/logs**', route => route.fulfill({ json: { total: 0, page: 1, page_size: 20, items: [] } }))
    await page.goto('/audit')
    await expect(page.getByText('操作审计报表')).toBeVisible()
    await expect(page.getByText('审计总览')).toBeVisible()
  })
})
