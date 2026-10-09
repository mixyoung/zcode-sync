import { useState, useEffect, useCallback } from "react";

export type ThemeMode = "system" | "light" | "dark";

const THEME_STORAGE_KEY = "zcode_theme_preference";

export function useTheme() {
  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored === "light" || stored === "dark" || stored === "system") {
        return stored;
      }
    } catch {}
    return "system"; // 默认跟随系统主题
  });

  const [resolvedDark, setResolvedDark] = useState<boolean>(() => {
    if (typeof window === "undefined") return true;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  const applyTheme = useCallback((mode: ThemeMode) => {
    const isSysDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const shouldBeDark = mode === "dark" ? true : mode === "light" ? false : isSysDark;

    setResolvedDark(shouldBeDark);

    if (shouldBeDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch {}
    applyTheme(mode);
  };

  useEffect(() => {
    applyTheme(themeMode);

    // 监听系统深浅色变化事件
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      if (themeMode === "system") {
        applyTheme("system");
      }
    };

    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [themeMode, applyTheme]);

  return {
    themeMode,
    resolvedDark,
    setThemeMode,
  };
}
