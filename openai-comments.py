from instagrapi import Client
import os
import random
import sys
import time
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

if len(sys.argv) < 4:
    print("Usage: python3 openai-comments.py <username> <password> <hashtag>")
    sys.exit(1)

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
hashtag = sys.argv[3]

load_dotenv('config.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
    print("❌ Error: Please set OPENAI_API_KEY in config.env")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

print(f"📸 Using credentials for: {USERNAME}")

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
    
    # Check limits (more conservative for comments)
    if len(limits["comments"]) >= 15:  # Reduced from 20 to 15 comments per hour
        print("⚠️ Rate limit reached for comments (15/hour)")
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
        
        # Test if session is actually valid by making a simple API call
        try:
            test_user = cl.user_info_by_username("instagram")
            print("✅ Login successful with existing session!")
            login_success = True
        except Exception as test_error:
            print(f"⚠️ Session appears expired: {test_error}")
            print("🔄 Attempting fresh login...")
            login_success = False
            
    except Exception as e:
        print(f"⚠️ Session login failed: {e}")
        print("🔄 Attempting fresh login...")
        login_success = False

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

def generate_comment_with_chatgpt(post_content, hashtag):
    try:
        # Analyze post content to generate more contextual comments
        content_analysis = analyze_post_content(post_content)
        
        # More sophisticated prompt system based on content type
        if content_analysis['type'] == 'food':
            prompts = [
                f"""You're a restaurant owner who loves food and wants to build genuine connections on social media. Comment on this food post naturally in Italian:

Post: {post_content}
Hashtag: #{hashtag}
Food type: {content_analysis.get('food_type', 'general')}

Write like you're genuinely interested in the food as a fellow food lover. Maybe ask about the recipe, mention you want to try it, or just say it looks good. Be specific about what you see. Keep it under 100 characters and sound natural. IMPORTANT: Write the comment in Italian language only. Don't mention your restaurant - just be a food enthusiast.

Comment:""",
                
                f"""Comment on this food post as a restaurant owner who appreciates good food in Italian:

Post: {post_content}
Hashtag: #{hashtag}

Write a casual, specific comment about the food. Maybe mention a detail you noticed, ask a question, or just say it looks delicious. Sound like a real person who knows food, not a bot. IMPORTANT: Write the comment in Italian language only. Don't promote anything - just show genuine food appreciation.

Comment:"""
            ]
        elif content_analysis['type'] == 'cooking':
            prompts = [
                f"""You're a restaurant owner commenting on a cooking post. Be genuinely interested in Italian:

Post: {post_content}
Hashtag: #{hashtag}

Write like you're impressed by the cooking skills or want to learn more. Ask about the technique, mention it looks professional, or just say it looks amazing. Be specific and natural. IMPORTANT: Write the comment in Italian language only. Show your passion for cooking without promoting your business.

Comment:"""
            ]
        else:
            prompts = [
                f"""Comment on this Instagram post naturally in Italian as a restaurant owner:

Post: {post_content}
Hashtag: #{hashtag}

Write like a real person would comment. Be specific about what you see, ask a question, or just say something nice. Keep it casual and under 100 characters. IMPORTANT: Write the comment in Italian language only. Don't be promotional - just be genuinely interested in the content.

Comment:"""
            ]
        
        prompt = random.choice(prompts)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a restaurant owner who wants to build genuine connections on social media. You comment on food and cooking posts to show your passion for food and engage with the community. Write natural, specific comments that reference the actual content. Don't be generic, promotional, or mention your restaurant. Sound like a human who genuinely loves food and cooking. IMPORTANT: All comments MUST be written in Italian language only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.9  # Higher temperature for more natural variation
        )
        
        comment = response.choices[0].message.content.strip()
        
        # Add human-like variations and typos occasionally
        if random.random() < 0.25:  # 25% chance for human touches
            human_modifications = [
                lambda x: x.replace("looks", "looks like"),
                lambda x: x.replace("amazing", "amaz"),
                lambda x: x.replace("delicious", "delish"),
                lambda x: x + " tbh",
                lambda x: x.replace("!", "!!"),
                lambda x: x.replace("love", "luv"),
                lambda x: x.replace("really", "rly"),
                lambda x: x.replace("you", "u"),
                lambda x: x.replace("are", "r"),
                lambda x: x + " tho",
                lambda x: x.replace("good", "gd"),
                lambda x: x.replace("great", "gr8"),
                lambda x: x.replace("that", "dat"),
                lambda x: x.replace("with", "w/"),
                lambda x: x.replace("about", "abt"),
            ]
            comment = random.choice(human_modifications)(comment)
        
        # Sometimes add emojis naturally (not excessive)
        if random.random() < 0.3 and len(comment) < 80:
            natural_emojis = ["😋", "👌", "🔥", "💯", "😍", "🤤"]
            if not any(emoji in comment for emoji in natural_emojis):
                comment += f" {random.choice(natural_emojis)}"
        
        return comment
    except Exception as e:
        print(f"⚠️  ChatGPT API error: {e}")
        # More natural fallback comments in Italian
        fallbacks = [
            f"sembra buono",
            f"yum",
            f"delizioso",
            f"bel post",
            f"sembra ottimo",
            f"roba buona",
            f"sembra gustoso",
            f"yummy",
            f"sembra fantastico",
            f"mi piace questo"
        ]
        return random.choice(fallbacks)

