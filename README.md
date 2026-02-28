# AMD Agentic Hardware Co-Design Platform

An AI-powered multi-agent system for automated hardware design generation using AMD/Xilinx FPGA workflows.

## 🎯 Overview

This platform uses a sequential three-agent pipeline powered by Google Gemini AI:

1. **System Architect** - Designs high-level hardware architecture
2. **RTL Engineer** - Generates synthesizable Verilog code and testbenches
3. **Vivado Integrator** - Creates Vivado TCL scripts and resource estimations

## 🚀 Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   - Open `.env` file
   - Replace `your_gemini_api_key_here` with your actual Gemini API key
   - Get your key from: https://makersuite.google.com/app/apikey

3. **Run the Server**
   ```bash
   python app.py
   ```
   Or use the startup scripts:
   - Windows: `start.bat`
   - Linux/Mac: `./start.sh`

4. **Open the Interface**
   - Navigate to `http://localhost:5000` in your browser
   - Or open `index.html` directly

## 📡 API Endpoint

**POST** `/generate-agentic-project`

Request body:
```json
{
  "userPrompt": "Design a 32-bit ALU with basic arithmetic operations",
  "domain": "Digital Design"
}
```

Response includes architecture design, Verilog code, testbench, and Vivado TCL script.

## 🏆 AMD Sling Shot Hackathon

Built for the AMD Sling Shot Hackathon 2026 - Demonstrating agentic AI workflows for hardware design automation.

Target Platform: Basys 3 (Artix-7 FPGA - xc7a35tcpg236-1)
