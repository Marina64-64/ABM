"""
Full cycle simulation of a customer using the reCAPTCHA Balancing API.
This script demonstrates submitting a task, polling for the result, 
and verifying the final reCAPTCHA solve.
"""

import requests
import time
import sys

# API Configuration
BASE_URL = "http://localhost:8000"
SITE_KEY = "6Lcc6RssAAAAALlRcHRwdgQm5-SrWLvSc9ceJ17y" # From Task 1 site
PAGE_URL = "https://cd.captchaaiplus.com/recaptcha-v3-2.php"

def simulate_customer_flow():
    print("🚀 Starting Customer Simulation Flow...")
    
    # 1. Submit reCAPTCHA Task
    print(f"\n[Step 1] Submitting task for: {PAGE_URL}")
    payload = {
        "sitekey": SITE_KEY,
        "pageurl": PAGE_URL
    }
    
    try:
        response = requests.post(f"{BASE_URL}/recaptcha/in", json=payload)
        response.raise_for_status()
        data = response.json()
        task_id = data["taskId"]
        print(f"✅ Task Created! ID: {task_id}")
    except Exception as e:
        print(f"❌ Failed to submit task: {e}")
        return

    # 2. Poll for Result
    print(f"\n[Step 2] Polling for result (ID: {task_id})...")
    max_retries = 30
    token = None
    
    for i in range(max_retries):
        try:
            res = requests.get(f"{BASE_URL}/recaptcha/res", params={"taskId": task_id})
            res.raise_for_status()
            res_data = res.json()
            
            status = res_data["status"]
            print(f"   Attempt {i+1}: Status is '{status}'")
            
            if status == "ready":
                token = res_data["token"]
                print(f"✅ Token Received: {token[:50]}...")
                break
            elif status == "error":
                print(f"❌ Task failed with error: {res_data.get('error')}")
                return
                
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            
        time.sleep(2)
    
    if not token:
        print("❌ Polling timed out.")
        return

    # 3. Simulate using the token (Verification)
    print("\n[Step 3] Simulating token injection/verification...")
    # On the target site, they POST the token back to verify
    verify_payload = {
        "token": token,
        "action": "submit"
    }
    
    try:
        verify_res = requests.post(PAGE_URL, data=verify_payload)
        verify_res.raise_for_status()
        result_json = verify_res.json()
        print(f"✅ Verification Result from Site: {result_json}")
        
        if result_json.get("success"):
            print(f"🎉 SUCCESS! Score achieved: {result_json.get('score')}")
        else:
            print("❌ Token verification failed on the target site.")
            
    except Exception as e:
        print(f"⚠️ Could not verify token on live site: {e}")

if __name__ == "__main__":
    simulate_customer_flow()
