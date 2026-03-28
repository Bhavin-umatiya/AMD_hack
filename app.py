import os
import json
import re
import subprocess
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, send_from_directory, g
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai
from google.genai import types
from dotenv import load_dotenv
from io import BytesIO
import zipfile

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Security headers (allow inline scripts/styles for Firebase SDK and inline styles)
Talisman(app,
    force_https=False,  # Allow HTTP in development
    content_security_policy=None  # Disable CSP for hackathon (Firebase SDK needs inline)
)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)

# Log all requests
@app.before_request
def log_request():
    print(f"\n📥 Incoming Request: {request.method} {request.path}")
    if request.is_json:
        print(f"   JSON Body: {request.get_json()}")

@app.after_request
def add_headers(response):
    # Prevent caching for API and static files
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables")
    print("Please set GEMINI_API_KEY in Render dashboard under Environment Variables")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini client initialized")

# Configure Groq API (fallback)
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized")
    else:
        groq_client = None
        print("⚠️ GROQ_API_KEY not found - fallback disabled")
except ImportError:
    groq_client = None
    print("⚠️ Groq package not installed - fallback disabled")

if not gemini_client and not groq_client:
    raise ValueError("Neither GEMINI_API_KEY nor GROQ_API_KEY configured. At least one is required.")

# Helper to get/set request-scoped gemini_failed flag
def get_gemini_failed():
    return getattr(g, 'gemini_failed', False)

def set_gemini_failed(value):
    g.gemini_failed = value

# Agent 1: System Architect Prompt Template
ARCHITECT_PROMPT = """You are a Senior Silicon Architect at AMD. Your job is to design the high-level architecture for a user's hardware project idea.

User Request: '{user_prompt}'

You must break this down into logical hardware blocks.
Return ONLY a valid JSON object with the following keys:

projectTitle: Create a professional, concise title for this hardware project based on the description.

architectureDescription: A paragraph explaining the data path, control unit, and how data flows through the system.

moduleList: An array of strings, listing the exact Verilog modules that need to be created (e.g., ['alu_32bit', 'control_unit', 'register_file']). Do NOT use markdown formatting outside the JSON."""

# Agent 2: RTL & Verification Engineer Prompt Template
RTL_ENGINEER_PROMPT = """You are an Expert Verilog RTL Engineer for AMD/Xilinx FPGAs.

Design: {architecture_json}

Generate MINIMAL synthesizable Verilog (under 40 lines) and brief testbench (under 15 lines).

Return JSON with escaped newlines (\\n not actual newlines):
{{"verilogCode": "module x();\\nendmodule", "testbenchCode": "module tb();\\nendmodule"}}

Keep it SHORT and SIMPLE. Escape ALL newlines as \\n"""

# Agent 3: AMD Vivado Integrator Prompt Template
VIVADO_INTEGRATOR_PROMPT = """You are an AMD Vivado Expert. 
Project: '{project_title}' 
Target FPGA: AMD Artix-7 (Basys 3)
RTL Code for Analysis:
{rtl_code}

Your task is to generate a dynamic TCL script that:
1. Creates a project named after the title.
2. Adds the file 'design.v' (which contains the RTL code above).
3. Sets the CORRECT top module based on the 'RTL Code for Analysis' above.
4. Runs synthesis and implementation.

Also estimate the resource utilization (Est. LUTs, FFs, BRAM) specifically for THIS logic.

Return ONLY a valid JSON object:
{{"vivadoTclScript": "# TCL\\ncreate_project...\\nadd_files...\\nset_property top [TopModuleName]...", "resourceEstimation": "Design-specific: 120 LUTs, 45 FFs"}}

Keep script under 15 lines. Escape ALL newlines as \\n."""

# ========================================
# SERVE FRONTEND FILES
# ========================================

@app.route('/')
def home():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_files(filename):
    """Serve other files from root directory"""
    # Prevent directory traversal attacks
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid path"}), 400
    
    # Check if file exists in root directory
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    
    return jsonify({"error": "File not found"}), 404

