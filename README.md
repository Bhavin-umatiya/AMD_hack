# AMD Agentic Hardware Co-Design Platform

An AI-powered multi-agent system for automated hardware design generation using AMD/Xilinx FPGA workflows.

## 🎯 Overview

This platform uses a sequential three-agent pipeline with **intelligent AI model fallback**:

1. **System Architect** - Designs high-level hardware architecture
2. **RTL Engineer** - Generates synthesizable Verilog code and testbenches
3. **Vivado Integrator** - Creates Vivado TCL scripts and resource estimations

### 🤖 Multi-Model AI System

Each agent independently tries AI models in this order:
- **Primary**: Google Gemini 2.0 Flash (fast, powerful)
- **Fallback**: Groq Llama 3.1 70B (FREE unlimited, ultra-fast)

**Per-Agent Fallback Flow**:
```
User generates design
    ↓
Agent 1: Try Gemini
    ├─ Success? → Use Gemini ✅
    └─ Failed? → Try Groq ✅
    
Agent 2: Try Gemini
    ├─ Success? → Use Gemini ✅
    └─ Failed? → Try Groq ✅
    
Agent 3: Try Gemini
    ├─ Success? → Use Gemini ✅
    └─ Failed? → Try Groq ✅
```

This ensures **maximum reliability** - if Gemini quota is exhausted or fails, Groq takes over seamlessly for each individual agent.

## 🚀 Local Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     # Primary (Gemini) - Get from: https://aistudio.google.com/app/apikey
     GEMINI_API_KEY=your_gemini_api_key_here
     
     # Fallback (Groq) - Get from: https://console.groq.com/keys (FREE)
     GROQ_API_KEY=your_groq_api_key_here
     ```
   - **Note**: At least one API key required. Both recommended for reliability.

3. **Run the Server**
   ```bash
   python app.py
   ```
   Or use the startup scripts:
   - Windows: `start.bat`
   - Linux/Mac: `./start.sh`

4. **Open the Interface**
   - Navigate to `http://localhost:5000` in your browser

## 🌐 Deploy to Render (Free)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration

4. **Add Environment Variables**
   - In Render dashboard, go to "Environment"
   - Add variables:
     - **Key**: `GEMINI_API_KEY` | **Value**: Your Gemini API key
     - **Key**: `GROQ_API_KEY` | **Value**: Your Groq API key (optional)
   - Click "Save Changes"

5. **Deploy**
   - Render will automatically deploy your app
   - Your app will be live at: `https://your-app-name.onrender.com`

## 📡 API Endpoint

**POST** `/generate-agentic-project`

Request body:
```json
{
  "userPrompt": "Design a 32-bit ALU with basic arithmetic operations"
}
```

Response includes:
- Architecture design
- Verilog code & testbench
- Vivado TCL script
- **Models used** (shows which AI was used for each agent)

## 🏆 AMD Sling Shot Hackathon

Built for the AMD Sling Shot Hackathon 2026 - Demonstrating agentic AI workflows for hardware design automation.

Target Platform: Basys 3 (Artix-7 FPGA - xc7a35tcpg236-1)

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **AI Models**: 
  - Google Gemini 2.0 Flash (primary)
  - Groq Llama 3.1 70B (fallback, FREE unlimited)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: Firebase Firestore
- **Auth**: Firebase Authentication (Google Sign-In)
- **Deployment**: Render (Free tier)
