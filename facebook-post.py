from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import pickle
import os
import sys

# Default values (will be overridden by command line arguments)
FB_EMAIL = ""
FB_PASSWORD = ""
IMAGE_PATH = "your_image.jpg"
TEXT = "Posting to personal Facebook profile using Selenium"

COOKIE_FILE = "fb_cookies.pkl"

def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def safe_click(driver, element, description="element"):
    """Safely click an element with multiple strategies"""
    try:
        print(f"Attempting to click {description}")
        # Try regular click first
        element.click()
        print(f"Successfully clicked {description}")
        return True
    except ElementClickInterceptedException:
        print(f"Click intercepted for {description}, trying scroll and click...")
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            element.click()
            print(f"Successfully clicked {description} after scroll")
            return True
        except ElementClickInterceptedException:
            print(f"Still intercepted for {description}, using JavaScript click...")
            driver.execute_script("arguments[0].click();", element)
            print(f"Successfully clicked {description} with JavaScript")
            return True
    except Exception as e:
        print(f"Error clicking {description}: {e}")
        return False

def handle_popups(driver):
    """Handle common Facebook popups and overlays"""
    try:
        # Wait a moment for popups to appear
        time.sleep(2)
        
        # Close buttons with various selectors
        popup_selectors = [
            "//div[@aria-label='Close' and @role='button']",
            "//div[@aria-label='Close']",
            "//button[@aria-label='Close']",
            "//div[contains(@class, 'close') and @role='button']",
            "//div[@data-testid='cookie-policy-manage-dialog-decline-button']",
            "//button[contains(text(), 'Decline')]",
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Maybe Later')]",
            "//div[contains(text(), 'Allow Essential and Optional Cookies')]/..//button[contains(text(), 'Decline')]"
        ]
        
        for selector in popup_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        safe_click(driver, element, f"popup element with selector {selector}")
                        time.sleep(1)
            except:
                continue
                
        # Handle cookie banners specifically
        try:
            cookie_decline = driver.find_element(By.XPATH, "//button[@data-cookiebanner='decline_button']")
            if cookie_decline.is_displayed():
                safe_click(driver, cookie_decline, "cookie decline button")
        except:
            pass
            
    except Exception as e:
        print(f"Error handling popups: {e}")

