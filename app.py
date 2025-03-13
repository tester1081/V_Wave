import os
import time
from flask import Flask, request, jsonify, render_template
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# Load sensitive data from environment variables
EMAIL = os.getenv("CODASHOP_EMAIL", "prospemichael@gmail.com")  # Default for testing
PASSWORD = os.getenv("CODASHOP_PASSWORD", "codashop5050")  # Default for testing

# URLs and selectors
SIGN_IN_URL = "https://www.codashop.com/en-ng/sign-in"
SIGN_IN_EMAIL_BUTTON_XPATH = '//*[@id="signin-email"]'
EMAIL_INPUT_SELECTOR = 'input[type="email"]'
PASSWORD_INPUT_SELECTOR = 'input[type="password"]'
SUBMIT_BUTTON_SELECTOR = 'button[type="submit"]'
COD_MOBILE_URL = "https://www.codashop.com/en-ng/call-of-duty-mobile"
USER_ID_INPUT_SELECTOR = "#userId"
PRODUCT_XPATH_TEMPLATE = '//*[@id="voucher"]/div[2]/ul/li[{}]/div/div[1]'  # Updated XPath
BUY_NOW_BUTTON_XPATH = '//*[@id="voucher"]/div[3]/button'  # Example XPath for "Buy Now" button

def simulate_human_delay(seconds=0.5):
    """Simulate human-like delay between actions."""
    time.sleep(seconds)

def retry_interaction(action, description, timeout=30):
    """
    Retry an interaction until it succeeds or the timeout is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            action()
            print(f"✅ {description} successful!")
            return True
        except Exception as e:
            print(f"⚠️ {description} failed. Retrying...")
            simulate_human_delay(0.5)  # Short delay between retries
    print(f"❌ {description} failed after {timeout} seconds.")
    return False

def login_and_select_product(player_id, product_index):
    with sync_playwright() as p:
        # Launch browser in non-headless mode (visible)
        browser = p.chromium.launch(headless=False)  # Set headless=True for production
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: Go to the sign-in page
            print("🌐 Navigating to sign-in page...")
            page.goto(SIGN_IN_URL, timeout=60000, wait_until="domcontentloaded")
            simulate_human_delay()

            # Step 2: Wait for the "Sign in with Email" button to appear
            print("⏳ Waiting for 'Sign in with Email' button...")
            retry_interaction(
                lambda: page.wait_for_selector(f'xpath={SIGN_IN_EMAIL_BUTTON_XPATH}', state="visible", timeout=5000),
                "Waiting for 'Sign in with Email' button"
            )

            # Step 3: Click "Sign in with Email"
            print("🔑 Clicking 'Sign in with Email'...")
            retry_interaction(
                lambda: page.click(f'xpath={SIGN_IN_EMAIL_BUTTON_XPATH}'),
                "Clicking 'Sign in with Email'"
            )

            # Step 4: Fill the login form
            print("⌨️ Filling login form...")
            retry_interaction(
                lambda: page.fill(EMAIL_INPUT_SELECTOR, EMAIL),
                "Filling email"
            )
            retry_interaction(
                lambda: page.fill(PASSWORD_INPUT_SELECTOR, PASSWORD),
                "Filling password"
            )

            # Step 5: Submit the login form
            print("✅ Logging in...")
            retry_interaction(
                lambda: page.click(SUBMIT_BUTTON_SELECTOR),
                "Submitting login form"
            )

            # Wait for login to complete (check for a logged-in element)
            print("⏳ Waiting for login to complete...")
            retry_interaction(
                lambda: page.wait_for_selector(USER_ID_INPUT_SELECTOR, timeout=5000),
                "Waiting for login to complete"
            )
            print("✅ Login successful!")

            # Step 6: Navigate to the COD Mobile page
            print("🌐 Navigating to COD Mobile page...")
            retry_interaction(
                lambda: page.goto(COD_MOBILE_URL, timeout=60000, wait_until="domcontentloaded"),
                "Navigating to COD Mobile page"
            )
            simulate_human_delay()

            # Step 7: Wait for a few seconds before entering the player ID
            print("⏳ Waiting before entering player ID...")
            simulate_human_delay(5)  # Wait 5 seconds before entering the ID

            # Step 8: Enter the player ID
            print("⌨️ Entering player ID...")
            retry_interaction(
                lambda: page.fill(USER_ID_INPUT_SELECTOR, player_id),
                "Entering player ID"
            )

            # Step 9: Select the product as quickly as possible
            print(f"🛒 Selecting product index {product_index}...")
            product_xpath = PRODUCT_XPATH_TEMPLATE.format(product_index)
            retry_interaction(
                lambda: page.click(f'xpath={product_xpath}'),
                "Selecting product"
            )

            # Step 10: Click the "Buy Now" button (if available)
            print("🛍️ Attempting to click 'Buy Now' button...")
            retry_interaction(
                lambda: page.click(f'xpath={BUY_NOW_BUTTON_XPATH}'),
                "Clicking 'Buy Now' button"
            )

            return f"✅ Player ID {player_id} entered, Product {product_index} selected for COD!"
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return f"❌ An error occurred: {str(e)}"
        finally:
            # Close the browser
            print("🛑 Closing browser...")
            browser.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    player_id = data.get("playerId")
    product_index = data.get("productIndex")

    if not player_id or product_index is None:
        return jsonify({"message": "❌ Missing Player ID or Product Index!"})

    result = login_and_select_product(player_id, int(product_index))
    return jsonify({"message": result})

if __name__ == "__main__":
    app.run(debug=True)