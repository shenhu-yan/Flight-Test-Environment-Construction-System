import { ref, onUnmounted } from 'vue'

export function useWebSocket(url: string, onMessage: (data: any) => void) {
  const connected = ref(false)
  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  let heartbeatTimer: number | null = null

  function connect() {
    // URL already contains token from getWsUrl, do NOT append another ?token=
    ws = new WebSocket(url)
    
    ws.onopen = () => {
      connected.value = true
      heartbeatTimer = window.setInterval(() => {
        ws?.send(JSON.stringify({ type: 'heartbeat' }))
      }, 30000)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch {}
    }
    
    ws.onclose = () => {
      connected.value = false
      if (heartbeatTimer) clearInterval(heartbeatTimer)
      reconnectTimer = window.setTimeout(connect, 3000)
    }
    
    ws.onerror = () => ws?.close()
  }
  
  function send(data: any) {
    ws?.send(JSON.stringify(data))
  }
  
  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (heartbeatTimer) clearInterval(heartbeatTimer)
    ws?.close()
  }
  
  connect()
  onUnmounted(disconnect)
  
  return { connected, send, disconnect }
}
