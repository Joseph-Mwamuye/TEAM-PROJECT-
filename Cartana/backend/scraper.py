import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
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

    def clean_price(self, price_str: str) -> Optional[float]:
        """Extract and clean price from string, returning float value."""
        if not price_str:
            return None
        print(f"Cleaning price: {price_str}")
        price = re.sub(r'[^\d.,]', '', price_str)
        try:
            price = price.replace(',', '.')
            if price.count('.') > 1:
                parts = price.split('.')
                price = ''.join(parts[:-1]) + '.' + parts[-1]
            return float(price)
        except ValueError:
            print(f"Could not parse price: {price_str}")
            return None

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
                price = self.clean_price(price_elem.text)
                if price is not None:
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
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
                price = self.clean_price(price_elem.text)
                if price is not None:
                    results.append({
                        'title': title_elem.text.strip(),
                        'price': price,
                        'description': '',
                        'source': 'eBay',
                        'url': product_url
                    })
                    
        return results

    def search_products(self, query: str) -> pd.DataFrame:
        """Search for products across multiple platforms and return sorted results."""
        print("\nSearching Amazon...")
        amazon_results = self.search_amazon(query)
        
        print("\nSearching eBay...")
        ebay_results = self.search_ebay(query)
        
        all_results = amazon_results + ebay_results
        
        if not all_results:
            print("\nNo results found with valid prices")
            return pd.DataFrame(columns=['title', 'price', 'description', 'source', 'url'])
            
        df = pd.DataFrame(all_results)
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
        print(results.to_string(index=False))

if __name__ == "__main__":
    main()