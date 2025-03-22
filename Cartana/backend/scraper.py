import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import time
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProductScraper:
    def __init__(self):
        self.user_agents = [
            # Updated Chrome agents
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox agents
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0',
            
            # Safari agents
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15',
            
            # Mobile agents
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }
        

        self.amazon_base_url = "https://www.amazon.com"
        self.ebay_base_url = "https://www.ebay.com"
        self.jumia_base_url = "https://www.jumia.co.ke"
        self.kilimall_base_url = "https://www.kilimall.co.ke"
        # self.carrefourkenya_base_url = "https://www.carrefour.ke"
        self.oraimokenya_base_url = "https://ke.oraimo.com"
        self.hotpointkenya_base_url = "https://hotpoint.co.ke"
    
        # Get current USD to KES exchange rate
        self.usd_to_kes = self.get_exchange_rate()
        print(f"Current USD to KES exchange rate: {self.usd_to_kes}")
        
    def get_exchange_rate(self) -> float:
        """Get current USD to KES exchange rate."""
        try:
            # Using a free currency API
            response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
            data = response.json()
            return data["rates"]["KES"]
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            # Fallback to an approximate exchange rate if the API fails
            return 130.0  # Example fallback rate (update as needed)
        
    def make_request(self, url: str) -> Optional[str]:
        """Make HTTP request with rotating user-agent and random delays."""
        try:
            # Random delay with different ranges for mobile vs desktop user-agents
            is_mobile = random.choice([True, False])
            delay = random.uniform(1.5, 4.5) if is_mobile else random.uniform(1, 3)
            time.sleep(delay)
            
            # Rotate user agent
            headers = self.headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Debug prints (optional)
            print(f"\nUsed User-Agent: {headers['User-Agent']}")
            print(f"Status code: {response.status_code}")
            
            return response.text if response.status_code == 200 else None
            
        except Exception as e:
            print(f"Request error: {e}")
            return None
    

    def clean_price(self, price_str: str, currency: str = 'USD') -> Tuple[Optional[float], str]:
        """Extract and clean price from string, returning float value and currency."""
        if not price_str:
            return None, currency
    
        original_price = price_str
        print(f"Cleaning price: {price_str}")
    
        # Determine currency from string
        if 'KSh' in price_str or 'Ksh' in price_str or 'KES' in price_str:
            currency = 'KES'
        elif '£' in price_str or 'GBP' in price_str:
            currency = 'GBP'
        elif '€' in price_str or 'EUR' in price_str:
            currency = 'EUR'
    
        # Remove all non-numeric characters except periods and commas
        digits_only = re.sub(r'[^\d.,]', '', price_str)
    
        try:
            # Special case handling for prices with scientific notation like 3.4963e+4
            if 'e' in digits_only.lower():
                result = float(digits_only)
                print(f"Scientific notation detected: {digits_only} -> {result}")
                return result, currency
                
            # Strategy 1: Detect format based on position of comma and period
            last_comma_pos = digits_only.rfind(',')
            last_period_pos = digits_only.rfind('.')
            
            # If both exist, the rightmost one is likely the decimal separator
            if last_comma_pos > 0 and last_period_pos > 0:
                if last_comma_pos > last_period_pos:
                    # Comma is the decimal separator (European format)
                    # Replace all periods (thousands separators)
                    cleaned = digits_only.replace('.', '')
                    # Replace comma with period for float conversion
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Period is the decimal separator (US format)
                    # Remove all commas (thousands separators)
                    cleaned = digits_only.replace(',', '')
            elif last_comma_pos > 0:
                # Only commas exist
                # Check if it looks like a decimal separator (e.g., "34,96")
                if len(digits_only) - last_comma_pos <= 3:
                    # Likely a decimal comma
                    cleaned = digits_only.replace(',', '.')
                else:
                    # Likely a thousands separator
                    cleaned = digits_only.replace(',', '')
            elif last_period_pos > 0:
                # Only periods exist
                # Keep as is, already in format for float conversion
                cleaned = digits_only
            else:
                # No separators at all
                cleaned = digits_only
            
            # Final check: if the number looks unreasonably large, try to correct it
            # This is a heuristic to catch values like 349639.99 that should be 349.63 or 34.96
            result = float(cleaned)
            
            # For typical online products, if price > 10000, it might be an error
            if result > 10000 and '.' in cleaned:
                # Try to see if moving the decimal point makes more sense
                parts = cleaned.split('.')
                if len(parts) == 2 and len(parts[0]) > 2:
                    # Try different decimal places
                    candidates = []
                    # Try placing decimal point 2 positions from right in whole number part
                    if len(parts[0]) > 2:
                        test_price = float(parts[0][:-2] + '.' + parts[0][-2:] + parts[1])
                        candidates.append((test_price, abs(test_price - 100)))  # Distance from typical price
                    
                    # Check if any candidate is more reasonable
                    if candidates:
                        candidates.sort(key=lambda x: x[1])  # Sort by reasonableness
                        alternate_result = candidates[0][0]
                        
                        # If the alternate result is significantly different and more reasonable
                        if alternate_result < result / 10:
                            print(f"Price correction: {result} -> {alternate_result} (original: {original_price})")
                            result = alternate_result

            print(f"Parsed price: {result} {currency} (from {original_price})")
            return result, currency
        
        except ValueError as e:
            print(f"Could not parse price: {price_str}, error: {e}")
            return None, currency




    def search_amazon(self, query: str) -> List[Dict]:
        """Search Amazon for products."""
        url = f"https://www.amazon.com/s?k={quote_plus(query)}"
        results = []
        
        html_content = self.make_request(url)
        if not html_content:
            return results
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\nAmazon Debug Info:")
        print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        products = (
            soup.find_all('div', {'data-component-type': 's-search-result'}) or
            soup.find_all('div', {'class': 'sg-col-4-of-12'}) or
            soup.find_all('div', {'class': 'sg-col-20-of-24'})
        )
        
        print(f"Found {len(products)} products on Amazon")
        
        if len(products) == 0:
            print("Sample of HTML received:")
            print(soup.prettify()[:500])
        
        for product in products:
            title_elem = (
                product.find('span', {'class': 'a-text-normal'}) or
                product.find('h2', {'class': 'a-size-mini'})
            )
            price_elem = (
                product.find('span', {'class': 'a-price-whole'}) or
                product.find('span', {'class': 'a-offscreen'}) or
                product.find('span', {'class': 'a-price'})
            )
            
            # Find product URL
            url_elem = product.find('a', {'class': 'a-link-normal'})
            product_url = urljoin(self.amazon_base_url, url_elem['href']) if url_elem else None
            
            if title_elem and price_elem and product_url:
                price, currency = self.clean_price(price_elem.text)
                if price is not None:
                    price_kes = price * self.usd_to_kes if currency == 'USD' else None
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
                        'currency': currency,
                        'price_kes': price_kes,
                        'description': '',
                        'source': 'Amazon',
                        'url': product_url
                    })
                    
        return results
    
    def search_hotpoint_kenya(self, query: str) -> List[Dict]:
        """Search Hotpoint Kenya with updated 2024 selectors"""
        results = []
        try:
            url = f"https://hotpoint.co.ke/search/?q={quote_plus(query)}"
            html_content = self.make_request(url)
            if not html_content:
                return results
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print("\nHotpoint Kenya Debug Info:")
            print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
            
            # Updated product container selector
            products = soup.find_all('div', {'class': 'product-item'})
            print(f"Found {len(products)} products on Hotpoint Kenya")
            
            if not products:
                print("Sample of HTML received:")
                print(soup.prettify()[:500])
                return results
        
            for product in products:
                try:
                    # Extract product components
                    card = product.find('div', {'class': 'product-card'})
                    if not card:
                        continue

                    # Title extraction
                    title_elem = card.find('h5', {'class': 'product-card-name'})
                    
                    # Price handling
                    price_container = card.find('div', {'class': 'stockrecord-prices'})
                    current_price_elem = price_container.find('span', {'class': 'stockrecord-price-current'}) if price_container else None
                    original_price_elem = price_container.find('span', {'class': 'stockrecord-price-old'}) if price_container else None
                    
                    # URL extraction
                    url_elem = card.find('a', href=True)
                    product_url = urljoin(self.hotpointkenya_base_url, url_elem['href']) if url_elem else None

                    if all([title_elem, current_price_elem, product_url]):
                        # Clean price text
                        price_text = current_price_elem.text.replace('KES', '').strip()
                        price, currency = self.clean_price(price_text, 'KES')
                        
                        # Get original price if available
                        original_price = None
                        if original_price_elem:
                            original_price_text = original_price_elem.text.replace('KES', '').strip()
                            original_price, _ = self.clean_price(original_price_text, 'KES')
                        
                        results.append({
                            'title': title_elem.text.strip(),
                            'price': price,
                            'original_price': original_price,
                            'currency': currency,
                            'price_kes': price,
                            'source': 'Hotpoint Kenya',
                            'url': product_url,
                            # 'discount': self._calculate_discount(price, original_price)
                        })

                except Exception as product_error:
                    print(f"Hotpoint Kenya product error: {product_error}")
                    continue
                
        except Exception as e:
            print(f"Hotpoint Kenya search failed: {str(e)}")
            
        return results

    def _calculate_discount(self, current_price: float, original_price: Optional[float]) -> Optional[str]:
        """Calculate discount percentage if original price exists"""
        if original_price and current_price and original_price > current_price:
            discount = ((original_price - current_price) / original_price) * 100
            return f"{round(discount)}%"
        return None

    def search_ebay(self, query: str) -> List[Dict]:
        """Search eBay for products."""
        url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}"
        results = []
        
        html_content = self.make_request(url)
        if not html_content:
            return results
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\neBay Debug Info:")
        print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        products = (
            soup.find_all('div', {'class': 's-item__info'}) or
            soup.find_all('div', {'class': 'srp-river-result'}) or
            soup.find_all('li', {'class': 's-item'})
        )
        
        print(f"Found {len(products)} products on eBay")
        
        if len(products) == 0:
            print("Sample of HTML received:")
            print(soup.prettify()[:500])
        
        for product in products:
            title_elem = (
                product.find('div', {'class': 's-item__title'}) or
                product.find('h3', {'class': 's-item__title'})
            )
            price_elem = product.find('span', {'class': 's-item__price'})
            
            # Find product URL
            url_elem = product.find('a', {'class': 's-item__link'})
            product_url = url_elem['href'] if url_elem else None
            
            if title_elem and price_elem and product_url:
                price, currency = self.clean_price(price_elem.text)
                if price is not None:
                    price_kes = price * self.usd_to_kes if currency == 'USD' else None
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
                        'currency': currency,
                        'price_kes': price_kes,
                        'description': '',
                        'source': 'eBay',
                        'url': product_url
                    })
                    
        return results
    

    def search_jumia(self, query: str) -> List[Dict]:
        """Search Jumia Kenya with updated 2024 selectors"""
        results = []
        try:
            url = f"https://www.jumia.co.ke/catalog/?q={quote_plus(query)}"
            html_content = self.make_request(url)
            if not html_content:
                return results

            soup = BeautifulSoup(html_content, 'html.parser')
            products = soup.find_all('article', {'class': 'prd'})

            print(f"Found {len(products)} products on Jumia")

            for product in products:
                try:
                # Extract product details using updated selectors
                    link_element = product.find('a', {'class': 'core'})
                    if not link_element:
                        continue

                    product_url = urljoin(self.jumia_base_url, link_element['href'])
                    title_element = link_element.find('h3', {'class': 'name'})
                    price_element = link_element.find('div', {'class': 'prc'})

                    if not all([title_element, price_element, product_url]):
                        continue

                    title = title_element.text.strip()
                    price_text = price_element.text.strip()
                    price, currency = self.clean_price(price_text, 'KES')

                    results.append({
                        'title': title,
                        'price': price,
                        'currency': currency,
                        'price_kes': price,
                        'source': 'Jumia',
                        'url': product_url
                    })

                except Exception as product_error:
                    print(f"Jumia product error: {product_error}")
                    continue

        except Exception as e:
            print(f"Jumia search failed: {str(e)}")
            
        return results
    
    def search_oraimo_kenya(self, query: str) -> List[Dict]:
        """Search Oraimo Kenya with updated 2024 selectors"""
        results = []
        try:
            url = f"https://ke.oraimo.com/search?keyword={quote_plus(query)}"
            html_content = self.make_request(url)
            if not html_content:
                return results
            
            soup = BeautifulSoup(html_content, 'html.parser')
            print("\nOraimo Kenya Debug Info:")
            print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
            
            # Find all product items using the correct class
            products = soup.find_all('div', class_='js_product site-product')
            print(f"Found {len(products)} products on Oraimo Kenya")
        
            if not products:
                print("Sample of HTML received:")
                print(soup.prettify()[:500])
                return results
            
            for product in products:
                try:
                    # Extract product details
                    # Get the first anchor tag with product info
                    product_link = product.find('a', class_='product-img js_load_item js_select_item')
                    
                    # Extract title from h3 > a > span
                    title_elem = product.find('h3').find('a').find('span')
                    
                    # Extract price info
                    price_container = product.find('div', class_='product-desc').find('p', class_='product-price')
                    
                    # Get URL
                    url_elem = product_link['href'] if product_link else None
                    
                    # Get data attributes for additional info
                    product_data = {}
                    if product_link:
                        product_data = {
                            'id': product_link.get('data-id'),
                            'sku': product_link.get('data-sku'),
                            'name': product_link.get('data-name'),
                            'price': product_link.get('data-price'),
                            'category': product_link.get('data-category')
                        }
                    
                    # Handle price extraction
                    if price_container:
                        current_price = price_container.find('span').text.strip()
                        original_price = price_container.find('del').text.strip() if price_container.find('del') else None
                    else:
                        current_price = None
                        original_price = None
                    
                    # Get review info if available
                    review_container = product.find('div', class_='product-review')
                    review_score = review_container.find('span', class_='review-score').text.strip() if review_container else None
                    review_count = review_container.find('span', class_='review-count').text.strip() if review_container else None
                    
                    # Extract product features
                    features = []
                    product_points = product.find('div', class_='product-points')
                    if product_points:
                        for point in product_points.find_all('p', class_='product-point'):
                            feature_text = point.find('span').find('span').text.strip()
                            features.append(feature_text)
                    
                    if title_elem and current_price and url_elem:
                        price_text = current_price.replace('KES', '').strip()
                        price, currency = self.clean_price(price_text, 'KES')
                        
                        results.append({
                            'title': title_elem.text.strip(),
                            'price': price,
                            'currency': currency,
                            'price_kes': price,
                            'original_price': self.clean_price(original_price.replace('KES', '').strip())[0] if original_price else None,
                            'description': ' | '.join(features) if features else '',
                            'review_score': review_score.replace('(', '').replace(')', '') if review_score else None,
                            'review_count': review_count.replace('(', '').replace(')', '') if review_count else None,
                            'sku': product_data.get('sku'),
                            'category': product_data.get('category'),
                            'source': 'Oraimo Kenya',
                            'url': url_elem if url_elem.startswith('http') else urljoin(self.oraimokenya_base_url, url_elem)
                        })
                except Exception as product_error:
                    print(f"Oraimo Kenya product parsing error: {product_error}")
                    continue
        except Exception as e:
            print(f"Oraimo Kenya search failed: {str(e)}")
        
        return results
    


    # def search_carrefour_kenya(self, query: str) -> List[Dict]:
    #     """Search Carrefour Kenya using Selenium for JS-rendered content"""
    #     results = []
    #     driver = None
    #     try:
    #         url = f"https://www.carrefour.ke/mafken/en/v4/search?keyword={quote_plus(query)}"
            
    #         # Configure Selenium
    #         driver = self.get_driver()  # Use your existing browser setup
    #         driver.get(url)
            
    #         # Wait for products to load
    #         WebDriverWait(driver, 15).until(
    #             EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="product_card_image_container"]'))
    #         )
            
    #         # Scroll to load all products
    #         driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    #         time.sleep(2)
            
    #         # Get the rendered HTML
    #         soup = BeautifulSoup(driver.page_source, 'html.parser')
            
    #         # Updated selector strategy
    #         product_containers = soup.find_all('div', {'class': 'css-yqd9tx'})
    #         print(f"Found {len(product_containers)} products")
            
    #         for container in product_containers:
    #             try:
    #                 # Extract product details
    #                 title_elem = container.find('a', {'data-testid': 'product_name'})
    #                 price_container = container.find('div', {'data-testid': 'product_price'})
                    
    #                 if not title_elem or not price_container:
    #                     continue
                    
    #                 # Price components
    #                 main_price = price_container.find('div', class_='css-14zpref')
    #                 decimal_price = price_container.find('div', class_='css-1pjcwg4')
    #                 currency = price_container.find('span', class_='css-1edki26')
                    
    #                 # Build price string
    #                 price_text = f"{main_price.text.strip()}{decimal_price.text.strip()}" if main_price and decimal_price else ""
    #                 currency = currency.text.strip() if currency else 'KES'
                    
    #                 # Clean price
    #                 price, currency = self.clean_price(price_text, currency)
                    
    #                 results.append({
    #                     'title': title_elem.text.strip(),
    #                     'price': price,
    #                     'currency': currency,
    #                     'price_kes': price,
    #                     'source': 'Carrefour Kenya',
    #                     'url': urljoin(self.carrefourkenya_base_url, title_elem['href'])
    #                 })
                    
    #             except Exception as e:
    #                 print(f"Product parsing error: {str(e)}")
    #                 continue
                    
    #     except Exception as e:
    #         print(f"Carrefour search failed: {str(e)}")
    #     finally:
    #         if driver:
    #             driver.quit()
        
    #     return results
    
    
    def search_kilimall(self, query: str) -> List[Dict]:
        """Search Kilimall Kenya with updated 2024 selectors"""
        results = []
        try:
            url = f"https://www.kilimall.co.ke/search?q={quote_plus(query)}"
            html_content = self.make_request(url)
            
            if not html_content:
                return results

            soup = BeautifulSoup(html_content, 'html.parser')
                
            # Find product containers
            products = soup.find_all('div', {'class': 'listing-item'})
            print(f"Found {len(products)} products on Kilimall")

            for product in products:
                try:
                    # Extract product components
                    product_item = product.find('div', {'class': 'product-item'})
                    if not product_item:
                        continue

                    # Title extraction
                    title_elem = product_item.find('p', {'class': 'product-title'})
                    
                    # Price extraction
                    price_elem = product_item.find('div', {'class': 'product-price'})
                    
                    # URL extraction
                    url_elem = product_item.find('a', href=True)
                    product_url = urljoin(self.kilimall_base_url, url_elem['href']) if url_elem else None

                    # Validate required elements
                    if not all([title_elem, price_elem, product_url]):
                        continue

                    # Process data
                    price_text = price_elem.get_text(strip=True)
                    price, currency = self.clean_price(price_text, 'KES')
                    
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'price': price,
                        'currency': currency,
                        'price_kes': price,
                        'source': 'Kilimall',
                        'url': product_url
                    })

                except Exception as product_error:
                    print(f"Kilimall product error: {product_error}")
                    continue

        except Exception as e:
            print(f"Kilimall search failed: {str(e)}")
        
        return results



    def search_products(self, query: str) -> pd.DataFrame:
        """Search for products across multiple platforms and return sorted results."""
        all_results= []

        search_functions = [
            (self.search_amazon, "Amazon"),
            (self.search_ebay, "eBay"),
            (self.search_jumia, "Jumia"),
            (self.search_kilimall, "Kilimall"),
            # (self.search_carrefour_kenya, "Carrefour Kenya"),
            (self.search_oraimo_kenya, "Oraimo Kenya"),
            (self.search_hotpoint_kenya, "Hotpoint Kenya")
        ]

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_platform = {
                executor.submit(func, query): platform_name
                for func, platform_name in search_functions
            }

            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    platform_results = future.result()
                    all_results.extend(platform_results)
                    print(f"\nCompleted search on {platform} with {len(platform_results)} results")
                except Exception as e:
                    print(f"\nError searching {platform}: {str(e)}")
        
        
        if not all_results:
            print("\nNo results found with valid prices")
            return pd.DataFrame(columns=['title', 'price', 'currency', 'price_usd', 'price_kes', 'description', 'source', 'url'])
            
        df = pd.DataFrame(all_results)
        
        # Format prices for display
        if 'price_kes' in df.columns:
            df['price_kes'] = df['price_kes'].apply(lambda x: f"{x:.2f} KES" if pd.notnull(x) else "N/A")
        
        if 'price_usd' in df.columns:
            df['price_usd'] = df['price_usd'].apply(lambda x: f"{x:.2f} USD" if pd.notnull(x) else "N/A")
            
        # Format original prices with currency
        df['display_price'] = df.apply(
            lambda row: f"{row['price']:.2f} {row['currency']}", axis=1
        )
        
        # Sort by price (convert all to USD for sorting)
        if 'currency' in df.columns:
            def get_usd_price(row):
                if row['currency'] == 'USD':
                    return row['price']
                elif row['currency'] == 'KES':
                    return row['price'] / self.usd_to_kes
                else:
                    return row['price']  # Fallback
                    
            df['sort_price'] = df.apply(get_usd_price, axis=1)
            df = df.sort_values('sort_price')
            df = df.drop('sort_price', axis=1)
        else:
            df = df.sort_values('price')
            
        return df

def main():
    scraper = ProductScraper()
    
    while True:
        query = input("\nEnter product to search (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        print("\nSearching for products...")
        results = scraper.search_products(query)
        
        if len(results) == 0:
            print("No results found.")
            continue
            
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print("\nResults (sorted by price):")
        # Reorder columns for better display
        display_cols = ['title', 'display_price', 'price_usd', 'price_kes', 'source', 'url']
        display_cols = [col for col in display_cols if col in results.columns]
        print(results[display_cols].to_string(index=False))

if __name__ == "__main__":
    main()