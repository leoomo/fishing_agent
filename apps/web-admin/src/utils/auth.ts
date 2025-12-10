const TOKEN_KEY = 'fishing_admin_token'
const USER_KEY = 'fishing_admin_user'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const getUserInfo = (): UserInfo | null => {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? JSON.parse(userStr) : null
}

export const setUserInfo = (user: UserInfo): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const isAuthenticated = (): boolean => {
  return !!getToken()
}

export interface UserInfo {
  user_id: number
  username: string
  role: string
  email?: string
  full_name?: string
}
