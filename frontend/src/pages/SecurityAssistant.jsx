import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { assistantAPI } from '../services/api'

export default function SecurityAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hello! I\'m your AI Security Assistant. I can help you with:\n\n• Analyzing threats and vulnerabilities\n• Explaining CVEs in simple terms\n• Providing security recommendations\n• Answering security policy questions\n\nWhat would you like to know?',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadSuggestions()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadSuggestions = async () => {
    try {
      const response = await assistantAPI.getSuggestions()
      setSuggestions(response.data.suggestions.slice(0, 4))
    } catch (error) {
      console.error('Error loading suggestions:', error)
    }
  }

  const handleSend = async (message = input) => {
    if (!message.trim()) return

    const userMessage = {
      role: 'user',
      content: message,
    }

    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await assistantAPI.chat(message)
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
      }
      setMessages((prev) => [...prev, assistantMessage])

      if (response.data.suggestions) {
        setSuggestions(response.data.suggestions)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion)
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-700 bg-slate-900">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">AI Security Assistant</h1>
            <p className="text-slate-400">Natural language security intelligence</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
              </div>
            )}

            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-100'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                  <User className="w-6 h-6 text-slate-300" />
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="bg-slate-800 rounded-lg p-4">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestions */}
      {suggestions.length > 0 && (
        <div className="px-6 pb-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">Quick Actions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-sm transition-colors border border-slate-700"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-6 border-t border-slate-700 bg-slate-900">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) =>setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything about security..."
            className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Press Enter to send • AI responses may take a few seconds
        </p>
      </div>
    </div>
  )
}
