import os
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import zipfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# Agent 1: System Architect Prompt Template
ARCHITECT_PROMPT = """You are a Senior Silicon Architect at AMD. Your job is to design the high-level architecture for a user's hardware project idea.

User Request: '{user_prompt}'

You must break this down into logical hardware blocks.
Return ONLY a valid JSON object with the following keys:

projectTitle: Create a professional, concise title for this hardware project based on the description.

architectureDescription: A paragraph explaining the data path, control unit, and how data flows through the system.

moduleList: An array of strings, listing the exact Verilog modules that need to be created (e.g., ['alu_32bit', 'control_unit', 'register_file']). Do NOT use markdown formatting outside the JSON."""

# Agent 2: RTL & Verification Engineer Prompt Template
RTL_ENGINEER_PROMPT = """You are an Expert Verilog RTL Engineer specializing in AMD/Xilinx FPGAs.

The System Architect has provided the following design: {architecture_json}

Your job is to write the actual code. The code MUST be synthesizable on an FPGA. Do not use non-synthesizable constructs in the main module (like initial blocks).
Return ONLY a valid JSON object with the following keys:

verilogCode: The complete, synthesizable Verilog code for the main top-level module and its sub-modules. Include comments.

testbenchCode: A standard Verilog testbench that applies clock, reset, and stimulus to test the top-level module. Include $monitor or $display statements. Do NOT use markdown formatting outside the JSON."""

# Agent 3: AMD Vivado Integrator Prompt Template
VIVADO_INTEGRATOR_PROMPT = """You are an AMD Vivado Toolchain Expert.

We have designed a project titled '{project_title}'.

Your job is to write the tool command language (TCL) script to automate the build process in AMD Vivado, and estimate the hardware cost. Assume the target board is a Basys 3 (Artix-7 FPGA, part number: xc7a35tcpg236-1).
Return ONLY a valid JSON object with the following keys:

vivadoTclScript: A complete Vivado .tcl script that creates a project, adds the Verilog source files, sets the top module, runs synthesis, and runs implementation.

resourceEstimation: A string predicting the approximate hardware cost (e.g., 'Estimated 300 LUTs, 150 Flip-Flops, 0 DSP slices'). Do NOT use markdown formatting outside the JSON."""

def call_gemini_agent(prompt, agent_name="Agent"):
    """Call Gemini API with error handling"""
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError(f"{agent_name} returned empty response")
        
        # Try to extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        result = json.loads(response_text)
        return result
    
    except json.JSONDecodeError as e:
        raise ValueError(f"{agent_name} did not return valid JSON: {str(e)}\nResponse: {response.text[:500]}")
    except Exception as e:
        raise ValueError(f"{agent_name} error: {str(e)}")

@app.route('/')
def home():
    return jsonify({
        "message": "AMD Agentic Hardware Co-Design Platform",
        "status": "running",
        "endpoints": ["/generate-agentic-project"]
    })

@app.route('/generate-agentic-project', methods=['POST'])
def generate_agentic_project():
    """
    Multi-agent pipeline for hardware design generation
    """
    try:
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
        
        # ========================================
        # AGENT 1: System Architect
        # ========================================
        print("🕵️‍♂️ Agent 1: System Architect - Starting...")
        architect_prompt = ARCHITECT_PROMPT.format(
            user_prompt=user_prompt
        )
        
        architecture_result = call_gemini_agent(architect_prompt, "System Architect")
        print(f"✅ Agent 1 Complete - Project: {architecture_result.get('projectTitle', 'N/A')}")
        print(f"   Modules: {len(architecture_result.get('moduleList', []))} identified\n")
        
        # ========================================
        # AGENT 2: RTL & Verification Engineer
        # ========================================
        print("👨‍💻 Agent 2: RTL Engineer - Starting...")
        rtl_prompt = RTL_ENGINEER_PROMPT.format(
            architecture_json=json.dumps(architecture_result, indent=2)
        )
        
        rtl_result = call_gemini_agent(rtl_prompt, "RTL Engineer")
        print(f"✅ Agent 2 Complete - Generated Verilog and Testbench")
        print(f"   Verilog Code: {len(rtl_result.get('verilogCode', ''))} characters")
        print(f"   Testbench Code: {len(rtl_result.get('testbenchCode', ''))} characters\n")
        
        # ========================================
        # AGENT 3: AMD Vivado Integrator
        # ========================================
        print("🧐 Agent 3: Vivado Integrator - Starting...")
        vivado_prompt = VIVADO_INTEGRATOR_PROMPT.format(
            project_title=architecture_result.get('projectTitle', 'FPGA_Project')
        )
        
        vivado_result = call_gemini_agent(vivado_prompt, "Vivado Integrator")
        print(f"✅ Agent 3 Complete - Generated Vivado TCL Script")
        print(f"   TCL Script: {len(vivado_result.get('vivadoTclScript', ''))} characters")
        print(f"   Resource Estimation: {vivado_result.get('resourceEstimation', 'N/A')}\n")
        
        # ========================================
        # Combine All Results
        # ========================================
        print(f"{'='*60}")
        print("✨ Pipeline Complete - Combining Results")
        print(f"{'='*60}\n")
        
        final_response = {
            "status": "success",
            "architecture": {
                "projectTitle": architecture_result.get('projectTitle', ''),
                "architectureDescription": architecture_result.get('architectureDescription', ''),
                "moduleList": architecture_result.get('moduleList', [])
            },
            "rtl": {
                "verilogCode": rtl_result.get('verilogCode', ''),
                "testbenchCode": rtl_result.get('testbenchCode', '')
            },
            "vivado": {
                "vivadoTclScript": vivado_result.get('vivadoTclScript', ''),
                "resourceEstimation": vivado_result.get('resourceEstimation', '')
            }
        }
        
        return jsonify(final_response), 200
    
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
        project_title = data.get('architecture', {}).get('projectTitle', 'FPGA_Project')
        verilog_code = data.get('rtl', {}).get('verilogCode', '')
        testbench_code = data.get('rtl', {}).get('testbenchCode', '')
        vivado_script = data.get('vivado', {}).get('vivadoTclScript', '')
        architecture_desc = data.get('architecture', {}).get('architectureDescription', '')
        module_list = data.get('architecture', {}).get('moduleList', [])
        resource_est = data.get('vivado', {}).get('resourceEstimation', '')
        
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
    print("Starting Flask server on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
