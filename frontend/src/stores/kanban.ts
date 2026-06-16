import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchKanbanOrders, fetchKanbanOrderDetail, fetchKanbanStats, type OrderKanbanItem, type ProcessKanbanItem } from '../api/kanban'

export interface Order {
  order_id: string
  order_no: string
  product_name: string
  product_code?: string
  part_no?: string
  spec?: string
  unit?: string
  quantity: number
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  factory_id: string
  factory_name: string
  is_overdue: boolean
  process_count: number
  pending_count: number
  in_progress_count: number
  completed_count: number
}

export interface Process {
  record_id: string
  order_id: string
  process_id?: string
  process_name?: string
  process_order?: number
  factory_id?: string
  factory_name?: string
  status: 'pending' | 'received' | 'shipped' | 'completed' | 'transferred'
  is_overdue: boolean
  receive_qty: number
  ship_qty: number
  prev_ship_qty?: number
  current_receive_qty?: number
  current_ship_qty?: number
  available_receive_qty?: number
  available_ship_qty?: number
  prev_process_id?: string
  next_process_id?: string
}

export const useKanbanStore = defineStore('kanban', () => {
  const orderList = ref<Order[]>([])
  const currentOrder = ref<(Order & { processes: Process[] }) | null>(null)
  const loading = ref(false)
  const stats = ref({ total: 0, pending: 0, in_progress: 0, completed: 0, overdue_count: 0 })

  // 获取订单列表
  async function fetchOrders(params?: { status?: string; factory_id?: string; order_no?: string; start_date?: string; end_date?: string }) {
    loading.value = true
    try {
      const res = await fetchKanbanOrders(params)
      orderList.value = res.items || []
    } finally {
      loading.value = false
    }
  }

  // 获取订单详情
  async function fetchDetail(orderId: string) {
    loading.value = true
    try {
      const res: any = await fetchKanbanOrderDetail(orderId)
      const detail = res.data || res
      let baseOrder = orderList.value.find(o => o.order_id === orderId)
      if (!baseOrder) {
        const list = await fetchKanbanOrders({ order_no: orderId, page_size: 100 })
        baseOrder = (list.items || []).find(o => o.order_id === orderId)
      }
      currentOrder.value = {
        ...(baseOrder || {
          order_id: detail.order_id,
          order_no: detail.order_no,
          product_name: detail.product_name || '',
          product_code: detail.product_code,
          part_no: detail.part_no,
          spec: detail.spec,
          unit: detail.unit,
          quantity: detail.quantity || 0,
          status: detail.status || 'pending',
          factory_id: detail.factory_id || '',
          factory_name: detail.factory_name || '',
          is_overdue: false,
          process_count: 0,
          pending_count: 0,
          in_progress_count: 0,
          completed_count: 0
        } as Order),
        order_id: detail.order_id,
        order_no: detail.order_no,
        processes: detail.items || []
      }
      return currentOrder.value
    } finally {
      loading.value = false
    }
  }

  // 获取统计数据
  async function fetchStats(factoryId?: string) {
    const res = await fetchKanbanStats(factoryId)
    stats.value = res
  }

  return {
    orderList,
    currentOrder,
    loading,
    stats,
    fetchOrders,
    fetchDetail,
    fetchStats
  }
})
