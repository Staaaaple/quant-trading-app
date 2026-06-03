import client from './client'

export interface User {
  id: number
  name: string
  avatar_url: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  name: string
  avatar_url?: string | null
}

export const userApi = {
  list: () => client.get<User[]>('/users').then(r => r.data),
  get: (id: number) => client.get<User>(`/users/${id}`).then(r => r.data),
  create: (data: UserCreate) => client.post<User>('/users', data).then(r => r.data),
  update: (id: number, data: Partial<UserCreate>) => client.put<User>(`/users/${id}`, data).then(r => r.data),
  delete: (id: number) => client.delete(`/users/${id}`).then(r => r.data),
}
