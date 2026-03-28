import subprocess
import os
import sys

# Configuration
PROJECT_ID = "amdhacakthon"
SERVICE_NAME = "amd-hardware-agent"
REGION = "us-central1"

def run_command(cmd, name):
    print(f"\n- Starting: {name}...")
    try:
        # We use shell=True on Windows to ensure gcloud/firebase can be found in PATH
        result = subprocess.run(cmd, shell=True, check=True)
        print(f"OK: {name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nERROR during {name}:")
        print(f"Reason: {str(e)}")
        return False

def main():
    print("="*60)
    print("AMD PRO AUTOMATION: Deploying to Google Cloud & Firebase")
    print("="*60)
    
    # 1. Check for API Keys in Environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key or not groq_key:
        print("\nWARNING: GEMINI_API_KEY or GROQ_API_KEY not found in your terminal environment.")
        print("Please set them first (e.g., $env:GEMINI_API_KEY='your_key')")
        # Continue anyway, gcloud might have them or will fail anyway
    
    # 2. Deploy Backend to Cloud Run
    deploy_cmd = (
        f"gcloud run deploy {SERVICE_NAME} "
        f"--source . "
        f"--project {PROJECT_ID} "
        f"--region {REGION} "
        f"--allow-unauthenticated "
        f"--set-env-vars \"GEMINI_API_KEY={gemini_key},GROQ_API_KEY={groq_key}\""
    )
    
    if not run_command(deploy_cmd, "Google Cloud Run Deployment"):
        sys.exit(1)
        
    # 3. Deploy Frontend to Firebase
    hosting_cmd = f"firebase deploy --only hosting --project {PROJECT_ID}"
    
    if not run_command(hosting_cmd, "Firebase Hosting Deployment"):
        sys.exit(1)
        
    print("\n" + "="*60)
    print("ALL THINGS DEPLOYED SUCCESSFULLY!")
    print(f"Live Site: https://{PROJECT_ID}.web.app")
    print("="*60)

if __name__ == "__main__":
    main()
