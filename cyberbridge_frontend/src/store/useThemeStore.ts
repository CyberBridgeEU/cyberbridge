import { create } from 'zustand';

type Theme = 'light' | 'dark' | 'dark-glass';

interface ThemeStore {
    theme: Theme;
    setTheme: (theme: Theme) => void;
}

const useThemeStore = create<ThemeStore>((set) => ({
    theme: (localStorage.getItem('cyberbridge-theme') as Theme) || 'light',
    setTheme: (theme: Theme) => {
        localStorage.setItem('cyberbridge-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
    },
}));

export default useThemeStore;
