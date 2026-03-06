# 🛡️ SentinelAI - Autonomous Cyber Defense Platform

**AI-Powered Cybersecurity Platform for Modern Threat Detection & Response**

![SentinelAI](https://img.shields.io/badge/AI-Cybersecurity-blue)
![React](https://img.shields.io/badge/React-18.x-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Python](https://img.shields.io/badge/Python-3.11-3776ab)

## 🎯 Problem Statement

As cyber threats evolve rapidly, traditional security systems struggle to detect sophisticated attacks such as:
- **Polymorphic malware** - constantly changing code
- **Deepfake phishing** campaigns
- **Adversarial intrusions**
- **Automated vulnerability exploitation**

SentinelAI addresses these challenges with an intelligent, adaptive, and proactive cybersecurity system.

## ✨ Features

### 🔍 1. AI Malware Detection Engine
- Detects polymorphic and adversarial malware
- Behavioral analysis using machine learning
- File entropy and opcode analysis
- Integration with VirusTotal API

### 🎭 2. Deepfake & Phishing Detection
- Email phishing detection using NLP
- Domain reputation analysis
- Suspicious content identification
- Text and media analysis capabilities

### 📊 3. Intelligent Vulnerability Prioritization
- CVE database integration
- Asset criticality scoring
- Risk-based prioritization
- Exploit availability tracking

### 🤖 4. AI Security Assistant
- Natural language security policy queries
- Chatbot interface for threat intelligence
- Automated security recommendations
- Real-time threat explanations

### ⚡ 5. Automated Response Engine
- Real-time threat scoring
- Automated alert system
- Threat containment actions
- Incident response workflows

### 🎨 6. Generative Evasion Countermeasures
- Deceptive network responses
- Traffic simulation
- Honeypot capabilities

## 🏗️ Architecture

```
SentinelAI
│
├── Frontend (React + Tailwind CSS)
│   ├── Dashboard
│   ├── Malware Analyzer
│   ├── Phishing Detector
│   ├── Vulnerability Intelligence
│   └── Security AI Chat
│
├── Backend (FastAPI)
│   ├── Malware Detection Service
│   ├── Phishing Detection Service
│   ├── CVE Intelligence Engine
│   ├── AI Assistant Service
│   └── Threat Analytics
│
└── External Integrations
    ├── NVD CVE Database
    ├── VirusTotal API
    ├── OpenAI API
    └── Threat Intelligence Feeds
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- API Keys (Optional but recommended):
  - OpenAI API Key
  - VirusTotal API Key

### Installation

#### 1. Clone the repository
```bash
git clone https://github.com/yourusername/sentinelai.git
cd sentinelai
```

#### 2. Setup Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

Create `.env` file in backend directory:
```env
OPENAI_API_KEY=your_openai_key_here
VIRUSTOTAL_API_KEY=your_virustotal_key_here
```

Start backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

#### 3. Setup Frontend
```bash
cd frontend
npm install
```

Create `.env` file in frontend directory:
```env
VITE_API_URL=http://localhost:8000
```

Start development server:
```bash
npm run dev
```

#### 4. Access the Application
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## 📱 UI Pages

1. **Login Page** - Secure authentication
2. **Main Dashboard** - Threat overview and analytics
3. **Malware Analysis** - File upload and analysis
4. **Phishing Detection** - Email and URL scanning
5. **Vulnerability Intelligence** - CVE prioritization
6. **Security AI Chat** - Natural language queries
7. **Settings** - Configuration and API management

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **React Router** - Navigation
- **Axios** - API client

### Backend
- **FastAPI** - Web framework
- **Python 3.11** - Programming language
- **Scikit-learn** - ML models
- **Transformers** - NLP models
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation

### AI/ML
- **OpenAI GPT** - Security assistant
- **HuggingFace** - Phishing detection
- **Custom ML Models** - Malware detection

## 📊 Key Modules

### Malware Detection
Uses machine learning to analyze:
- File hash and signatures
- Behavioral patterns
- API calls and syscalls
- Entropy analysis
- Opcode frequency

### Phishing Detection
Analyzes emails for:
- Suspicious sender domains
- Malicious URLs
- Social engineering patterns
- Grammar and urgency indicators

### CVE Intelligence
Prioritizes vulnerabilities based on:
- CVSS scores
- Asset criticality
- Exploit availability
- Threat actor activity

## 🔐 Security Features

- JWT-based authentication
- Role-based access control
- API rate limiting
- Secure file handling
- Encrypted data storage

## 📈 Future Enhancements

- [ ] Real-time threat intelligence feeds
- [ ] Advanced deepfake detection
- [ ] Network traffic analysis
- [ ] SIEM integration
- [ ] Mobile app support
- [ ] Multi-tenant support

## 🤝 Contributing

This is a hackathon project. Contributions, issues, and feature requests are welcome!

## 📄 License

MIT License

## 👥 Team

Built for CyberSecurity Hackathon 2026

## 🙏 Acknowledgments

- NVD CVE Database
- VirusTotal
- OpenAI
- HuggingFace Community

---

**⚠️ Disclaimer:** This is a prototype built for educational and hackathon purposes. Not intended for production use without further security hardening.
