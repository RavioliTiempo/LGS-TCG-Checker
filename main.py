from playwright.sync_api import sync_playwright
# Checks TCGPlayer for card prices and availability from specific sellers

# TODO: Ask user for the card code


codes = {
    "Portals Salisbury": "a89437e2",
    "Portals Easton": "21597b4f",
    "Portals Kent Island": "280dfda8",
    "RNG Games": "fed53a55",
    "Two Pair Collectibles (Easton)": "65780286",
    "Safari Zone (Smyrna)": "d89a247e"
}

Base_URL = "https://www.tcgplayer.com/product/"
print("Example card code: https://www.tcgplayer.com/product/230147?Language=English")
Card_Code = input("Enter the card code (e.g., 230147): ")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    Full_URL = Base_URL + Card_Code
    page = browser.new_page()
    page.goto(Full_URL)
    page.wait_for_load_state('networkidle')
    card_name = page.query_selector('.product-details__name').inner_text()
    print(card_name)
    spotlight_content = page.locator('.spotlight__listing').inner_text()
    print(f"TCG Price: {spotlight_content}")
    for code_name, code_value in codes.items():
        Full_URL = Base_URL + Card_Code + "/?seller=" + code_value
        page = browser.new_page()
        page.goto(Full_URL)
        page.wait_for_load_state('networkidle')
        no_listings = page.query_selector('.no-result.spotlight__no-listings')
        
        if no_listings:
            print(f"{code_name}: Out of Stock")
        else:
            spotlight_content = page.locator('.spotlight__listing').inner_text()
            print(f"{code_name}: {spotlight_content}")
    browser.close()
