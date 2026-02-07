#Yanjingdou: Multi-Model Cross-Verification Q&A Platform
A reliable AI-powered question-answering tool that leverages cross-verification across multiple models to deliver accurate, credible responses.
🌟 Core Features
Multi-Model Synergy: Integrates Qwen (Alibaba Cloud) and GLM-4 (Zhipu AI) for dual-model parallel reasoning, eliminating biases from single-model outputs.
Neutral Referee Mechanism: Employs an unbiased academic referee system to audit answers for logical flaws, factual errors, and calculation mistakes.
Direct & Verified Responses: Provides immediate answers while presenting cross-verification details (raw model outputs + referee evaluations) for full transparency.
Credibility Rating: Automatically assigns "High/Medium/Low Credibility" scores based on model consistency and referee assessments.
User-Friendly Access: Supports registered accounts (unlimited usage) and guest mode (3 free trials) with secure password encryption.
🚀 Key Advantages
Enhanced Reliability: Cross-validates results across independent models to reduce errors from single-model limitations.
Transparent Reasoning: Displays full audit trails, including raw model outputs and referee feedback, for academic and professional use cases.
Efficient Workflow: Parallel model execution and automated result fusion ensure fast response times without compromising accuracy.
Wide Applicability: Ideal for academic research, technical problem-solving, legal analysis, mathematical calculations, and more.
📋 Usage Scenarios
Complex mathematical calculations and logical reasoning
Academic writing and research verification
Legal and regulatory compliance analysis
Technical troubleshooting and knowledge validation
Decision support requiring high credibility
🚀 Quick Start
Access the Platform: Visit the deployed link (or run locally via the code repository).
Authenticate: Log in with your account or use guest mode (3 free trials).
Submit a Query: Enter your question (supports calculations, reasoning, analysis, etc.).
Get Results: Receive an immediate direct answer + detailed cross-verification report.
⚙️ Technical Stack
Frontend: Gradio (intuitive web interface with responsive design)
Backend: Python 3.9+
AI Models: Qwen-Turbo/Plus (Alibaba Cloud DashScope), GLM-4/Flash (Zhipu AI)
Key Libraries: gradio, dashscope, zhipuai, json, threading
🛠️ Deployment Options
Free Deployment: Deploy via Replit, Hugging Face Spaces, or ngrok (local tunneling).
Self-Hosted: Run on your own server by configuring API keys for Qwen and GLM-4.
API Configuration: Store API keys as environment variables (never hardcode in production).
⚠️ Disclaimer
This tool is for research and learning purposes only—not for commercial or legal decision-making.
Users are responsible for obtaining valid API keys for Qwen and GLM-4 (usage fees apply).
Guest mode is limited to 3 free trials; register an account for unlimited access.
AI-generated content may contain errors—always cross-check critical information with official sources.
📌 Repository Structure
plaintext
Yanjingdou/
├── app.py               # Core application code
├── requirements.txt     # Dependencies
├── config.txt           # Configuration template (API keys not included)
└── README.md            # Documentation
📥 Dependencies
Install required packages via:
bash
运行
pip install -r requirements.txt
gradio>=4.20.0
dashscope
zhipuai
python-dotenv
🔒 Security Notes
Passwords are encrypted using MD5 hashing.
API keys are stored as environment variables (never exposed in code).
User data is securely stored in JSON format with restricted access.
Developed with a focus on reliability, transparency, and user experience—empowering users to trust AI-generated answers through cross-verification.