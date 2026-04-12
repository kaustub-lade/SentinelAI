import { useState } from 'react'
import { Shield, Mail, Lock } from 'lucide-react'
import { authAPI } from '../services/api'

export default function Login({ setIsAuthenticated }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await authAPI.login({ email, password })
      localStorage.setItem('sentinelai_token', response.data.access_token)
      localStorage.setItem('sentinelai_user', JSON.stringify(response.data.user))
      setIsAuthenticated(true)
    } catch (err) {
      console.error('Login failed:', err)
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Shield className="w-16 h-16 text-blue-500" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">SentinelAI</h1>
          <p className="text-slate-400">Autonomous Cyber Defense Platform</p>
        </div>

        {/* Login Card */}
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Sign In</h2>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform-translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-10"
                  placeholder="admin@sentinelai.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-10"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 text-lg"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            {error && (
              <p className="text-sm text-red-400 text-center">{error}</p>
            )}
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-400">
              Use a registered account to sign in
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-8">
          © 2026 SentinelAI. Built for Cybersecurity Hackathon.
        </p>
      </div>
    </div>
  )
}
