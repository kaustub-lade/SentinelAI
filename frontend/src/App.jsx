import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import MalwareAnalysis from './pages/MalwareAnalysis'
import PhishingDetection from './pages/PhishingDetection'
import VulnerabilityIntelligence from './pages/VulnerabilityIntelligence'
import SecurityAssistant from './pages/SecurityAssistant'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
            <Navigate to="/dashboard" /> : 
            <Login setIsAuthenticated={setIsAuthenticated} />
          } 
        />
        
        <Route
          path="/"
          element={
            isAuthenticated ? 
            <Layout setIsAuthenticated={setIsAuthenticated} /> : 
            <Navigate to="/login" />
          }
        >
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="malware" element={<MalwareAnalysis />} />
          <Route path="phishing" element={<PhishingDetection />} />
          <Route path="vulnerabilities" element={<VulnerabilityIntelligence />} />
          <Route path="assistant" element={<SecurityAssistant />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  )
}

export default App