def login(driver):
    """Login to Facebook with improved error handling"""
    print("Starting login process...")
    driver.get("https://www.facebook.com/")
    wait = WebDriverWait(driver, 15)
    
    try:
        # Handle initial popups and cookie banners
        print("Waiting for page to load...")
        time.sleep(5)
        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)
        
        print("Handling initial popups...")
        handle_popups(driver)
        
        # Wait for and fill email field using multiple selectors
        print("Looking for email field...")
        email_selectors = [
            (By.CSS_SELECTOR, "[data-testid='royal-email']"),
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]
        
        email_input = None
        for selector_type, selector_value in email_selectors:
            try:
                print(f"Trying email selector: {selector_type} = {selector_value}")
                email_input = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                print(f"✓ Found email field with {selector_type}: {selector_value}")
                break
            except TimeoutException:
                print(f"✗ Failed with {selector_type}: {selector_value}")
                continue
        
        if email_input is None:
            print("ERROR: Could not find email input field")
            print("Available input elements:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for i, inp in enumerate(inputs):
                print(f"  Input {i}: type='{inp.get_attribute('type')}', name='{inp.get_attribute('name')}', id='{inp.get_attribute('id')}', placeholder='{inp.get_attribute('placeholder')}'")
            raise TimeoutException("Could not find email input field")
        
        # Clear and enter email
        print(f"Entering email: {FB_EMAIL}")
        email_input.clear()
        email_input.send_keys(FB_EMAIL)
        entered_email = email_input.get_attribute('value')
        print(f"Email entered successfully: {entered_email}")
        
        # Wait for and fill password field
        print("Looking for password field...")
        password_selectors = [
            (By.CSS_SELECTOR, "[data-testid='royal-pass']"),
            (By.ID, "pass"),
            (By.NAME, "pass"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        
        pass_input = None
        for selector_type, selector_value in password_selectors:
            try:
                print(f"Trying password selector: {selector_type} = {selector_value}")
                pass_input = driver.find_element(selector_type, selector_value)
                print(f"✓ Found password field with {selector_type}: {selector_value}")
                break
            except NoSuchElementException:
                print(f"✗ Failed with {selector_type}: {selector_value}")
                continue
        
        if pass_input is None:
            print("ERROR: Could not find password input field")
            raise TimeoutException("Could not find password input field")
        
        # Clear and enter password
        print("Entering password...")
        pass_input.clear()
        pass_input.send_keys(FB_PASSWORD)
        print("Password entered successfully")
        
        # Handle any popups that might have appeared
        print("Handling popups before login...")
        handle_popups(driver)
        
        # Find and click login button
        print("Looking for login button...")
        login_selectors = [
            (By.CSS_SELECTOR, "[data-testid='royal-login-button']"),
            (By.NAME, "login"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Log In') or contains(text(), 'Log in')]"),
            (By.CSS_SELECTOR, "button[value='1']"),
        ]
        
        login_button = None
        for selector_type, selector_value in login_selectors:
            try:
                print(f"Trying login button selector: {selector_type} = {selector_value}")
                login_button = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                print(f"✓ Found login button with {selector_type}: {selector_value}")
                break
            except TimeoutException:
                print(f"✗ Failed with {selector_type}: {selector_value}")
                continue
        
        if login_button is None:
            print("ERROR: Could not find login button")
            print("Available buttons:")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(buttons):
                print(f"  Button {i}: text='{btn.text}', type='{btn.get_attribute('type')}', name='{btn.get_attribute('name')}', value='{btn.get_attribute('value')}'")
            raise TimeoutException("Could not find login button")
        
        # Click login button
        print("Clicking login button...")
        if safe_click(driver, login_button, "login button"):
            print("✓ Login button clicked successfully")
        else:
            print("✗ Failed to click login button, trying Enter key...")
            # Try pressing Enter on password field as alternative
            pass_input.send_keys(Keys.RETURN)
            print("✓ Pressed Enter on password field")
        
        # Wait for redirection and handle any additional popups
        print("Waiting for login redirect...")
        time.sleep(8)  # Give more time for login
        
        print(f"Current URL after login attempt: {driver.current_url}")
        print(f"Page title after login: {driver.title}")
        
        handle_popups(driver)
        
        # Check if login was successful
        current_url = driver.current_url
        if "facebook.com" in current_url and "/login" not in current_url:
            print("✓ Login appears successful!")
            
            # Handle 2FA if present
            if "two_step_verification" in current_url or "two_factor" in current_url:
                print("⚠ Two-factor authentication detected!")
                print("Please complete 2FA manually in the browser window...")
                print("Waiting 30 seconds for manual 2FA completion...")
                time.sleep(30)
                
                # Check if still on 2FA page
                if "two_step_verification" in driver.current_url or "two_factor" in driver.current_url:
                    print("Still on 2FA page. Please complete it and press Enter to continue...")
                    input("Press Enter when 2FA is complete...")
                
                # Navigate to home page after 2FA
                print("Navigating to Facebook home page...")
                driver.get("https://www.facebook.com/")
                time.sleep(5)
            
            # Save cookies for future use
            with open(COOKIE_FILE, "wb") as f:
                pickle.dump(driver.get_cookies(), f)
                print("✓ Cookies saved successfully")
        else:
            print(f"⚠ Login might have failed. Current URL: {current_url}")
            # Check for error messages
            error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'incorrect') or contains(text(), 'error') or contains(text(), 'wrong')]")
            if error_elements:
                print("Found potential error messages:")
                for elem in error_elements:
                    if elem.is_displayed():
                        print(f"  - {elem.text}")
            
    except TimeoutException as e:
        print(f"✗ Timeout during login: {e}")
        print(f"Current URL: {driver.current_url}")
        print("Page source (first 1000 chars):")
        print(driver.page_source[:1000])
        raise
    except Exception as e:
        print(f"✗ Error during login: {e}")
        import traceback
        traceback.print_exc()
        raise

def load_cookies(driver):
    """Load saved cookies to skip login"""
    print("Loading saved cookies...")
    driver.get("https://www.facebook.com/")
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Could not add cookie: {e}")
            driver.refresh()
            time.sleep(3)
            print("Cookies loaded successfully")
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
    return True

def post_to_profile(driver):
    """Post content to Facebook profile with improved selectors"""
    print("Starting post creation...")
    driver.get("https://www.facebook.com/")
    wait = WebDriverWait(driver, 20)
    
    try:
        # Handle popups first
        print("Handling popups before posting...")
        handle_popups(driver)
        time.sleep(3)
        
        # Look for post creation area with multiple strategies
        print("Looking for post creation area...")
        post_area_selectors = [
            # Modern Facebook selectors (2024)
            "//div[@role='button' and contains(@aria-label, 'Create a post')]",
            "//div[@role='button']//span[contains(text(), \"What's on your mind\")]",
            "//div[@role='button']//span[contains(text(), 'What are you thinking about')]",
            "//div[contains(@aria-label, 'Write a post')]",
            "//div[contains(@data-testid, 'status-attachment-mentions-input')]",
            "//div[@role='button'][contains(@aria-describedby, 'placeholder')]",
            
            # Classic selectors
            "//div[@role='button'][contains(@aria-label, 'Create')]",
            "//div[contains(text(), 'Write something')]",
            "//span[contains(text(), 'on your mind')]",
            "//textarea[@placeholder]",
            
            # Generic fallbacks
            "//div[@role='button' and contains(@class, 'post') and contains(@class, 'composer')]",
            "//div[@contenteditable='true']",
        ]
        
        post_area = None
        for selector in post_area_selectors:
            try:
                print(f"Trying post area selector: {selector}")
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # Additional check - make sure it's not too small (likely not the main post area)
                        size = element.size
                        if size['height'] > 10 and size['width'] > 100:
                            post_area = element
                            print(f"✓ Found suitable post area with selector: {selector}")
                            print(f"  Element size: {size}")
                            break
                if post_area:
                    break
            except Exception as e:
                print(f"✗ Error with selector {selector}: {e}")
                continue
        
        if post_area is None:
            print("Could not find post creation area with standard selectors")
            print("Trying to find any clickable div that might be the post area...")
            
            # More aggressive fallback searches
            fallback_selectors = [
                "//div[@role='button' and contains(@style, 'cursor')]",
                "//div[@role='button'][contains(@class, 'composer') or contains(@class, 'post')]",
                "//div[contains(@class, 'story') and contains(@class, 'composer')]",
                "//div[contains(@placeholder, 'mind') or contains(@placeholder, 'thinking')]",
                "//div[@role='button'][position()=1]",  # Sometimes the first button is the post area
            ]
            
            for selector in fallback_selectors:
                try:
                    print(f"Trying fallback selector: {selector}")
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        post_area = elements[0]
                        print(f"✓ Found potential post area with fallback: {selector}")
                        break
                except:
                    continue
        
        if post_area is None:
            print("Could not find any post creation area")
            print("Current page source (first 2000 chars):")
            print(driver.page_source[:2000])
            
            # Last resort - print all buttons and divs with role='button' for debugging
            print("\nAll clickable elements for debugging:")
            buttons = driver.find_elements(By.XPATH, "//div[@role='button'] | //button")
            for i, btn in enumerate(buttons[:10]):  # Limit to first 10
                try:
                    text = btn.text[:50] if btn.text else "No text"
                    aria_label = btn.get_attribute('aria-label') or "No aria-label"
                    print(f"  {i}: text='{text}', aria-label='{aria_label}'")
                except:
                    pass
            
            raise TimeoutException("No post creation area found")
        
        # Click on post area
        if safe_click(driver, post_area, "post creation area"):
            print("Successfully clicked post creation area")
        else:
            raise Exception("Failed to click post creation area")
        
        # Wait for modal/composer to open
        time.sleep(3)
        handle_popups(driver)
        
        # Look for text input area
        print("Looking for text input area...")
        text_selectors = [
            "//div[@role='textbox']",
            "//div[@contenteditable='true']",
            "//textarea",
            "//div[@data-testid='status-attachment-mentions-input']",
            "//div[contains(@aria-label, 'What')]",
            "//div[@aria-describedby][@contenteditable='true']",
        ]
        
        text_area = None
        for selector in text_selectors:
            try:
                print(f"Trying text area selector: {selector}")
                elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text_area = element
                        print(f"Found text area with selector: {selector}")
                        break
                if text_area:
                    break
            except TimeoutException:
                continue
        
        if text_area is None:
            print("Could not find text input area")
            raise TimeoutException("No text input area found")
        
        # Enter text
        print("Entering text...")
        driver.execute_script("arguments[0].focus();", text_area)
        time.sleep(1)
        
        # Clear and enter text using multiple methods
        try:
            text_area.clear()
        except:
            pass
        
        try:
            text_area.send_keys(Keys.CONTROL + "a")  # Select all
            text_area.send_keys(Keys.DELETE)  # Delete
        except:
            pass
        
        text_area.send_keys(TEXT)
        print(f"Text entered: {TEXT}")
        time.sleep(2)
        
        # Handle image upload if file exists
        if IMAGE_PATH and os.path.exists(IMAGE_PATH):
            print("Looking for image upload...")
            try:
                # Look for file input
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                for file_input in file_inputs:
                    if file_input.is_enabled():
                        file_input.send_keys(os.path.abspath(IMAGE_PATH))
                        print("Image uploaded successfully")
                        time.sleep(3)
                        break
            except Exception as e:
                print(f"Could not upload image: {e}")
        elif IMAGE_PATH and not os.path.exists(IMAGE_PATH):
            print(f"Image file {IMAGE_PATH} not found, skipping image upload")
        else:
            print("No image path provided, skipping image upload")
        
        # Look for and click Post button
        print("Looking for Post button...")
        post_button_selectors = [
            "//div[@aria-label='Post'][@role='button']",
            "//button[contains(text(), 'Post')]",
            "//div[@role='button'][contains(text(), 'Post')]",
            "//button[@data-testid='react-composer-post-button']",
            "//div[@aria-label='Share'][@role='button']",
            "//span[text()='Post']/..",
        ]
        
        post_button = None
        for selector in post_button_selectors:
            try:
                print(f"Trying post button selector: {selector}")
                elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        post_button = element
                        print(f"Found post button with selector: {selector}")
                        break
                if post_button:
                    break
            except TimeoutException:
                continue
        
        if post_button is None:
            print("Could not find Post button")
            raise TimeoutException("No Post button found")
        
        # Click Post button
        if safe_click(driver, post_button, "Post button"):
            print("Post button clicked successfully")
        else:
            raise Exception("Failed to click Post button")
        
        # Wait for post to be created
        print("Waiting for post to be created...")
        time.sleep(5)
        print("Post creation completed!")
        
    except TimeoutException as e:
        print(f"Timeout error in post_to_profile: {e}")
        raise
    except Exception as e:
        print(f"Error in post_to_profile: {e}")
        raise

def main():
    """Main function to run the Facebook automation"""
    driver = None
    
    # Parse command line arguments
    global FB_EMAIL, FB_PASSWORD, TEXT, IMAGE_PATH
    
    if len(sys.argv) < 4:
        print("Error: Missing required arguments")
        print("Usage: python facebook-post.py <email> <password> <text> [image_path]")
        print("Example: python facebook-post.py user@email.com mypassword 'Hello World!' /path/to/image.jpg")
        sys.exit(1)
    
    FB_EMAIL = sys.argv[1]
    FB_PASSWORD = sys.argv[2]
    TEXT = sys.argv[3]
    
    if len(sys.argv) >= 5 and sys.argv[4] and sys.argv[4] != "null":
        IMAGE_PATH = sys.argv[4]
    else:
        IMAGE_PATH = None
    
    # Validate email and password are not empty
    if not FB_EMAIL or not FB_PASSWORD or not TEXT:
        print("Error: Email, password, and text cannot be empty")
        sys.exit(1)
    
    try:
        print("Setting up Chrome driver...")
        driver = setup_driver(headless=True)  # Use headless for scheduled posts
        
        # Delete existing cookies to force fresh login
        if os.path.exists(COOKIE_FILE):
            print("Removing saved cookies to force fresh login...")
            os.remove(COOKIE_FILE)
        
        # Always perform fresh login
        print("Performing fresh login with credentials...")
        login(driver)
        
        # Create post
        post_to_profile(driver)
        
        print("Facebook automation completed successfully!")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if driver:
            print("Closing browser...")
            time.sleep(2)
            driver.quit()

if __name__ == "__main__":
    main()
