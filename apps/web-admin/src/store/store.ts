import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import equipmentReducer from './slices/equipmentSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    equipment: equipmentReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