def analyze_post_content(content):
    """Analyze post content to generate more contextual comments"""
    content_lower = content.lower()
    
    # Food-related keywords
    food_keywords = ['pizza', 'pasta', 'burger', 'sushi', 'cake', 'bread', 'cheese', 'meat', 'fish', 'chicken', 'beef', 'pork', 'salad', 'soup', 'dessert', 'ice cream', 'chocolate', 'coffee', 'tea', 'wine', 'beer', 'cocktail']
    
    # Cooking-related keywords
    cooking_keywords = ['recipe', 'cook', 'bake', 'grill', 'fry', 'roast', 'steam', 'sauté', 'homemade', 'kitchen', 'chef', 'cooking', 'baking', 'prep', 'ingredients', 'method', 'technique']
    
    # Avoid commenting on posts with these keywords (inappropriate or spam)
    avoid_keywords = ['buy now', 'click link', 'dm me', 'message me', 'follow me', 'like for like', 'follow for follow', 'sponsored', 'ad', 'promotion', 'sale', 'discount', 'limited time', 'offer']
    
    # Check for inappropriate content
    for keyword in avoid_keywords:
        if keyword in content_lower:
            return {'type': 'avoid', 'reason': f'Contains {keyword}', 'confidence': 0}
    
    # Determine content type
    food_matches = sum(1 for keyword in food_keywords if keyword in content_lower)
    cooking_matches = sum(1 for keyword in cooking_keywords if keyword in content_lower)
    
    if cooking_matches > 0:
        return {'type': 'cooking', 'confidence': cooking_matches}
    elif food_matches > 0:
        return {'type': 'food', 'food_type': 'general', 'confidence': food_matches}
    else:
        return {'type': 'general', 'confidence': 0}

def is_safe_to_comment(media):
    """Check if it's safe to comment on this post"""
    try:
        caption = media.caption_text or ""
        
        # Skip posts that are too old (more than 7 days)
        # Skip posts with very short captions (likely low quality)
        if len(caption) < 10:
            return False, "Caption too short"
        
        # Skip posts with excessive hashtags (spam-like)
        hashtag_count = caption.count('#')
        if hashtag_count > 20:
            return False, "Too many hashtags"
        
        # Skip posts with excessive mentions
        mention_count = caption.count('@')
        if mention_count > 5:
            return False, "Too many mentions"
        
        return True, "Safe to comment"
    except:
        return False, "Error analyzing post"

# Require hashtag for comments
if not hashtag:
    print("Hashtag is required for hashtag-only search.")
    sys.exit(1)

# Add delay before API calls
safe_delay(3, 7)

# Fetch medias with retries
max_retries = 3
for attempt in range(max_retries):
    try:
        print(f"📥 Fetching posts (attempt {attempt + 1}/{max_retries})")
        medias = cl.hashtag_medias_recent(hashtag, amount=30)
        break
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error fetching medias (attempt {attempt + 1}): {e}")
        
        # Handle specific Instagram errors
        if "login_required" in error_msg:
            print("❌ Instagram requires fresh login. Deleting session file...")
            session_file = f"session_{USERNAME}.json"
            if os.path.exists(session_file):
                os.remove(session_file)
                print("✅ Session file deleted. Please run the script again for fresh login.")
            sys.exit(1)
        elif "rate" in error_msg or "limit" in error_msg:
            print("⚠️ Rate limit detected. Waiting longer...")
            safe_delay(30, 60)  # Much longer delay for rate limits
        elif attempt < max_retries - 1:
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

print(f"Found {len(filtered_medias)} posts for #{hashtag}, checking for posts you haven't commented on...")

posts_to_comment = []
for media in filtered_medias:
    try:
        safe_delay(2, 5)  # Delay between API calls
        comments = cl.media_comments(media.id)
        already_commented = any(comment.user.username == USERNAME for comment in comments)
        if not already_commented:
            posts_to_comment.append(media)
        else:
            print(f"Skipping post {media.code} - already commented")
    except Exception as e:
        print(f"Could not check comments for post {media.code}: {e}")
        posts_to_comment.append(media)
        safe_delay(5, 10)  # Longer delay on error

