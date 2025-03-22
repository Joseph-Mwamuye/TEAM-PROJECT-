# product_scraper.py
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
import time
import random

class ProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        """Make HTTP request with proper error handling and debugging."""
        try:
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            print(f"\nDebug info for {url}:")
            print(f"Status code: {response.status_code}")
            print(f"Response length: {len(response.text)} characters")
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
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
        """Search Jumia Kenya for products."""
        url = f"https://www.jumia.co.ke/catalog/?q={quote_plus(query)}"
        results = []
    
        html_content = self.make_request(url)
        if not html_content:
            return results
        
        soup = BeautifulSoup(html_content, 'html.parser')
    
        print("\nJumia Debug Info:")
        print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        # Jumia product elements
        products = (
            soup.find_all('article', {'class': 'prd'}) or
            soup.find_all('div', {'class': 'info'})
        )
    
        print(f"Found {len(products)} products on Jumia")
    
        if len(products) == 0:
            print("Sample of HTML received:")
            print(soup.prettify()[:500])
    
        for product in products:
            # Try different possible selectors for Jumia product info
            title_elem = product.find('h3', {'class': 'name'})
            price_elem = product.find('div', {'class': 'prc'})
            
            # Find product URL
            url_elem = product.find('a')
            
            # Debug the URL element
            if url_elem:
                print(f"URL element attributes: {url_elem.attrs}")
                product_url = None
                # Check if href exists before accessing it
                if 'href' in url_elem.attrs:
                    product_url = urljoin(self.jumia_base_url, url_elem['href'])
                else:
                    # Try to find parent with href if the direct element doesn't have it
                    parent_with_href = product.find_parent('a', href=True)
                    if parent_with_href:
                        product_url = urljoin(self.jumia_base_url, parent_with_href['href'])
            else:
                product_url = None
                print("No URL element found for this product")
            
            if title_elem and price_elem and product_url:
                price, currency = self.clean_price(price_elem.text, 'KES')  # Jumia Kenya uses KES
                if price is not None:
                    price_usd = price / self.usd_to_kes if currency == 'KES' else None
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
                        'currency': currency,
                        'price_usd': price_usd,
                        'price_kes': price,  # Original price already in KES
                        'description': '',
                        'source': 'Jumia',
                        'url': product_url
                    })
                    
        return results

    def search_kilimall(self, query: str) -> List[Dict]:
        """Search Kilimall Kenya for products."""
        url = f"https://www.kilimall.co.ke/new/commoditysearch?q={quote_plus(query)}"
        results = []
        
        html_content = self.make_request(url)
        if not html_content:
            return results
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\nKilimall Debug Info:")
        print(f"Page title: {soup.title.string if soup.title else 'No title found'}")
        
        # Kilimall product elements
        products = (
            soup.find_all('div', {'class': 'item_box'}) or
            soup.find_all('li', {'class': 'item'})
        )
        
        print(f"Found {len(products)} products on Kilimall")
        
        if len(products) == 0:
            print("Sample of HTML received:")
            print(soup.prettify()[:500])
        
        for product in products:
            title_elem = product.find('div', {'class': 'goods-name'})
            price_elem = product.find('div', {'class': 'price'})
            
            # Find product URL
            url_elem = product.find('a', {'class': 'goods-name-link'})
            product_url = urljoin(self.kilimall_base_url, url_elem['href']) if url_elem else None
            
            if title_elem and price_elem and product_url:
                price, currency = self.clean_price(price_elem.text, 'KES')  # Kilimall Kenya uses KES
                if price is not None:
                    price_usd = price / self.usd_to_kes if currency == 'KES' else None
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
                        'currency': currency,
                        'price_usd': price_usd,
                        'price_kes': price,  # Original price already in KES
                        'description': '',
                        'source': 'Kilimall',
                        'url': product_url
                    })
                    
        return results

    def search_products(self, query: str) -> pd.DataFrame:
        """Search for products across multiple platforms and return sorted results."""
        print("\nSearching Amazon...")
        amazon_results = self.search_amazon(query)
        
        print("\nSearching eBay...")
        ebay_results = self.search_ebay(query)
        
        print("\nSearching Jumia...")
        jumia_results = self.search_jumia(query)
        
        print("\nSearching Kilimall...")
        kilimall_results = self.search_kilimall(query)
        
        all_results = amazon_results + ebay_results + jumia_results + kilimall_results
        
        if not all_results:
            print("\nNo results found with valid prices")
            return pd.DataFrame(columns=['title', 'price', 'currency', 'price_usd', 'price_kes', 'description', 'source', 'url'])
            
        df = pd.DataFrame(all_results)
        
        # Format prices for display
        if 'price_kes' in df.columns:
            df['price_kes_numeric'] = df['price_kes']
            # Only format for display
            df['price_kes_display'] = df['price_kes'].apply(lambda x: f"{x:.2f} KES" if pd.notnull(x) else "N/A")
    
        if 'price_usd' in df.columns:
            df['price_usd_numeric'] = df['price_usd']
            # Only format for display
            df['price_usd_display'] = df['price_usd'].apply(lambda x: f"{x:.2f} USD" if pd.notnull(x) else "N/A")
            
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