from playwright.sync_api import sync_playwright

def verify_seo(page):
    # Navigate to home page
    page.goto("http://localhost:5000")

    # Check for recent questions section
    # Note: It might be empty if no questions have been asked yet, but the container should be there if we force it
    # Actually, in my code, I only show it if recent_shares is not empty.
    # So I need to seed a question first.

    # Check meta tags
    description = page.locator('meta[name="description"]').get_attribute('content')
    print(f"Meta Description: {description}")

    # Navigate to a passage page
    page.goto("http://localhost:5000/bible/kjv/John/3")

    # Check breadcrumb schema
    breadcrumbs = page.locator('script[type="application/ld+json"]').last
    schema_content = breadcrumbs.text_content()
    print(f"Breadcrumb Schema: {schema_content}")

    page.screenshot(path="verification/seo_verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify_seo(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
