import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import settings

def verify_environment():
    print("=== Jobexa AutoApply Environment Verification ===")
    print(f"Project Name: {settings.PROJECT_NAME}")
    print(f"Database URL: {settings.DATABASE_URL[:25]}...")
    
    gmail_oauth_status = "CONFIGURED" if (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET) else "MISSING (Will use fallback/mock)"
    print(f"Google OAuth Status: {gmail_oauth_status}")
    print(f"Redirect URI: {settings.GOOGLE_OAUTH_REDIRECT_URI}")
    
    nim_status = "CONFIGURED" if settings.NVIDIA_NIM_API_KEY else "NOT CONFIGURED (Will use fallback templates)"
    print(f"NVIDIA NIM API Key: {nim_status}")
    print("=================================================")
    return True

if __name__ == "__main__":
    verify_environment()
