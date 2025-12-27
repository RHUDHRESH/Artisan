// Application configuration
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
  environment: process.env.NODE_ENV || "development",
} as const;

export function buildApiUrl(path: string): string {
  const baseUrl = config.apiUrl;
  const normalizedPath = path.startsWith('/') ? path : `/${path}` ;
  return `${baseUrl}${normalizedPath}` ;
}

export function buildWsUrl(path: string): string {
  const baseUrl = config.wsUrl;
  const normalizedPath = path.startsWith('/') ? path : `/${path}` ;
  // Remove duplicate /ws if path already contains it
  if (normalizedPath.startsWith('/ws')) {
    return baseUrl.replace(/\/ws$/, '') + normalizedPath;
  }
  return `${baseUrl}${normalizedPath}` ;
}

export default config;
