from playwright.sync_api import sync_playwright
import time
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    # Page 1: User A
    page1 = context.new_page()
    page1.goto("http://localhost:5000")

    # Page 2: User B
    page2 = context.new_page()
    page2.goto("http://localhost:5000")

    # Wait for pages to load
    page1.wait_for_selector("#questionInput")
    page2.wait_for_selector("#questionInput")

    print("Both pages loaded")

    # User A starts a long request (Study generation takes longer)
    page1.locator("button[data-tool='study']").click()
    page1.fill("#questionInput", "Love")
    page1.click("#askButton")
    print("User A started study")

    # Wait a tiny bit to ensure A gets the lock
    time.sleep(1)

    # User B starts a request (Ask)
    page2.fill("#questionInput", "Hope")
    page2.click("#askButton")
    print("User B started ask")

    # Wait for the queue to appear on Page 2
    try:
        # Check if queue display appears
        queue_display = page2.locator("#queueDisplay")
        queue_display.wait_for(state="visible", timeout=10000)
        print("Queue display visible for User B")

        # Take screenshot of Page 2 (waiting)
        page2.screenshot(path="verification/queue_ui.png")
        print("Screenshot saved to verification/queue_ui.png")

        # Verify text content
        pos_text = page2.locator("#queuePosNum").inner_text()
        print(f"User B Position: {pos_text}")

    except Exception as e:
        print(f"Error checking queue: {e}")
        page2.screenshot(path="verification/error_state.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
