import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { userApi, type User } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // ── State ──
  const users = ref<User[]>([])
  const currentUserId = ref<number | null>(null)
  const loading = ref(false)

  // ── Getters ──
  const currentUser = computed(() => {
    return users.value.find(u => u.id === currentUserId.value) || null
  })

  const isLoggedIn = computed(() => currentUserId.value !== null && currentUser.value !== null)

  // ── Actions ──

  /** 加载用户列表并恢复当前用户 */
  async function loadUsers() {
    loading.value = true
    try {
      users.value = await userApi.list()

      const stored = localStorage.getItem('active_user_id')
      if (stored) {
        const id = parseInt(stored)
        if (users.value.find(u => u.id === id)) {
          currentUserId.value = id
        } else if (users.value.length > 0) {
          const firstUser = users.value[0]!
          currentUserId.value = firstUser.id
          localStorage.setItem('active_user_id', String(firstUser.id))
        }
      } else if (users.value.length > 0) {
        const firstUser = users.value[0]!
        currentUserId.value = firstUser.id
        localStorage.setItem('active_user_id', String(firstUser.id))
      }
    } catch (e) {
      console.error('Failed to load users:', e)
    } finally {
      loading.value = false
    }
  }

  /** 切换用户 */
  function switchUser(userId: number) {
    if (userId === currentUserId.value) return
    currentUserId.value = userId
    localStorage.setItem('active_user_id', String(userId))
    // 触发全局事件，通知各页面刷新
    window.dispatchEvent(new CustomEvent('user:switched', { detail: { userId } }))
  }

  /** 创建新用户 */
  async function createUser(name: string): Promise<User | null> {
    try {
      const user = await userApi.create({ name: name.trim() })
      users.value.push(user)
      // 自动切换到新用户
      switchUser(user.id)
      return user
    } catch (e) {
      console.error('Failed to create user:', e)
      return null
    }
  }

  /** 删除用户 */
  async function deleteUser(userId: number): Promise<boolean> {
    try {
      await userApi.delete(userId)
      users.value = users.value.filter(u => u.id !== userId)

      // 如果删除的是当前用户，切换到第一个可用用户
      if (currentUserId.value === userId) {
        if (users.value.length > 0) {
          switchUser(users.value[0]!.id)
        } else {
          currentUserId.value = null
          localStorage.removeItem('active_user_id')
          window.dispatchEvent(new CustomEvent('user:switched', { detail: { userId: null } }))
        }
      }
      return true
    } catch (e) {
      console.error('Failed to delete user:', e)
      return false
    }
  }

  /** 获取当前用户ID（供API调用使用） */
  function getCurrentUserId(): number | null {
    return currentUserId.value
  }

  return {
    users,
    currentUserId,
    currentUser,
    loading,
    isLoggedIn,
    loadUsers,
    switchUser,
    createUser,
    deleteUser,
    getCurrentUserId,
  }
})
