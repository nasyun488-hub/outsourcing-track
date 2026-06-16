import request from './index'

export interface ScanJudgeResult {
  qr_code: string
  record_id?: string
  jump_type: 'receive' | 'ship' | 'view' | 'not_found'
  message: string
  record_status?: 'pending' | 'received' | 'shipped' | 'completed'
  lock_type?: 'none' | 'entry_lock' | 'relation_lock' | 'sync_lock'
  factory_id?: string
}

export interface ReceiveParams {
  record_id: string
  receive_qty: number
  receive_time?: string
}

export interface ShipParams {
  record_id: string
  ship_qty: number
  ship_time?: string
}

export interface ReturnParams {
  from_record_id: string
  to_record_id: string
  return_qty: number
  return_reason: string
}

export interface RecordInfo {
  record_id: string
  order_id: string
  process_id: string
  process_seq?: string
  process_name?: string
  factory_id?: string
  factory_name?: string
  status: 'pending' | 'received' | 'shipped' | 'completed'
  record_status?: 'pending' | 'received' | 'shipped' | 'completed'
  lock_type: 'none' | 'entry_lock' | 'relation_lock' | 'sync_lock'
  entry_lock: boolean
  relation_lock: boolean
  sync_lock: boolean
  previous_record_id?: string
  next_record_id?: string
  is_overdue?: boolean
  total_receive_qty: number
  total_ship_qty: number
  gross_receive_qty?: number
  gross_ship_qty?: number
  returned_in_qty?: number
  returned_out_qty?: number
  prev_ship_qty?: number
  current_receive_qty?: number
  current_ship_qty?: number
  available_receive_qty?: number
  available_ship_qty?: number
  receive_batches: ReceiveRecord[]
  ship_batches: ShipRecord[]
  returns: ReturnRecord[]
}

export interface ReceiveRecord {
  batch_no: number
  receive_time: string
  receive_qty: number
  receiver_name?: string
  user_id?: string
}

export interface ShipRecord {
  batch_no: number
  ship_time: string
  ship_qty: number
  shipper_name?: string
  user_id?: string
  is_return?: boolean
  return_reason?: string
  return_qty?: number
}

export interface ReturnRecord {
  return_id: string
  from_record_id: string
  to_record_id: string
  user_id?: string
  return_reason?: string
  return_qty: number
  created_at: string
}

function normalizeRecord(raw: any): RecordInfo {
  const status = raw.status || raw.record_status || 'pending'
  const lockType = raw.lock_type || 'none'
  return {
    ...raw,
    status,
    record_status: status,
    process_id: String(raw.process_id || ''),
    entry_lock: lockType === 'entry_lock',
    relation_lock: lockType === 'relation_lock',
    sync_lock: lockType === 'sync_lock',
    receive_batches: raw.receive_batches || [],
    ship_batches: raw.ship_batches || [],
    returns: raw.returns || []
  }
}

export interface BatchScanResult {
  total: number
  success_count: number
  fail_count: number
  items: ScanJudgeResult[]
}

export const scanJudge = (qr_code: string): Promise<ScanJudgeResult> => {
  return request.get<ScanJudgeResult>('/records/scan/judge', { params: { qr_code } }) as unknown as Promise<ScanJudgeResult>
}

export const scanBatch = (qr_codes: string[]): Promise<BatchScanResult> => {
  return request.post<BatchScanResult>('/records/scan/batch', { qr_codes }) as unknown as Promise<BatchScanResult>
}

export const receive = (data: ReceiveParams) => {
  return request.post<{
    success: boolean
    message: string
    batch: { batch_id: string; record_id: string; receive_qty: number; batch_no: number }
    record: RecordInfo
  }>('/records/receive', data)
}

export const ship = (data: ShipParams) => {
  return request.post<{
    success: boolean
    message: string
    batch: { batch_id: string; record_id: string; ship_qty: number; batch_no: number }
    record: RecordInfo
  }>('/records/ship', data)
}

export const getOrderRecords = (order_id: string) => {
  return request.get<{
    order_id: string
    records: RecordInfo[]
  }>(`/records/${order_id}`).then((res: any) => ({
    ...res,
    records: (res.records || []).map(normalizeRecord)
  }))
}

export const getRecordDetail = (record_id: string) => {
  return request.get<any>(`/records/detail/${record_id}`).then(normalizeRecord)
}

export const returnGoods = (data: ReturnParams) => {
  return request.post<{
    success: boolean
    message: string
    return_record: any
    from_record: RecordInfo
    to_record: RecordInfo
  }>('/records/return', data)
}