# ========================================
# AI AGENT FUNCTIONS
# ========================================

def call_gemini_api(prompt, agent_name="Agent"):
    """Call Gemini API directly"""
    if not gemini_client:
        raise ValueError("Gemini client not initialized")
    
    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    
    if not response or not response.text:
        raise ValueError(f"{agent_name} returned empty response")
    
    return response.text.strip()

def call_groq_api(prompt, agent_name="Agent"):
    """Call Groq API directly"""
    if not groq_client:
        raise ValueError("Groq client not initialized")
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8192
    )
    
    if not response.choices or not response.choices[0].message.content:
        raise ValueError(f"{agent_name} returned empty response")
    
    return response.choices[0].message.content.strip()

def parse_ai_response(response_text, agent_name="Agent"):
    """Parse JSON from AI response, removing markdown if present"""
    # Remove markdown code blocks if present
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    elif response_text.startswith('```'):
        response_text = response_text[3:]
    
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    # Try to extract JSON if there's extra text
    # Look for content between first { and last }
    if not response_text.startswith('{'):
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            response_text = match.group(0)
    
    # Parse JSON
    try:
        result = json.loads(response_text)
        
        # Post-process: unescape newlines in string values if they were escaped
        if 'verilogCode' in result and isinstance(result['verilogCode'], str):
            result['verilogCode'] = result['verilogCode'].replace('\\n', '\n').replace('\\t', '\t')
        if 'testbenchCode' in result and isinstance(result['testbenchCode'], str):
            result['testbenchCode'] = result['testbenchCode'].replace('\\n', '\n').replace('\\t', '\t')
        if 'vivadoTclScript' in result and isinstance(result['vivadoTclScript'], str):
            result['vivadoTclScript'] = result['vivadoTclScript'].replace('\\n', '\n').replace('\\t', '\t')
        
        return result
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        print(f"\n⚠️  JSON Parse Error - attempting to fix...")
        
        # For RTL/Vivado responses, the issue is often unescaped newlines in code
        # Try wrapping the code sections properly
        try:
            # Attempt to manually extract fields if JSON is broken
            project_title_match = re.search(r'"projectTitle"\s*:\s*"([^"]+)"', response_text)
            verilog_code_match = re.search(r'"verilogCode"\s*:\s*"(.+?)"testbenchCode"', response_text, re.DOTALL)
            
            if agent_name == "RTL Engineer" and not verilog_code_match:
                # The JSON is completely broken - ask for simpler output
                raise ValueError(f"{agent_name}: JSON parsing failed completely. The model may have returned code without proper escaping.")
            
            # Save debug info
            print(f"\n⚠️ JSON Parse Error Details:")
            print(f"Error: {str(e)}")
            print(f"Response preview: {response_text[:300]}...")
            raise ValueError(f"{agent_name} did not return valid JSON: {str(e)}\nResponse: {response_text[:500]}")
        except Exception as inner_e:
            print(f"⚠️ Fix attempt failed: {inner_e}")
            raise ValueError(f"{agent_name} did not return valid JSON: {str(e)}\nResponse: {response_text[:500]}")

