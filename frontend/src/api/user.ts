import { delay } from './mock/utils'
import { DEMO_USER } from './mock/demoData'

export interface User {
  id: number
  name: string
  avatar_url: string | null
  is_active: boolean
  is_demo: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  name: string
  avatar_url?: string | null
}

export const userApi = {
  list: () => delay(300).then(() => [DEMO_USER as User]),
  get: (id: number) => delay(300).then(() => ({ ...DEMO_USER, id } as User)),
  create: (data: UserCreate) => delay(400).then(() => ({ ...DEMO_USER, ...data, id: 1 } as User)),
  update: (id: number, data: Partial<UserCreate>) => delay(400).then(() => ({ ...DEMO_USER, ...data, id } as User)),
  delete: (_id: number) => delay(300).then(() => ({ success: true })),
  resetDemo: () => delay(500).then(() => ({ ok: true, deleted_counts: {} })),
}