if not posts_to_comment:
    print("No posts found that you haven't already commented on.")
    sys.exit(0)

print(f"Found {len(posts_to_comment)} posts you haven't commented on")

# Limit to max 2 comments for safety (more conservative than likes)
# Reduce by 20% - now 1-2 comments with 20% chance to skip entirely
if random.random() < 0.2:  # 20% chance to skip commenting entirely
    print("🎲 Randomly skipping comment generation (20% reduction)")
    sys.exit(0)

# More sophisticated selection based on content quality
high_quality_posts = []
for media in posts_to_comment:
    try:
        # Analyze post quality
        caption_length = len(media.caption_text or "")
        has_hashtags = '#' in (media.caption_text or "")
        has_mentions = '@' in (media.caption_text or "")
        
        # Prefer posts with longer captions and hashtags (more engagement)
        quality_score = 0
        if caption_length > 50:
            quality_score += 2
        if has_hashtags:
            quality_score += 1
        if has_mentions:
            quality_score += 1
        
        if quality_score >= 2:
            high_quality_posts.append(media)
    except:
        pass

# Use high quality posts if available, otherwise use all posts
posts_to_use = high_quality_posts if high_quality_posts else posts_to_comment
num_to_comment = min(random.randint(1, 2), len(posts_to_use))  # 1-2 comments instead of always 2
selected_medias = random.sample(posts_to_use, num_to_comment)

success_count = 0
for i, media in enumerate(selected_medias, 1):
    try:
        # More sophisticated timing - vary delays based on post type
        base_delay = random.uniform(15, 30)  # Longer base delay
        
        # Add extra delay for posts with more engagement (more human-like)
        caption_length = len(media.caption_text or "")
        if caption_length > 100:
            base_delay += random.uniform(5, 15)  # Extra time to "read" longer posts
        
        safe_delay(base_delay, base_delay + 10)
        
        post_content = ""
        if media.caption_text:
            post_content = media.caption_text
        else:
            post_content = f"Post about #{hashtag}"
        
        # Analyze content for better comment generation
        content_analysis = analyze_post_content(post_content)
        
        # Skip posts that are not safe to comment on
        is_safe, reason = is_safe_to_comment(media)
        if not is_safe:
            print(f"⚠️ Skipping post {i}: {reason}")
            continue
        
        # Skip posts with inappropriate content
        if content_analysis['type'] == 'avoid':
            print(f"⚠️ Skipping post {i}: {content_analysis['reason']}")
            continue
        
        comment = generate_comment_with_chatgpt(post_content, hashtag)
        
        # Sometimes add human-like typos or casual language
        if random.random() < 0.15:  # 15% chance for human touches
            human_modifications = [
                lambda x: x.replace("looks", "looks like"),
                lambda x: x.replace("amazing", "amaz"),
                lambda x: x.replace("delicious", "delish"),
                lambda x: x + " tbh",
                lambda x: x.replace("!", "!!"),
                lambda x: x.replace("love", "luv"),
                lambda x: x.replace("really", "rly"),
                lambda x: x.replace("you", "u"),
                lambda x: x.replace("are", "r"),
                lambda x: x + " tho",
                lambda x: x.replace("good", "gd"),
                lambda x: x.replace("great", "gr8"),
                lambda x: x.replace("that", "dat"),
                lambda x: x.replace("with", "w/"),
                lambda x: x.replace("about", "abt"),
                lambda x: x.replace("because", "bc"),
                lambda x: x.replace("through", "thru"),
            ]
            comment = random.choice(human_modifications)(comment)
        
        # Additional delay before posting comment (more human-like)
        pre_comment_delay = random.uniform(8, 20)  # Longer delay to seem more thoughtful
        safe_delay(pre_comment_delay, pre_comment_delay + 5)
        
        cl.media_comment(media.id, comment)
        print(f"💬 Commented on post {i}: https://www.instagram.com/p/{media.code}/")
        print(f"   Post content: {post_content[:100]}{'...' if len(post_content) > 100 else ''}")
        print(f"   Content type: {content_analysis['type']}")
        print(f"   AI Comment: {comment}")
        print("-" * 50)
        
        # Update rate limits
        update_rate_limits("comments")
        success_count += 1
        
        # Additional delay after successful comment (more human-like)
        post_comment_delay = random.uniform(12, 25)  # Longer delay to seem more natural
        safe_delay(post_comment_delay, post_comment_delay + 8)
        
    except Exception as e:
        print(f"⚠️ Failed to comment on post {i}: {e}")
        safe_delay(20, 40)  # Much longer delay on comment error

print(f"✅ Successfully commented on {success_count}/{len(selected_medias)} posts")

# Final delay before exit
safe_delay(2, 5) 