import { useState } from 'react'
import { Mail, AlertTriangle, CheckCircle, Shield } from 'lucide-react'
import { phishingAPI } from '../services/api'

export default function PhishingDetection() {
  const [emailData, setEmailData] = useState({
    sender_email: '',
    subject: '',
    email_content: '',
  })
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)

  const handleChange = (e) => {
    setEmailData({
      ...emailData,
      [e.target.name]: e.target.value,
    })
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      const response = await phishingAPI.checkEmail(emailData)
      setResult(response.data)
    } catch (error) {
      console.error('Error analyzing email:', error)
      alert('Error analyzing email. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'Critical':
        return 'text-red-500'
      case 'High':
        return 'text-orange-500'
      case 'Medium':
        return 'text-yellow-500'
      case 'Low':
        return 'text-green-500'
      default:
        return 'text-slate-400'
    }
  }

  const getRiskLevelBg = (level) => {
    switch (level) {
      case 'Critical':
        return 'bg-red-900'
      case 'High':
        return 'bg-orange-900'
      case 'Medium':
        return 'bg-yellow-900'
      case 'Low':
        return 'bg-green-900'
      default:
        return 'bg-slate-900'
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Phishing Detection</h1>
        <p className="text-slate-400">Analyze emails for phishing attempts using NLP and pattern recognition</p>
      </div>

      {/* Input Form */}
      <div className="card p-6 mb-8">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Mail className="w-6 h-6" />
          Email Analysis
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Sender Email
            </label>
            <input
              type="email"
              name="sender_email"
              value={emailData.sender_email}
              onChange={handleChange}
              className="input-field"
              placeholder="sender@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email Subject
            </label>
            <input
              type="text"
              name="subject"
              value={emailData.subject}
              onChange={handleChange}
              className="input-field"
              placeholder="Urgent: Verify your account"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email Content
            </label>
            <textarea
              name="email_content"
              value={emailData.email_content}
              onChange={handleChange}
              className="input-field"
              rows="8"
              placeholder="Paste email content here..."
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={analyzing || !emailData.email_content}
            className="btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {analyzing ? 'Analyzing...' : 'Analyze Email'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Verdict Card */}
          <div className="card p-8">
            <div className="text-center mb-6">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
                result.is_phishing ? getRiskLevelBg(result.risk_level) : 'bg-green-900'
              }`}>
                {result.is_phishing ? (
                  <AlertTriangle className="w-8 h-8 text-red-400" />
                ) : (
                  <CheckCircle className="w-8 h-8 text-green-400" />
                )}
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">
                {result.is_phishing ? (
                  <span className="text-red-500">⚠️ Phishing Detected</span>
                ) : (
                  <span className="text-green-500">✓ Email Appears Safe</span>
                )}
              </h2>
              <p className="text-slate-400 mb-4">
                Confidence: <span className="text-white font-mono">{(result.confidence * 100).toFixed(1)}%</span>
              </p>
              <span className={`inline-block px-4 py-2 rounded-full font-medium ${
                result.risk_level === 'Critical' ? 'bg-red-900 text-red-200' :
                result.risk_level === 'High' ? 'bg-orange-900 text-orange-200' :
                result.risk_level === 'Medium' ? 'bg-yellow-900 text-yellow-200' :
                'bg-green-900 text-green-200'
              }`}>
                Risk Level: {result.risk_level}
              </span>
            </div>
          </div>

          {/* Detected Indicators */}
          {result.detected_indicators.length > 0 && (
            <div className="card p-6">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-orange-400" />
                Detected Phishing Indicators
              </h3>
              <div className="space-y-2">
                {result.detected_indicators.map((indicator, index) => (
                  <div key={index} className="p-3 bg-orange-900/20 border border-orange-700 rounded-lg flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <p className="text-orange-300">{indicator}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis Details */}
          <div className="card p-6">
            <h3 className="text-xl font-bold text-white mb-4">Analysis Details</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(result.analysis).map(([key, value]) => (
                <div key={key} className="p-4 bg-slate-700 rounded-lg">
                  <p className="text-slate-400 text-sm capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="text-white text-lg font-bold mt-1">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="card p-6">
            <h3 className="text-xl font-bold text-white mb-4">Recommendations</h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className={`mt-1 ${result.is_phishing ? 'text-red-400' : 'text-green-400'}`}>
                    {result.is_phishing ? '⚠' : '✓'}
                  </span>
                  <span className="text-slate-300">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
