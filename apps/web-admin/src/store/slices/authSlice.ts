import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { authApi, type LoginRequest } from '@/api/services/auth'
import { setToken, setUserInfo, clearToken, type UserInfo } from '@/utils/auth'

interface AuthState {
  isAuthenticated: boolean
  user: UserInfo | null
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  loading: false,
  error: null,
}

// 异步登录
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials)
      setToken(response.access_token)
      setUserInfo(response.user)
      return response
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      return rejectWithValue(err.response?.data?.detail || '登录失败')
    }
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      clearToken()
    },
    setAuth: (state, action) => {
      state.isAuthenticated = true
      state.user = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { logout, setAuth } = authSlice.actions
export default authSlice.reducer
