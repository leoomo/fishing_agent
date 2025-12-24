import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import equipmentReducer from './slices/equipmentSlice'
import crawlerReducer from './slices/crawlerSlice'
import pendingEquipmentReducer from './slices/pendingEquipmentSlice'
import ocrWorkerReducer from './slices/ocrWorkerSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    equipment: equipmentReducer,
    crawler: crawlerReducer,
    pendingEquipment: pendingEquipmentReducer,
    ocrWorker: ocrWorkerReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
