import { useState, useEffect } from 'react'
import { Activity, Shield, AlertTriangle, Bug, TrendingUp, ShieldAlert, MailWarning, MessageSquareText, Download } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { dashboardAPI, reportsAPI } from '../services/api'
import { getStoredUser, isPrivilegedRole } from '../utils/session'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [threats, setThreats] = useState([])
  const [timeline, setTimeline] = useState([])
  const [distribution, setDistribution] = useState([])
  const [activity, setActivity] = useState([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [currentUser] = useState(() => getStoredUser())
  const canAccessReports = isPrivilegedRole(currentUser)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [statsRes, threatsRes, timelineRes, distRes, activityRes] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getRecentThreats(),
        dashboardAPI.getThreatTimeline(),
        dashboardAPI.getThreatDistribution(),
        canAccessReports ? dashboardAPI.getActivity() : Promise.resolve({ data: { activity: [] } }),
      ])

      setStats(statsRes.data)
      setThreats(threatsRes.data.threats.slice(0, 5))
      setTimeline(timelineRes.data.timeline)
      setDistribution(distRes.data.distribution)
      setActivity(activityRes?.data?.activity || [])
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const downloadReports = async () => {
    try {
      setExporting(true)
      const response = await reportsAPI.exportBundle('all')
      const blob = new Blob([response.data], { type: 'application/zip' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `sentinelai-reports-${new Date().toISOString().replace(/[:.]/g, '-')}.zip`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Error exporting reports:', error)
    } finally {
      setExporting(false)
    }
  }

  const StatCard = ({ icon: Icon, title, value, trend, color }) => (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <span className="text-green-400 text-sm flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            {trend}
          </span>
        )}
      </div>
      <h3 className="text-slate-400 text-sm font-medium">{title}</h3>
      <p className="text-3xl font-bold text-white mt-1">{value}</p>
    </div>
  )

  const getSeverityBadge = (severity) => {
    const badges = {
      Critical: 'badge-critical',
      High: 'badge-high',
      Medium: 'badge-medium',
      Low: 'badge-low',
    }
    return badges[severity] || 'badge-low'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Security Dashboard</h1>
            <p className="text-slate-400">Real-time threat monitoring and analytics</p>
          </div>
          {canAccessReports && (
            <button
              onClick={downloadReports}
              disabled={exporting}
              className="inline-flex items-center gap-2 px-4 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
              {exporting ? 'Exporting...' : 'Download Reports'}
            </button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={AlertTriangle}
          title="Total Threats Today"
          value={stats?.total_threats_today || 0}
          color="bg-red-600"
        />
        <StatCard
          icon={Shield}
          title="Critical Alerts"
          value={stats?.critical_alerts || 0}
          color="bg-orange-600"
        />
        <StatCard
          icon={Bug}
          title="Malware Detected"
          value={stats?.malware_detected || 0}
          color="bg-purple-600"
        />
        <StatCard
          icon={Activity}
          title="Risk Score"
          value={stats?.risk_score || 0}
          color="bg-blue-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Threat Timeline */}
        <div className="lg:col-span-2 card p-6">
          <h2 className="text-xl font-bold text-white mb-4">Threat Timeline (24h)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="timestamp" 
                stroke="#94a3b8"
                tickFormatter={(value) => new Date(value).getHours() + ':00'}
              />
              <YAxis stroke="#94a3b8" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Line type="monotone" dataKey="malware" stroke="#ef4444" strokeWidth={2} />
              <Line type="monotone" dataKey="phishing" stroke="#f59e0b" strokeWidth={2} />
              <Line type="monotone" dataKey="vulnerabilities" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Threat Distribution */}
        <div className="card p-6">
          <h2 className="text-xl font-bold text-white mb-4">Threat Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Activity Feed */}
      {canAccessReports && (
        <div className="card p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Recent Activity</h2>
            <span className="text-slate-400 text-sm">Audit trail</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activity.length > 0 ? activity.map((item) => (
              <div key={item.id} className="rounded-lg border border-slate-700 bg-slate-800/60 p-4">
                <div className="flex items-start gap-3">
                  <div className={`mt-1 p-2 rounded-lg ${item.severity === 'warning' ? 'bg-amber-600' : 'bg-blue-600'}`}>
                    {item.action.includes('assistant') ? <MessageSquareText className="w-4 h-4 text-white" /> : item.action.includes('phishing') ? <MailWarning className="w-4 h-4 text-white" /> : <ShieldAlert className="w-4 h-4 text-white" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-white font-medium truncate">{item.action}</p>
                    <p className="text-slate-400 text-sm">{item.resource_type || 'system'} {item.resource_id ? `• ${item.resource_id}` : ''}</p>
                    <p className="text-slate-500 text-xs mt-1">{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )) : (
              <p className="text-slate-400 text-sm">No audit events recorded yet.</p>
            )}
          </div>
        </div>
      )}

      {/* Recent Threats Table */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-white mb-4">Recent Threats</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Type</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Severity</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Description</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Source IP</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {threats.map((threat) => (
                <tr key={threat.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-3 px-4 text-white font-medium">{threat.type}</td>
                  <td className="py-3 px-4">
                    <span className={getSeverityBadge(threat.severity)}>
                      {threat.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{threat.description}</td>
                  <td className="py-3 px-4 text-slate-300 font-mono text-sm">{threat.source_ip}</td>
                  <td className="py-3 px-4">
                    <span className="text-green-400 text-sm">{threat.status}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-sm">
                    {new Date(threat.timestamp).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
