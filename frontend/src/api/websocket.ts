export function getWsUrl(path: string, params?: Record<string, string>): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const token = localStorage.getItem('token') || ''
  let url = `${protocol}//${host}${path}?token=${token}`
  if (params) {
    Object.entries(params).forEach(([k, v]) => url += `&${k}=${v}`)
  }
  return url
}
