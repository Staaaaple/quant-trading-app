<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { userApi, type User } from '@/api/user'

const router = useRouter()

const users = ref<User[]>([])
const currentUserId = ref<number | null>(null)
const isOpen = ref(false)
const showCreateModal = ref(false)
const showDeleteConfirm = ref(false)
const userToDelete = ref<User | null>(null)
const newUserName = ref('')

const currentUser = computed(() => {
  return users.value.find(u => u.id === currentUserId.value) || null
})

async function loadUsers() {
  try {
    users.value = await userApi.list()
    const stored = localStorage.getItem('active_user_id')
    if (stored) {
      const id = parseInt(stored)
      if (users.value.find(u => u.id === id)) {
        currentUserId.value = id
      } else if (users.value.length > 0) {
        currentUserId.value = users.value[0].id
      }
    } else if (users.value.length > 0) {
      currentUserId.value = users.value[0].id
    }
  } catch (e) {
    console.error('Failed to load users:', e)
  }
}

function switchUser(userId: number) {
  currentUserId.value = userId
  localStorage.setItem('active_user_id', String(userId))
  isOpen.value = false
  window.location.reload()
}

async function createUser() {
  if (!newUserName.value.trim()) return
  try {
    const user = await userApi.create({ name: newUserName.value.trim() })
    users.value.push(user)
    switchUser(user.id)
    newUserName.value = ''
    showCreateModal.value = false
    // 新用户跳转到开始界面
    router.push('/profile')
  } catch (e) {
    console.error('Failed to create user:', e)
    alert('创建用户失败')
  }
}

function confirmDelete(user: User) {
  userToDelete.value = user
  showDeleteConfirm.value = true
  isOpen.value = false
}

async function deleteUser() {
  if (!userToDelete.value) return
  try {
    await userApi.delete(userToDelete.value.id)
    users.value = users.value.filter(u => u.id !== userToDelete.value!.id)
    // 如果删除的是当前用户，切换到第一个可用用户
    if (currentUserId.value === userToDelete.value.id) {
      if (users.value.length > 0) {
        switchUser(users.value[0].id)
      } else {
        currentUserId.value = null
        localStorage.removeItem('active_user_id')
      }
    }
    showDeleteConfirm.value = false
    userToDelete.value = null
  } catch (e) {
    console.error('Failed to delete user:', e)
    alert('删除用户失败')
  }
}

function getInitials(name: string) {
  return name.charAt(0).toUpperCase()
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="user-switcher">
    <!-- 当前用户头像 -->
    <button class="avatar-btn" @click="isOpen = !isOpen">
      <div v-if="currentUser" class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <div v-else class="avatar avatar--empty">?</div>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: isOpen ? 'rotate(180deg)' : '' }">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <!-- 下拉菜单 -->
    <div v-if="isOpen" class="dropdown">
      <div class="dropdown-header">
        <span class="dropdown-title">切换用户</span>
      </div>

      <div class="user-list">
        <div
          v-for="user in users"
          :key="user.id"
          class="user-item"
          :class="{ active: user.id === currentUserId }"
          @click="switchUser(user.id)"
        >
          <div class="user-avatar">{{ getInitials(user.name) }}</div>
          <div class="user-info">
            <div class="user-name">{{ user.name }}</div>
            <div v-if="user.id === currentUserId" class="user-badge">当前</div>
          </div>
          <button
            v-if="users.length > 1"
            class="delete-btn"
            @click.stop="confirmDelete(user)"
            title="删除用户"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="dropdown-footer">
        <button class="create-btn" @click="showCreateModal = true; isOpen = false">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          新建用户
        </button>
      </div>
    </div>

    <!-- 点击外部关闭 -->
    <div v-if="isOpen" class="overlay" @click="isOpen = false"></div>

    <!-- 创建用户弹窗 -->
    <div v-if="showCreateModal" class="modal">
      <div class="modal-content">
        <h3>新建用户</h3>
        <input
          v-model="newUserName"
          type="text"
          placeholder="输入用户名"
          @keyup.enter="createUser"
          ref="nameInput"
        />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="createUser" :disabled="!newUserName.trim()">创建</button>
        </div>
      </div>
      <div class="modal-overlay" @click="showCreateModal = false"></div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteConfirm" class="modal">
      <div class="modal-content">
        <h3>确认删除</h3>
        <p>确定要删除用户 <strong>{{ userToDelete?.name }}</strong> 吗？</p>
        <p class="warning">该用户的所有数据（画像、组合、记录）将被删除，此操作不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn-danger" @click="deleteUser">删除</button>
        </div>
      </div>
      <div class="modal-overlay" @click="showDeleteConfirm = false"></div>
    </div>
  </div>
</template>

<style scoped>
.user-switcher {
  position: relative;
}

.avatar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.2s;
}
.avatar-btn:hover {
  background: rgba(0,0,0,0.05);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #171717;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
}
.avatar--empty {
  background: #e5e5e5;
  color: #a3a3a3;
}

.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 240px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
  z-index: 200;
  overflow: hidden;
}

.dropdown-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.dropdown-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #a3a3a3;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-list {
  max-height: 240px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
}
.user-item:hover {
  background: #fafafa;
}
.user-item.active {
  background: #f5f5f5;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #171717;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #171717;
}
.user-badge {
  font-size: 0.65rem;
  font-weight: 700;
  color: #16a34a;
  background: #dcfce7;
  padding: 2px 6px;
  border-radius: 4px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #a3a3a3;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}
.user-item:hover .delete-btn {
  opacity: 1;
}
.delete-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.dropdown-footer {
  padding: 10px;
  border-top: 1px solid rgba(0,0,0,0.05);
}
.create-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border: 1px dashed rgba(0,0,0,0.12);
  border-radius: 12px;
  background: transparent;
  color: #525252;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.create-btn:hover {
  border-color: #171717;
  color: #171717;
  background: #fafafa;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 150;
}

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.3);
}
.modal-content {
  position: relative;
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  z-index: 1;
}
.modal-content h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #171717;
  margin: 0 0 16px;
}
.modal-content input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 12px;
  font-size: 0.9rem;
  font-family: inherit;
  margin-bottom: 16px;
  outline: none;
}
.modal-content input:focus {
  border-color: #171717;
}
.modal-content p {
  font-size: 0.85rem;
  color: #525252;
  margin: 0 0 8px;
}
.modal-content .warning {
  color: #dc2626;
  font-size: 0.8rem;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
.modal-actions button {
  flex: 1;
  padding: 12px;
  border-radius: 12px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: inherit;
}
.btn-secondary {
  background: #f5f5f5;
  color: #525252;
}
.btn-secondary:hover {
  background: #e5e5e5;
}
.btn-primary {
  background: #171717;
  color: #fff;
}
.btn-primary:hover {
  background: #262626;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-danger {
  background: #dc2626;
  color: #fff;
}
.btn-danger:hover {
  background: #b91c1c;
}
</style>
