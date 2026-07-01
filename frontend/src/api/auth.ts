import request from './index'

export interface LoginParams {
  phone: string
  code: string
}

export interface PasswordLoginParams {
  account: string
  password: string
}

export interface SendSmsParams {
  phone: string
}

export interface UserInfo {
  user_id: string
  phone: string
  name: string
  role: string
  factory_id: string
  factory_name?: string
  status?: string
  last_login?: string
  created_at?: string
  updated_at?: string
}

export const sendSms = (phone: string) => {
  return request.post<{ message: string; code: string }>('/auth/send-sms', { phone })
}

export const login = (data: LoginParams) => {
  return request.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/login', data)
}

export const passwordLogin = (data: PasswordLoginParams) => {
  return request.post<{ access_token: string; token_type: string; expires_in: number }>('/auth/password-login', data)
}

export const fetchMe = () => {
  return request.get<Record<string, any>>('/auth/me')
}

export const changePassword = (data: { old_password: string; new_password: string }) => {
  return request.put<{ success: boolean; message: string }>('/auth/password', data)
}
