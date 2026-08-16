from instagrapi import Client
import os
import random
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Accept hashtag as optional argument
if len(sys.argv) < 3:
    print("Usage: python3 openai-instagram.py <username> <password> [<hashtag>]")
    sys.exit(1)

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
hashtag = sys.argv[3] if len(sys.argv) > 3 else None

print(f"📸 Using credentials for: {USERNAME}")
print(f"🔍 Searching posts for #{hashtag}...")

def get_proxies():
    proxies = []
    try:
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except Exception:
        pass
    if not proxies:
        proxies = [os.getenv('TINYPROXY_HTTP', 'http://127.0.0.1:8888')]
    return proxies

def get_user_agents():
    """Rotate user agents for better stealth - Updated to latest 2024/2025 versions"""
    user_agents = [
        "Instagram 387.1.0.34.85 Android",
        "Instagram 385.0.0.47.74 Android", 
        "Instagram 384.0.0.46.83 Android",
        "Instagram 383.1.0.48.78 Android",
        "Instagram 382.0.0.49.84 Android"
    ]
    return random.choice(user_agents)

def get_device_settings():
    """Generate random device settings for better stealth - Updated to current devices"""
    devices = [
        {
            "manufacturer": "samsung",
            "model": "SM-S918B",  # Galaxy S23 Ultra
            "android_version": 34,
            "android_release": "14"
        },
        {
            "manufacturer": "xiaomi", 
            "model": "2312DRA50G",  # Redmi Note 13 Pro 5G
            "android_version": 34,
            "android_release": "14"
        },
        {
            "manufacturer": "realme",
            "model": "RMX3842",  # Realme device
            "android_version": 35,
            "android_release": "15"
        },
        {
            "manufacturer": "oppo",
            "model": "CPH2665",
            "android_version": 35,
            "android_release": "15"
        },
        {
            "manufacturer": "vivo",
            "model": "V2420",
            "android_version": 34,
            "android_release": "14"
        }
    ]
    return random.choice(devices)

def load_session(username):
    """Load existing session if available"""
    session_file = f"session_{username}.json"
    if os.path.exists(session_file):
        try:
            print(f"📁 Loading existing session for {username}")
            return session_file
        except Exception as e:
            print(f"⚠️ Failed to load session: {e}")
    return None

def save_session(cl, username):
    """Save session for future use"""
    try:
        session_file = f"session_{username}.json"
        cl.dump_settings(session_file)
        print(f"💾 Session saved for {username}")
    except Exception as e:
        print(f"⚠️ Failed to save session: {e}")

def safe_delay(min_seconds=2, max_seconds=8):
    """Add random delay between actions"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏳ Waiting {delay:.1f} seconds...")
    time.sleep(delay)

def check_rate_limits():
    """Simple rate limiting check"""
    rate_file = "rate_limits.json"
    current_time = time.time()
    
    # Load existing limits
    limits = {"likes": [], "comments": []}
    if os.path.exists(rate_file):
        try:
            with open(rate_file, 'r') as f:
                limits = json.load(f)
        except:
            pass
    
    # Clean old entries (older than 1 hour)
    hour_ago = current_time - 3600
    limits["likes"] = [t for t in limits["likes"] if t > hour_ago]
    limits["comments"] = [t for t in limits["comments"] if t > hour_ago]
    
    # Check limits
    if len(limits["likes"]) >= 50:  # Max 50 likes per hour
        print("⚠️ Rate limit reached for likes (50/hour)")
        return False
    
    return True

def update_rate_limits(action_type):
    """Update rate limit tracking"""
    rate_file = "rate_limits.json"
    current_time = time.time()
    
    # Load existing limits
    limits = {"likes": [], "comments": []}
    if os.path.exists(rate_file):
        try:
            with open(rate_file, 'r') as f:
                limits = json.load(f)
        except:
            pass
    
    # Add current action
    if action_type in limits:
        limits[action_type].append(current_time)
    
    # Save limits
    try:
        with open(rate_file, 'w') as f:
            json.dump(limits, f)
    except Exception as e:
        print(f"⚠️ Failed to update rate limits: {e}")

# Check rate limits before starting
if not check_rate_limits():
    print("❌ Rate limit exceeded. Please wait before trying again.")
    sys.exit(1)

# Initialize client with best practices
cl = Client()

# Set device settings for better stealth
device = get_device_settings()
cl.set_device(device)

# Set user agent
cl.set_user_agent(get_user_agents())

# Set proxy and login with session management
proxies = get_proxies()
login_success = False

# Try to load existing session first
session_file = load_session(USERNAME)
if session_file:
    try:
        cl.load_settings(session_file)
        cl.login(USERNAME, PASSWORD)
        print("✅ Login successful with existing session!")
        login_success = True
    except Exception as e:
        print(f"⚠️ Session login failed: {e}")
        print("🔄 Attempting fresh login...")

# If session login failed, try fresh login with proxies
if not login_success:
    for proxy in proxies:
        try:
            cl.set_proxy(proxy)
            print(f'🌐 Trying HTTP proxy: {proxy}')
            safe_delay(1, 3)  # Delay before login attempt
            cl.login(USERNAME, PASSWORD)
            print("✅ Login successful!")
            save_session(cl, USERNAME)
            login_success = True
            break
        except Exception as e:
            print(f"❌ Login failed with proxy {proxy}: {e}")
            safe_delay(2, 5)  # Delay before next proxy

if not login_success:
    print("❌ Login failed with all proxies.")
    sys.exit(1)

# Require hashtag again
if not hashtag:
    print("Hashtag is required for hashtag-only search.")
    sys.exit(1)

# Add delay before API calls
safe_delay(3, 7)

# Fetch recent medias by hashtag with retries
max_retries = 3
for attempt in range(max_retries):
    try:
        print(f"📥 Fetching posts (attempt {attempt + 1}/{max_retries})")
        medias = cl.hashtag_medias_recent(hashtag, amount=30)
        break
    except Exception as e:
        print(f"Error fetching medias (attempt {attempt + 1}): {e}")
        if attempt < max_retries - 1:
            safe_delay(10, 20)  # Longer delay on error
        else:
            medias = []

filtered_medias = []
for m in medias:
    try:
        _ = m.pk
        filtered_medias.append(m)
    except Exception as e:
        print(f"Skipping invalid media: {e}")

if not filtered_medias:
    print(f"No posts found for #{hashtag}.")
    sys.exit(0)

print(f"Found {len(filtered_medias)} posts for #{hashtag}, randomly selecting up to 3 to like...")

# Limit to 3 posts for safety
selected_medias = random.sample(filtered_medias, min(3, len(filtered_medias)))

# Like posts with proper delays and error handling
success_count = 0
for i, media in enumerate(selected_medias, 1):
    try:
        safe_delay(5, 15)  # Random delay between likes (5-15 seconds)
        
        cl.media_like(media.id)
        print(f"❤️ Liked post {i}: https://www.instagram.com/p/{media.code}/")
        
        # Update rate limits
        update_rate_limits("likes")
        success_count += 1
        
        # Additional delay after successful like
        safe_delay(3, 8)
        
    except Exception as e:
        print(f"⚠️ Failed to like post {i}: {e}")
        safe_delay(10, 20)  # Longer delay on error

print(f"✅ Successfully liked {success_count}/{len(selected_medias)} posts")

# Final delay before exit
safe_delay(2, 5)
