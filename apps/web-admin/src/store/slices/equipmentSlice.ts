import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { equipmentApi } from '@/api/services/equipment'
import type { Equipment, Brand } from '@/types/equipment'

interface EquipmentState {
  list: Equipment[]
  total: number
  loading: boolean
  brands: Brand[]
  currentEquipment: Equipment | null
}

const initialState: EquipmentState = {
  list: [],
  total: 0,
  loading: false,
  brands: [],
  currentEquipment: null,
}

// 异步获取装备列表
export const fetchEquipmentList = createAsyncThunk(
  'equipment/fetchList',
  async (params: { page: number; page_size: number; category?: string; keyword?: string }) => {
    const response = await equipmentApi.list(params)
    return response
  }
)

// 异步获取品牌列表
export const fetchBrandList = createAsyncThunk(
  'equipment/fetchBrands',
  async () => {
    const response = await equipmentApi.listBrands()
    return response
  }
)

const equipmentSlice = createSlice({
  name: 'equipment',
  initialState,
  reducers: {
    setCurrentEquipment: (state, action) => {
      state.currentEquipment = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchEquipmentList.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchEquipmentList.fulfilled, (state, action) => {
        state.loading = false
        state.list = action.payload.items
        state.total = action.payload.total
      })
      .addCase(fetchEquipmentList.rejected, (state) => {
        state.loading = false
      })
      .addCase(fetchBrandList.fulfilled, (state, action) => {
        state.brands = action.payload
      })
  },
})

export const { setCurrentEquipment } = equipmentSlice.actions
export default equipmentSlice.reducer
