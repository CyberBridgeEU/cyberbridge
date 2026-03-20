import { create } from 'zustand'
import { cyberbridge_back_end_rest_api } from '../constants/urls'
import useAuthStore from './useAuthStore'

export interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
}

interface ChatStore {
    messages: ChatMessage[]
    isStreaming: boolean
    error: string | null
    abortController: AbortController | null
    sendMessage: (content: string) => Promise<void>
    cancelStream: () => void
    clearChat: () => void
}

const useChatStore = create<ChatStore>()((set, get) => ({
    messages: [],
    isStreaming: false,
    error: null,
    abortController: null,

    sendMessage: async (content: string) => {
        const { messages, isStreaming } = get()
        if (isStreaming) return

        const token = useAuthStore.getState().token
        if (!token) {
            set({ error: 'Not authenticated. Please log in again.' })
            return
        }

        const userMessage: ChatMessage = { role: 'user', content }
        const updatedMessages = [...messages, userMessage]
        const assistantMessage: ChatMessage = { role: 'assistant', content: '' }

        const abortController = new AbortController()

        set({
            messages: [...updatedMessages, assistantMessage],
            isStreaming: true,
            error: null,
            abortController
        })

        // Trim to last 8 messages (4 turns) for context window
        const contextMessages = updatedMessages.slice(-8)

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/chatbot/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ messages: contextMessages }),
                signal: abortController.signal
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
                throw new Error(errorData.detail || `HTTP ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) throw new Error('No response stream')

            const decoder = new TextDecoder()
            let buffer = ''
            let assistantContent = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                // Keep the last potentially incomplete line in buffer
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue
                    const data = line.slice(6).trim()

                    if (data === '[DONE]') break

                    try {
                        const parsed = JSON.parse(data)
                        if (parsed.error) {
                            set({ error: parsed.error, isStreaming: false, abortController: null })
                            return
                        }
                        if (parsed.token) {
                            assistantContent += parsed.token
                            // Update the last message (assistant) with accumulated content
                            set(state => {
                                const msgs = [...state.messages]
                                msgs[msgs.length - 1] = { role: 'assistant', content: assistantContent }
                                return { messages: msgs }
                            })
                        }
                    } catch {
                        // Skip unparseable lines
                    }
                }
            }

            set({ isStreaming: false, abortController: null })
        } catch (err: unknown) {
            if (err instanceof DOMException && err.name === 'AbortError') {
                // User cancelled — keep partial response
                set({ isStreaming: false, abortController: null })
                return
            }
            const errorMessage = err instanceof Error ? err.message : 'An error occurred'
            set({ error: errorMessage, isStreaming: false, abortController: null })
        }
    },

    cancelStream: () => {
        const { abortController } = get()
        if (abortController) {
            abortController.abort()
            set({ isStreaming: false, abortController: null })
        }
    },

    clearChat: () => {
        const { abortController } = get()
        if (abortController) abortController.abort()
        set({ messages: [], isStreaming: false, error: null, abortController: null })
    }
}))

export default useChatStore
