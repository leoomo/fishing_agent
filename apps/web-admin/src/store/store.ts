import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import equipmentReducer from './slices/equipmentSlice'
import crawlerReducer from './slices/crawlerSlice'
import pendingEquipmentReducer from './slices/pendingEquipmentSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    equipment: equipmentReducer,
    crawler: crawlerReducer,
    pendingEquipment: pendingEquipmentReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
