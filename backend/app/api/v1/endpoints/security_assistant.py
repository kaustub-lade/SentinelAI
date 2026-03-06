"""
Security AI Assistant Endpoints - Natural Language Security Queries
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
from datetime import datetime

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    suggestions: Optional[List[str]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Chat with AI Security Assistant
    Natural language interface for security queries
    """
    user_message = request.message.lower()
    
    # Simple pattern matching for demo - replace with actual LLM
    if "vulnerability" in user_message or "cve" in user_message:
        response = """**Vulnerability Analysis:**

Based on the latest scan, here are your top priority vulnerabilities:

1. **CVE-2024-3094** (CVSS 9.8) - XZ Utils Backdoor
   - **Risk**: Critical
   - **Affected Systems**: 45 servers
   - **Action**: Immediate patching required

2. **CVE-2024-1234** (CVSS 8.5) - OpenSSL RCE
   - **Risk**: High
   - **Affected Systems**: 128 endpoints
   - **Action**: Patch within 24 hours

3. **CVE-2024-5678** (CVSS 7.2) - Apache DoS
   - **Risk**: Medium
   - **Affected Systems**: 23 servers
   - **Action**: Schedule patching this week

**Recommendation**: Focus on CVE-2024-3094 first as it's actively being exploited."""
        
        suggestions = [
            "Show me patch details for CVE-2024-3094",
            "What are the latest critical vulnerabilities?",
            "How do I mitigate CVE-2024-3094?"
        ]
    
    elif "malware" in user_message:
        response = """**Malware Detection Summary:**

In the last 24 hours, our AI detection engine has identified:

- **4 malicious files** detected and quarantined
- **7 suspicious files** under investigation
- **94% detection accuracy** with minimal false positives

**Recent Detections:**
1. Trojan.Generic.KD - Blocked at email gateway
2. Ransomware.Lockbit - Quarantined from endpoint
3. Spyware.InfoStealer - Removed from network share

**Recommendation**: All threats have been contained. Review quarantined files in the Malware Analysis dashboard."""
        
        suggestions = [
            "Show me details of recent malware detections",
            "How does the AI malware detection work?",
            "Scan a file for malware"
        ]
    
    elif "phishing" in user_message:
        response = """**Phishing Detection Report:**

Today's phishing detection statistics:

- **12 phishing emails** blocked automatically
- **5 suspicious URLs** flagged for review
- **98% detection accuracy**

**Top Phishing Attempts:**
1. Fake banking verification emails
2. Package delivery scams
3. Account suspension threats

**Trends**: Increased phishing activity targeting financial services. AI models have been updated with new patterns.

**Recommendation**: Continue user security awareness training."""
        
        suggestions = [
            "Check if an email is phishing",
            "What are common phishing indicators?",
            "Show phishing detection history"
        ]
    
    elif "threat" in user_message or "attack" in user_message:
        response = """**Current Threat Landscape:**

**Active Threats:** 14 detected today
- 🔴 Critical: 3
- 🟠 High: 5
- 🟡 Medium: 6

**Threat Types:**
- Malware attempts: 4
- Phishing campaigns: 7
- Suspicious activity: 3

**Geographic Distribution:**
- Most attacks from: Russia, China, Brazil
- Target services: Web applications, email, endpoints

**System Status:** All threats contained. No active incidents.

**Recommendation**: Monitor the 3 critical alerts in real-time."""
        
        suggestions = [
            "Show me critical threats",
            "What's the current risk score?",
            "Block suspicious IP addresses"
        ]
    
    elif "recommendation" in user_message or "what should" in user_message:
        response = """**Security Recommendations:**

Based on AI analysis of your environment:

**Immediate Actions:**
1. ✅ Patch CVE-2024-3094 on all affected systems
2. ✅ Review and block 5 suspicious IP addresses
3. ✅ Update email gateway rules for new phishing patterns

**This Week:**
- Schedule security awareness training for users
- Review access controls for critical assets
- Update firewall rules based on threat intelligence

**Long-term:**
- Implement zero-trust architecture
- Deploy advanced endpoint protection
- Enhance SIEM correlation rules

**Risk Reduction**: These actions will reduce your risk score from 75 to 45."""
        
        suggestions = [
            "How do I implement these recommendations?",
            "Show me the risk score breakdown",
            "Generate a security report"
        ]
    
    elif "help" in user_message or "what can you do" in user_message:
        response = """**🤖 SentinelAI Security Assistant**

I'm your AI-powered cybersecurity expert. I can help you with:

**Threat Intelligence:**
- Analyze current threats and vulnerabilities
- Explain CVEs in simple terms
- Prioritize security issues

**Detection & Response:**
- Check files for malware
- Detect phishing emails and URLs
- Provide incident response guidance

**Vulnerability Management:**
- List critical vulnerabilities
- Recommend patching priorities
- Track vulnerability trends

**Security Insights:**
- Security posture assessment
- Risk score analysis
- Compliance recommendations

**Example Questions:**
- "What are my critical vulnerabilities?"
- "Is this email a phishing attempt?"
- "What threats were detected today?"
- "How can I improve my security posture?"

How can I assist you today?"""
        
        suggestions = [
            "What are my critical vulnerabilities?",
            "Show me today's threat summary",
            "How is my security posture?"
        ]
    
    else:
        response = f"""I understand you're asking about: "{request.message}"

As your AI Security Assistant, I can provide insights on:
- Threat detection and analysis
- Vulnerability management
- Malware and phishing detection
- Security recommendations
- Risk assessment

Could you please provide more specific details about what you'd like to know? 

For example:
- "What are my top vulnerabilities?"
- "Analyze recent threats"
- "Check if a file is malicious"
- "Show phishing attempts today" """
        
        suggestions = [
            "What are my critical vulnerabilities?",
            "Show today's threat summary",
            "Help me understand CVE-2024-3094"
        ]
    
    conversation_id = request.conversation_id or f"conv_{random.randint(10000, 99999)}"
    
    return ChatResponse(
        response=response,
        conversation_id=conversation_id,
        suggestions=suggestions
    )


@router.get("/suggestions")
async def get_quick_suggestions():
    """
    Get quick action suggestions
    """
    return {
        "suggestions": [
            "What are my critical vulnerabilities?",
            "Show me today's threat summary",
            "Is my system secure?",
            "What malware was detected recently?",
            "Check for phishing attempts",
            "Explain CVE-2024-3094",
            "How can I improve security?",
            "What's my current risk score?"
        ]
    }


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history
    """
    # Mock conversation history
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": "user",
                "content": "What are my critical vulnerabilities?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Based on latest scan, you have 3 critical vulnerabilities requiring immediate attention...",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }


@router.post("/feedback")
async def submit_feedback(conversation_id: str, rating: int, feedback: Optional[str] = None):
    """
    Submit feedback for AI responses
    """
    return {
        "message": "Feedback received",
        "conversation_id": conversation_id,
        "rating": rating
    }
