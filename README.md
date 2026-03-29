# 🚀 AMD Agentic Hardware Co-Design Platform
**AMD Sling Shot Hackathon 2026 - Winner Category Submission**

[![Render](https://img.shields.io/badge/Render-Live_Site-ED1C24?style=for-the-badge&logo=render&logoColor=white)](https://amd-hardware-agent.onrender.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth_%26_Sync-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://console.firebase.google.com/)
[![FPGA](https://img.shields.io/badge/Target-Basys_3-4ade80?style=for-the-badge&logo=fpga&logoColor=black)]()

An industrial-grade, AI-powered multi-agent system designed to automate the hardware co-design process for AMD/Xilinx FPGAs. From natural language to synthesizable RTL and Vivado build scripts in seconds.

---

## 💎 Premium Features

-   **🧠 Sequential Agentic Pipeline**: Three autonomous AI agents (Architect, RTL Engineer, Vivado Integrator) collaborating with intelligent failover (Gemini 2.0 ↔ Groq Llama 3).
-   **🔌 Professional RTL Toolchain**: Built-in `iverilog` simulation and `yosys` gate-level synthesis for industrial RTL visualization.
-   **📱 Mobile-Responsive Ultra-UI**: A stunning glassmorphic interface optimized for both high-end workstations and mobile previews.
-   **☁️ Cloud Silicon Memory**: Real-time project syncing and AI Chat persistence powered by Firebase Firestore and Google Auth.
-   **📦 Vivado-Ready Export**: One-click ZIP export containing structured RTL, Testbenches, and Vivado Tcl build scripts.

---

## 🕵️‍♂️ The Agentic Design Flow

This platform uses a high-reliability fallback system to ensure your hardware is generated even during high-traffic periods:

1.  **System Architect**: Translates requirements into a structured hardware block diagram.
2.  **RTL Engineer**: Generates high-performance Verilog code and comprehensive testbenches.
3.  **Vivado Integrator**: Crafts the Tcl build pipeline and calculates resource estimations for Artix-7.

**Reliability Logic**: 
`Gemini 2.0 Flash (Primary) ➡️ Groq Llama 3.1 70B (Failover)`

---

## 🛠️ Industrial Toolchain Integration

We don't just generate text; we verify hardware.
-   **Verification**: Real-time `iverilog` simulation with full log capture.
-   **Synthesis**: Gate-level netlist generation using **Yosys**.
-   **Visualization**: Auto-generated High-Contrast RTL Schematics via **Netlistsvg**.

---

## 🚀 Rapid Deployment

### **Cloud Environment (Recommended)**
The platform is pre-configured for **Render** (Backend) and **Firebase** (Frontend).
1.  Connect your GitHub repo to Render.
2.  Add `GEMINI_API_KEY` and `GROQ_API_KEY` to Environment Variables.
3.  Ensure Firebase Auth and Firestore are enabled in your project Console.

### **Local Engineering Setup**
```bash
# 1. Clone & Install
git clone https://github.com/Bhavin-umatiya/AMD_hack.git
pip install -r requirements.txt

# 2. Configure
# Create .env with GEMINI_API_KEY and GROQ_API_KEY

# 3. Launch
python app.py
```

---

## 🏆 Hackathon Details
-   **Target Board**: Digilent Basys 3
-   **FPGA**: Xilinx Artix-7 (xc7a35tcpg236-1)
-   **Project Lead**: Bhavin Umatiya
-   **System Engineers**: Bhavin / Nishant

---
*Built with ❤️ for the AMD Sling Shot Hackathon 2026. Transforming the future of Agentic Hardware Design.*
