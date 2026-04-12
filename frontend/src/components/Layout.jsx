import { Outlet, NavLink } from 'react-router-dom'
import { Shield, LayoutDashboard, Bug, Mail, AlertTriangle, MessageSquare, LogOut } from 'lucide-react'
import { getStoredUser } from '../utils/session'

export default function Layout({ setIsAuthenticated }) {
  const currentUser = getStoredUser()

  const handleLogout = () => {
    localStorage.removeItem('sentinelai_token')
    localStorage.removeItem('sentinelai_user')
    setIsAuthenticated(false)
  }

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/malware', icon: Bug, label: 'Malware Analysis' },
    { path: '/phishing', icon: Mail, label: 'Phishing Detection' },
    { path: '/vulnerabilities', icon: AlertTriangle, label: 'Vulnerabilities' },
    { path: '/assistant', icon: MessageSquare, label: 'AI Assistant' },
  ]

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="text-xl font-bold text-white">SentinelAI</h1>
              <p className="text-xs text-slate-400">Cyber Defense</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User & Logout */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center justify-between mb-3 px-4 py-2">
            <div>
              <p className="text-sm font-medium text-white">{currentUser?.full_name || 'User'}</p>
              <p className="text-xs text-slate-400">{currentUser?.email || 'unknown@example.com'}</p>
              <p className="text-xs text-blue-300 mt-1 uppercase tracking-wide">{currentUser?.role || 'user'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