def call_agent_with_fallback(prompt, agent_name="Agent"):
    """Try Gemini first, fallback to Groq if it fails"""
    last_error = None
    
    # Try Gemini first (only if it hasn't failed before in this request)
    if gemini_client and not get_gemini_failed():
        try:
            print(f"   🔵 Trying Gemini for {agent_name}...")
            response_text = call_gemini_api(prompt, agent_name)
            result = parse_ai_response(response_text, agent_name)
            print(f"   ✅ Gemini succeeded for {agent_name}")
            return result, "Gemini"
        except Exception as e:
            last_error = e
            set_gemini_failed(True)  # Mark Gemini as failed for remaining agents in this request
            print(f"   ⚠️ Gemini failed for {agent_name}: {str(e)[:200]}")
            print(f"   🔒 Gemini marked as failed - will skip for remaining agents")
            if groq_client:
                print(f"   🔄 Falling back to Groq for {agent_name}...")
            else:
                raise ValueError(f"{agent_name} failed and no fallback available: {str(e)}")
    elif get_gemini_failed():
        print(f"   ⏭️ Skipping Gemini for {agent_name} (already failed)")
    
    # Fallback to Groq
    if groq_client:
        try:
            if not gemini_client:
                print(f"   🟢 Using Groq for {agent_name} (Gemini not available)...")
            response_text = call_groq_api(prompt, agent_name)
            print(f"   📝 Groq raw response length: {len(response_text)} chars")
            
            result = parse_ai_response(response_text, agent_name)
            print(f"   ✅ Groq succeeded for {agent_name}")
            return result, "Groq"
        except Exception as e:
            print(f"   ❌ Groq also failed for {agent_name}: {str(e)[:200]}")
            if last_error:
                raise ValueError(f"{agent_name} failed on both Gemini and Groq. Last error: {str(e)}")
            else:
                raise ValueError(f"{agent_name} failed on Groq: {str(e)}")
    
    raise ValueError(f"No AI service available for {agent_name}")

# ========================================
# HARDWARE TOOLS (Simulation & Synthesis)
# ========================================

def run_verilog_simulation(verilog_code, testbench_code):
    """
    Run Iverilog simulation on the provided code.
    Returns (success, output_logs)
    """
    # Check if iverilog is installed
    if shutil.which('iverilog') is None:
        return True, "⚠️ Iverilog not found. Integrated simulation is only available in Docker/Production. (Mock Success)"

    temp_dir = tempfile.mkdtemp()
    try:
        # Write files
        v_path = os.path.join(temp_dir, 'design.v')
        tb_path = os.path.join(temp_dir, 'testbench.v')
        
        with open(v_path, 'w') as f:
            f.write(verilog_code)
        with open(tb_path, 'w') as f:
            f.write(testbench_code)
            
        print(f"   🔬 Running Iverilog simulation...")
        
        # Compile
        sim_out = os.path.join(temp_dir, 'sim.out')
        compile_res = subprocess.run(
            ['iverilog', '-o', sim_out, v_path, tb_path],
            capture_output=True, text=True, timeout=10
        )
        
        if compile_res.returncode != 0:
            return False, f"Compilation Error:\n{compile_res.stderr}"
            
        # Execute
        run_res = subprocess.run(
            ['vvp', sim_out],
            capture_output=True, text=True, timeout=10
        )
        
        return (run_res.returncode == 0), run_res.stdout + run_res.stderr
        
    except subprocess.TimeoutExpired:
        return False, "Simulation timed out (likely infinite loop in RTL)"
    except Exception as e:
        return False, f"Simulation system error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def generate_rtl_schematic(verilog_code):
    """
    Use Yosys and NetlistSVG to generate an RTL schematic SVG.
    """
    # Check if yosys is installed
    if shutil.which('yosys') is None:
        return None, "⚠️ Yosys/NetlistSVG not found in this environment. (Schematic requires Docker)"

    temp_dir = tempfile.mkdtemp()
    try:
        v_path = os.path.join(temp_dir, 'design.v')
        json_path = os.path.join(temp_dir, 'design.json')
        svg_path = os.path.join(temp_dir, 'design.svg')
        
        with open(v_path, 'w') as f:
            f.write(verilog_code)
            
        # 1. Run Yosys synthesis to JSON
        # Detect top module name
        top_match = re.search(r'module\s+(\w+)', verilog_code)
        top_module = top_match.group(1) if top_match else "top"
        
        print(f"   🎨 Synthesizing RTL Schematic for module '{top_module}'...")
        
        yosys_cmd = [
            'yosys', '-p', 
            f'read_verilog {v_path}; prep -top {top_module}; write_json {json_path}'
        ]
        
        yosys_res = subprocess.run(yosys_cmd, capture_output=True, text=True, timeout=15)
        
        if not os.path.exists(json_path):
            return None, f"Yosys synthesis failed: {yosys_res.stderr}"
            
        # 2. Run NetlistSVG
        netlist_res = subprocess.run(
            ['netlistsvg', json_path, '-o', svg_path],
            capture_output=True, text=True, timeout=10
        )
        
        if not os.path.exists(svg_path):
            return None, f"NetlistSVG rendering failed: {netlist_res.stderr}"
            
        with open(svg_path, 'r') as f:
            svg_content = f.read()
            
        return svg_content, None
        
    except Exception as e:
        return None, f"Schematic generation error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ========================================
