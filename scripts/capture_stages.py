import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--window-size=1366,850')
driver = webdriver.Chrome(options=opts)

print("Capturing 1: Dashboard...")
driver.get("http://localhost:8000")
time.sleep(2)
driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_01_dashboard.png")

print("Capturing 2: Events Ledger & Agent Workflow...")
# Find events section or scroll down
try:
    ev_el = driver.find_element(By.ID, "events-list")
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", ev_el)
except Exception:
    driver.execute_script("window.scrollTo(0, 1100);")
time.sleep(1)
driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_02_events_ledger.png")

print("Capturing 3: Reference Store Hero...")
driver.get("http://localhost:8000/sites/1/")
time.sleep(2)
driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_03_store_hero.png")

print("Capturing 4: Store Catalog & Filters...")
driver.execute_script("window.scrollTo(0, 700);")
time.sleep(1)
driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_04_store_catalog.png")

print("Capturing 5: Cart Drawer & Checkout...")
try:
    # Add first product to cart
    add_btns = driver.find_elements(By.CSS_SELECTOR, "button")
    for b in add_btns:
        if "أضف" in b.text or "Add" in b.text or "سلة" in b.text:
            b.click()
            break
    time.sleep(1)
    driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_05_store_cart.png")
    
    # Click checkout button
    for b in driver.find_elements(By.CSS_SELECTOR, "button"):
        if "إتمام" in b.text or "Checkout" in b.text or "شراء" in b.text or "دفع" in b.text:
            b.click()
            break
    time.sleep(1)
    driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_05_store_checkout.png")
except Exception as e:
    print("Cart/checkout error:", e)

print("Capturing 6: English Mode...")
try:
    for b in driver.find_elements(By.CSS_SELECTOR, "button"):
        if "English" in b.text:
            b.click()
            time.sleep(1)
            driver.save_screenshot("e:/alkolya/Internships/Projects/autocorp/screenshot_06_store_english.png")
            break
except Exception as e:
    print("English switch error:", e)

driver.quit()
print("All screenshots successfully captured!")
