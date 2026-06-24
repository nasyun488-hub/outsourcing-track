import request from './index'

// ============ Kanban APIs ============

export interface OrderKanbanItem {
  order_id: string
  order_no: string
  product_name: string
  product_code?: string
  part_no?: string
  spec?: string
  quantity: number
  unit?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  factory_id: string
  factory_name?: string
  is_overdue: boolean
  process_count: number
  pending_count: number
  in_progress_count: number
  completed_count: number
}

export interface OrderKanbanListResponse {
  total: number
  page: number
  page_size: number
  items: OrderKanbanItem[]
}

export interface ProcessKanbanItem {
  record_id: string
  order_id: string
  process_id?: string
  process_name?: string
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
  can_receive?: boolean
  can_ship?: boolean
  can_operate?: boolean
  disabled_reason?: string | null
  next_action?: 'receive' | 'ship' | null
  is_bottleneck?: boolean
  risk_level?: 'normal' | 'medium' | 'high'
  risk_reason?: string | null
}

export interface ProcessKanbanListResponse {
  order_id: string
  order_no: string
  items: ProcessKanbanItem[]
  current_bottleneck_record_id?: string | null
  risk_level?: 'normal' | 'medium' | 'high'
  risk_reason?: string | null
}

export interface KanbanStatsResponse {
  total: number
  pending: number
  in_progress: number
  completed: number
  overdue_count: number
}

export function fetchKanbanOrders(params?: {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  order_no?: string
  factory_id?: string
  status?: string
  quick?: string
}) {
  return request.get<OrderKanbanListResponse>('/kanban/orders', { params })
}

export function fetchKanbanOrderDetail(orderId: string) {
  return request.get<ProcessKanbanListResponse>(`/kanban/orders/${orderId}/processes`)
}

export function fetchKanbanStats(factoryId?: string) {
  return request.get<KanbanStatsResponse>('/kanban/stats', { params: { factory_id: factoryId } })
}

// ============ Notification APIs ============

export interface NotificationResponse {
  notif_id: string
  user_id: string
  notif_type: string
  title: string
  content?: string
  is_read: number | string | boolean
  related_id?: string
  related_type?: string
  jump_url?: string
  created_at: string
}

export interface NotificationListResponse {
  total: number
  unread_count: number
  items: NotificationResponse[]
}

export function fetchNotifications(params?: {
  page?: number
  page_size?: number
  is_read?: number
  notif_type?: string
}) {
  return request.get<NotificationListResponse>('/notifications', { params })
}

export function markNotificationRead(notificationId: string) {
  return request.put<{ success: boolean; message: string }>(`/notifications/${notificationId}/read`)
}

export function markAllNotificationsRead() {
  return request.put<{ success: boolean; message: string }>('/notifications/read-all')
}

// ============ Export APIs ============

export function exportExcel(params?: {
  start_date?: string
  end_date?: string
  factory_id?: string
  order_id?: string
  report_type?: string
  status?: string
}) {
  return request.get('/export/excel', {
    params,
    responseType: 'blob'
  })
}

// ============ Admin APIs ============

export interface UserItem {
  id: string
  user_id?: string
  username: string
  name?: string
  phone?: string
  role: string
  factory_id?: string
  factory_name?: string
  status: string
}

export interface FactoryItem {
  id: string
  factory_id?: string
  name: string
  factory_name?: string
  contact: string
  phone: string
  status: string
}

export interface UserListResponse {
  total: number
  items: UserItem[]
}

export interface FactoryListResponse {
  total: number
  items: FactoryItem[]
}

export function fetchUsers(params?: {
  page?: number
  page_size?: number
  role?: string
  keyword?: string
  status?: string
}) {
  return request.get<UserListResponse>('/admin/users', { params })
}

export function createUser(data: {
  username: string
  password: string
  role: string
  factory_id?: string
}) {
  return request.post<{ success: boolean; user_id: string }>('/admin/users', data)
}

export function reviewOperatorApplication(userId: string, approved: boolean) {
  return request.put<{ success: boolean }>(`/admin/users/${userId}/review`, { approved })
}

export function fetchFactories(params?: {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
}) {
  return request.get<FactoryListResponse>('/admin/factories', { params })
}

export function createFactory(data: {
  name: string
  contact: string
  phone: string
}) {
  return request.post<{ success: boolean; factory_id: string }>('/admin/factories', data)
}

export function reviewFactoryAdminApplication(factoryId: string, approved: boolean) {
  return request.put<{ success: boolean }>(`/admin/factories/${factoryId}/review`, { approved })
}

export default request
