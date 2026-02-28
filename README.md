# AMD Agentic Hardware Co-Design Platform

An AI-powered multi-agent system for automated hardware design generation using AMD/Xilinx FPGA workflows.

## 🎯 Overview

This platform uses a sequential three-agent pipeline powered by Google Gemini AI:

1. **System Architect** - Designs high-level hardware architecture
2. **RTL Engineer** - Generates synthesizable Verilog code and testbenches
3. **Vivado Integrator** - Creates Vivado TCL scripts and resource estimations

## 🚀 Local Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   - Create a `.env` file in the project root
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```
   - Get your key from: https://aistudio.google.com/app/apikey

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

4. **Add Environment Variable**
   - In Render dashboard, go to "Environment"
   - Add variable:
     - **Key**: `GEMINI_API_KEY`
     - **Value**: Your Gemini API key
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

Response includes architecture design, Verilog code, testbench, and Vivado TCL script.

## 🏆 AMD Sling Shot Hackathon

Built for the AMD Sling Shot Hackathon 2026 - Demonstrating agentic AI workflows for hardware design automation.

Target Platform: Basys 3 (Artix-7 FPGA - xc7a35tcpg236-1)

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **AI**: Google Gemini 2.0 Flash
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: Firebase Firestore
- **Auth**: Firebase Authentication (Google Sign-In)
- **Deployment**: Render (Free tier)
