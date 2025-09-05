from flask import Flask, render_template_string, request
from playwright.sync_api import sync_playwright
import time
from urllib.parse import quote_plus

app = Flask(__name__)

codes = {
    "Portals (Salisbury)": "a89437e2",
    "Portals (Easton)": "21597b4f",
    "Portals (Kent Island)": "280dfda8",
    "RNG Games(South Plainfield)": "fed53a55",
    "Two Pair Collectibles (Easton)": "65780286",
    "Safari Zone (Smyrna)": "d89a247e"
}

Base_URL = "https://www.tcgplayer.com/product/"

def extract_price_from_text(text):
    """Extract price information from various text formats"""
    if not text or "Out of Stock" in text or "No listings" in text:
        return "Out of Stock"
    
    # Look for price patterns
    import re
    price_pattern = r'\$\d+\.\d{2}'
    prices = re.findall(price_pattern, text)
    
    if prices:
        return f"From {prices[0]}"
    
    return text.strip()

@app.route("/", methods=["GET", "POST"])
def index():
    results = {}
    card_name = ""
    card_image = ""
    error = ""
    if request.method == "POST":
        card_code = request.form["card_code"].strip()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Set user agent to avoid bot detection
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Main product page
                page.goto(Base_URL + card_code, wait_until='networkidle')
                time.sleep(3)  # Additional wait for JavaScript to load
                
                # Get card name
                try:
                    card_name = page.query_selector('h1.product-details__name').inner_text()
                except:
                    card_name = "Unknown Card"
                
                # Get TCGPlayer price - try multiple selectors
                tcg_price = "Price not available"
                try:
                    # Try multiple possible selectors for price
                    selectors = [
                        '.spotlight__price',
                        '[data-testid="price"]',
                        '.price-point',
                        '.listing-item__price',
                        'span[class*="price"]'
                    ]
                    
                    for selector in selectors:
                        price_elements = page.query_selector_all(selector)
                        for elem in price_elements:
                            text = elem.inner_text().strip()
                            if text and '$' in text:
                                tcg_price = extract_price_from_text(text)
                                break
                        if tcg_price != "Price not available":
                            break
                    
                except Exception as e:
                    tcg_price = f"Error: {str(e)}"
                
                results["TCGPlayer"] = tcg_price
                
                # Card image
                card_image = f"https://tcgplayer-cdn.tcgplayer.com/product/{card_code}_in_600x600.jpg"

                # Check each seller
                for code_name, code_value in codes.items():
                    try:
                        # Create new page for each seller
                        seller_page = context.new_page()
                        seller_page.set_extra_http_headers({
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        })
                        
                        seller_url = f"{Base_URL}{card_code}/?seller={code_value}"
                        seller_page.goto(seller_url, wait_until='networkidle')
                        time.sleep(2)  # Wait for page to load
                        
                        # Check for out of stock messages
                        out_of_stock_selectors = [
                            '.no-result',
                            '.no-listings',
                            '.out-of-stock',
                            'text=No listings',
                            'text=Out of stock',
                            'text=Not available'
                        ]
                        
                        out_of_stock = False
                        for selector in out_of_stock_selectors:
                            if seller_page.query_selector(selector):
                                out_of_stock = True
                                break
                        
                        if out_of_stock:
                            results[code_name] = "Out of Stock"
                        else:
                            # Try to find price
                            seller_price = "Price not available"
                            price_selectors = [
                                '.spotlight__price',
                                '.price-point',
                                '[data-testid="price"]',
                                '.listing-item__price',
                                'span[class*="price"]'
                            ]
                            
                            for selector in price_selectors:
                                price_elements = seller_page.query_selector_all(selector)
                                for elem in price_elements:
                                    text = elem.inner_text().strip()
                                    if text and '$' in text:
                                        seller_price = extract_price_from_text(text)
                                        break
                                if seller_price != "Price not available":
                                    break
                            
                            results[code_name] = seller_price
                        
                        seller_page.close()
                        
                    except Exception as e:
                        results[code_name] = f"Error: {str(e)}"
                        if 'seller_page' in locals():
                            seller_page.close()

                browser.close()
                
        except Exception as e:
            error = str(e)

    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TCGPlayer Card Lookup</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                form { margin: 20px 0; }
                input[type="text"] { padding: 10px; width: 300px; font-size: 16px; }
                button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
                button:hover { background: #0056b3; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
                th { background: #f8f9fa; font-weight: bold; }
                .error { color: red; }
                .card-info { display: flex; align-items: flex-start; gap: 20px; margin: 20px 0; }
                .card-image { max-width: 300px; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>TCGPlayer Card Lookup</h1>
            <form method="post">
                <input name="card_code" placeholder="Enter card code (e.g., 230147)" required>
                <button type="submit">Check Prices</button>
            </form>
            
            {% if error %}
                <p class="error">Error: {{ error }}</p>
            {% endif %}
            
            {% if card_name %}
                <div class="card-info">
                    <img src="{{ card_image }}" alt="{{ card_name }}" class="card-image">
                    <div>
                        <h2>{{ card_name }}</h2>
                    </div>
                </div>

                <table>
                    <tr>
                        <th>Seller</th>
                        <th>Price / Availability</th>
                    </tr>
                    {% for seller, price in results.items() %}
                    <tr>
                        <td><b>{{ seller }}</b></td>
                        <td>{{ price }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% endif %}
        </body>
        </html>
    """, results=results, card_name=card_name, error=error, card_image=card_image)

if __name__ == "__main__":
    app.run(debug=True)