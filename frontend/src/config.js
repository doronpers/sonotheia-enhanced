// Shared API configuration for consistent API calls across components

export const apiBase =
  import.meta.env.VITE_API_BASE_URL && import.meta.env.VITE_API_BASE_URL.length > 0
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
    : "";
