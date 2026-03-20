// src/store/useCountStore.ts
import { create } from 'zustand'

type Store = {
    count: number
    setCount: (count: number) => void
    increment: () => void
    decrement: () => void
}

const useCountStore = create<Store>((set) => ({
    count: 0,
    setCount: (newCount) => set({ count: newCount }),
    increment: () => set((state) => ({ count: state.count + 1 })),
    decrement: () => set((state) => ({ count: state.count - 1 })),
}))

export default useCountStore