# API ENDPOINTS
# ========================================

@app.route('/api/status')
def api_status():
    """API status check"""
    return jsonify({
        "message": "AMD Agentic Hardware Co-Design Platform",
        "status": "running",
        "endpoints": ["/generate-agentic-project", "/download-project", "/chat-assistant", "/api/synthesize"]
    })

@app.route('/api/synthesize', methods=['POST'])
def synthesize_rtl():
    """Endpoint to generate RTL schematic from code"""
    try:
        data = request.get_json()
        if not data or 'verilogCode' not in data:
            return jsonify({"error": "verilogCode is required"}), 400
            
        svg_content, error = generate_rtl_schematic(data['verilogCode'])
        
        if error:
            return jsonify({"error": error}), 500
            
        return jsonify({
            "status": "success",
            "svg": svg_content
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat-assistant', methods=['POST'])
def chat_assistant():
    """AI Chat Assistant for design refinement"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_message = data.get('message', '')
        project_data = data.get('projectData', None)
        chat_history = data.get('history', [])
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Build context from project data
        context = ""
        if project_data:
            context = f"""
Current Project Context:
- Title: {project_data.get('architecture', {}).get('projectTitle', 'N/A')}
- Description: {project_data.get('architecture', {}).get('architectureDescription', 'N/A')}
- Modules: {', '.join(project_data.get('architecture', {}).get('moduleList', []))}
"""
        
        # Build conversation history
        history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in chat_history[-5:]  # Last 5 messages for context
        ])
        
        # Create AI prompt
        chat_prompt = f"""You are an expert FPGA and hardware design assistant for AMD/Xilinx platforms.

{context}

Conversation History:
{history_text}

User Question: {user_message}

Provide a helpful, concise response. If the user asks to modify the design, explain what changes would be needed. Keep responses under 200 words unless code examples are requested."""
        
        # Call AI with fallback
        response_text = ""
        if gemini_client:
            try:
                response_text = call_gemini_api(chat_prompt, "Chat Assistant")
            except Exception as e:
                print(f"Chat Gemini failed: {str(e)[:100]}")
                if groq_client:
                    response_text = call_groq_api(chat_prompt, "Chat Assistant")
        elif groq_client:
            response_text = call_groq_api(chat_prompt, "Chat Assistant")
        
        if not response_text:
            raise ValueError("No AI service available")
        
        return jsonify({
            "status": "success",
            "response": response_text
        }), 200
        
    except Exception as e:
        print(f"\n❌ Chat error: {str(e)}\n")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/generate-agentic-project', methods=['GET', 'POST', 'OPTIONS'])
@limiter.limit("5 per minute")
def generate_agentic_project():
    """
    Multi-agent pipeline for hardware design generation
    """
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    # Handle GET method (for debugging)
    if request.method == 'GET':
        return jsonify({
            "error": "This endpoint requires POST method",
            "usage": "Send POST request with JSON body containing 'userPrompt'"
        }), 405
    
    try:
        # gemini_failed is now request-scoped via Flask g (resets automatically per request)
        set_gemini_failed(False)
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_prompt = data.get('userPrompt', '')
        
        if not user_prompt:
            return jsonify({"error": "userPrompt is required"}), 400
        
        print(f"\n{'='*60}")
        print(f"Starting Agentic Pipeline")
        print(f"User Prompt: {user_prompt}")
        print(f"{'='*60}\n")
        
        # Track which models were used
        models_used = []
        
        # ========================================
        # AGENT 1: System Architect
        # ========================================
        print("🕵️‍♂️ Agent 1: System Architect - Starting...")
        architect_prompt = ARCHITECT_PROMPT.format(
            user_prompt=user_prompt
        )
        
        architecture_result, model1 = call_agent_with_fallback(architect_prompt, "System Architect")
        models_used.append(f"Agent 1: {model1}")
        print(f"✅ Agent 1 Complete - Project: {architecture_result.get('projectTitle', 'N/A')}")
        print(f"   Modules: {len(architecture_result.get('moduleList', []))} identified\n")
        
        # ========================================
        # AGENT 2: RTL & Verification Engineer (With Self-Healing)
        # ========================================
        print("👨‍💻 Agent 2: RTL Engineer - Starting...")
        
        rtl_result = None
        sim_success = False
        sim_logs = ""
        retries = 0
        max_retries = 2
        
        while retries <= max_retries:
            # Prepare prompt for RTL generation
            if retries == 0:
                rtl_prompt = RTL_ENGINEER_PROMPT.format(
                    architecture_json=json.dumps(architecture_result, indent=2)
                )
            else:
                print(f"   🔄 Self-Healing: Attempt {retries+1}/{max_retries+1}...")
                rtl_prompt = f"""The previous Verilog code had simulation errors. 
ERROR LOGS:
{sim_logs}

Please fix the code and return the CORRECTED JSON with 'verilogCode' and 'testbenchCode'. 
Ensure syntax is perfect and all modules are defined.
Design Context: {json.dumps(architecture_result, indent=2)}"""

            rtl_result, model2 = call_agent_with_fallback(rtl_prompt, "RTL Engineer")
            
            # Run Simulation (Verify)
            sim_success, sim_logs = run_verilog_simulation(
                rtl_result.get('verilogCode', ''),
                rtl_result.get('testbenchCode', '')
            )
            
            if sim_success:
                print(f"   ✅ Simulation Passed!")
                break
            else:
                print(f"   ❌ Simulation Failed. Logs: {sim_logs[:100]}...")
                retries += 1
        
        models_used.append(f"Agent 2: {model2} ({retries} self-heals)")
        print(f"✅ Agent 2 Complete - Generated Verified Verilog and Testbench")
        print(f"   Verilog Code: {len(rtl_result.get('verilogCode', ''))} characters")
        print(f"   Testbench Code: {len(rtl_result.get('testbenchCode', ''))} characters\n")
        
        # ========================================
        # AGENT 3: AMD Vivado Integrator
        # ========================================
        print("🧐 Agent 3: Vivado Integrator - Starting...")
        vivado_prompt = VIVADO_INTEGRATOR_PROMPT.format(
            project_title=architecture_result.get('projectTitle', 'FPGA_Project'),
            rtl_code=rtl_result.get('verilogCode', '// No code')
        )
        
        vivado_result, model3 = call_agent_with_fallback(vivado_prompt, "Vivado Integrator")
        models_used.append(f"Agent 3: {model3}")
        print(f"✅ Agent 3 Complete - Generated Vivado TCL Script")
        print(f"   TCL Script: {len(vivado_result.get('vivadoTclScript', ''))} characters")
        print(f"   Resource Estimation: {vivado_result.get('resourceEstimation', 'N/A')}\n")
        
        # ========================================
        # Combine All Results
        # ========================================
        print(f"{'='*60}")
        print("✨ Pipeline Complete - Combining Results")
        print(f"Models Used: {', '.join(models_used)}")
        print(f"{'='*60}\n")
        
        return jsonify({
            "status": "success",
            "modelsUsed": models_used,
            "architecture": architecture_result,
            "rtl": {
                "verilogCode": rtl_result.get('verilogCode', ''),
                "testbenchCode": rtl_result.get('testbenchCode', ''),
                "simPassed": sim_success,
                "simulationLogs": sim_logs
            },
            "vivado": vivado_result
        }), 200
    
    except Exception as e:
        print(f"\n❌ Error in pipeline: {str(e)}\n")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/download-project', methods=['POST'])
def download_project():
    """
    Generate and download complete project as ZIP file
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No project data provided"}), 400
        
        # Get project details
        project_title = data.get('architecture', {}).get('projectTitle', 'FPGA_Project') or 'FPGA_Project'
        verilog_code = data.get('rtl', {}).get('verilogCode', '') or ''
        testbench_code = data.get('rtl', {}).get('testbenchCode', '') or ''
        vivado_script = data.get('vivado', {}).get('vivadoTclScript', '') or ''
        architecture_desc = data.get('architecture', {}).get('architectureDescription', '') or ''
        module_list = data.get('architecture', {}).get('module_list', data.get('architecture', {}).get('moduleList', [])) or []
        resource_est = data.get('vivado', {}).get('resourceEstimation', '') or ''
        simulation_logs = data.get('rtl', {}).get('simulationLogs', 'No logs available.') or 'No logs available.'
        
        # Create README content
        readme_content = f"""# {project_title}

## Project Description
{architecture_desc}

## Hardware Modules
{chr(10).join(f'- {module}' for module in module_list)}

## Resource Estimation
{resource_est}

## Project Structure
```
{project_title}/
├── rtl/
│   └── design.v          # Main Verilog RTL code
├── sim/
│   └── testbench.v       # Simulation testbench
├── scripts/
│   └── build.tcl         # Vivado build script
├── constraints/
│   └── basys3.xdc        # Pin constraints for Basys 3
├── logs/
│   └── simulation.log    # Verification results
├── architecture/
│   └── design_doc.md     # Detailed architecture summary
└── README.md             # This file
```

## How to Build

### Using Vivado
1. Open Vivado
2. In Tcl Console: `source scripts/build.tcl`
3. Or use GUI to create project and add files

### Simulation
1. Add `sim/testbench.v` and `rtl/design.v` to your simulator
2. Run simulation
3. Observe waveforms

## Target Hardware
- **Board**: Digilent Basys 3
- **FPGA**: Artix-7 (xc7a35tcpg236-1)

## Generated By
AMD Agentic Hardware Co-Design Platform
AMD Sling Shot Hackathon 2026
"""
        
        # Create Basys 3 constraints file
        constraints_content = """## Clock signal (100MHz)
set_property PACKAGE_PIN W5 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports clk]

## Switches
set_property PACKAGE_PIN V17 [get_ports {sw[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[0]}]
set_property PACKAGE_PIN V16 [get_ports {sw[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[1]}]

## LEDs
set_property PACKAGE_PIN U16 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
set_property PACKAGE_PIN E19 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]

## Buttons
set_property PACKAGE_PIN U18 [get_ports reset]
set_property IOSTANDARD LVCMOS33 [get_ports reset]

## Note: Modify port names to match your design
"""
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files
            zip_file.writestr('rtl/design.v', verilog_code)
            zip_file.writestr('sim/testbench.v', testbench_code)
            zip_file.writestr('scripts/build.tcl', vivado_script)
            zip_file.writestr('constraints/basys3.xdc', constraints_content)
            zip_file.writestr('logs/simulation.log', simulation_logs)
            zip_file.writestr('architecture/design_doc.md', architecture_desc)
            zip_file.writestr('README.md', readme_content)
        
        # Prepare for download
        zip_buffer.seek(0)
        
        # Clean filename
        safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in project_title)
        safe_filename = safe_filename.replace(' ', '_') + '.zip'
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=safe_filename
        )
        
    except Exception as e:
        print(f"\n❌ Error creating ZIP: {str(e)}\n")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AMD Agentic Hardware Co-Design Platform")
    print("="*60)
    print(f"API Key configured: {'✅' if GEMINI_API_KEY else '❌'}")
    
    # Get port from environment variable (Render provides this)
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"Starting Flask server on {host}:{port}")
    print("="*60 + "\n")
    
    app.run(debug=False, host=host, port=port)
