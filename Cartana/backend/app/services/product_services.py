from typing import List, Dict
import pandas as pd
import logging
from ..models.product import ProductCreate
from ..database import save_product_results, get_products_by_query
from .scraper_service import ScraperService

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.scraper = ScraperService()
    
    async def search_and_save_products(self, query: str) -> List[Dict[str, any]]:
        """Search for products and save results to database"""
        logger.info(f"Searching for products with query: {query}")
        
        # Check if we have recent results for this query
        cached_results = await get_products_by_query(query)
        if cached_results:
            logger.info(f"Found cached results for query: {query}")
            return cached_results
        
        # If no cached results, perform scraping
        products = await self.scraper.search_products(query)
        logger.info(f"Found {len(products)} products for query: {query}")
        
        
        if isinstance(products, pd.DataFrame):
            logger.info("Converting DataFrame to list of dictionaries.")
            products = products.to_dict(orient="records")
        # Save results to database
        if products:
            await save_product_results(query, products)
            logger.info(f"Saved {len(products)} products to database")
        
        return products
    
    async def format_products_for_response(self, products: List[Dict]) -> List[Dict]:
        """Format product data for API response"""
        # Fix: Ensure products is a list, not a DataFrame
        if isinstance(products, pd.DataFrame):
            logger.info("Converting DataFrame to list of dictionaries.")
            products = products.to_dict(orient="records")
        formatted_products = []
        
        for product in products:
            formatted_product = {
                "title": product["title"],
                "price": product["price"],
                "currency": product["currency"],
                "display_price": f"{product['price']:.2f} {product['currency']}",
                "price_usd": f"{product['price_usd']:.2f} USD" if product.get("price_usd") else None,
                "price_kes": f"{product['price_kes']:.2f} KES" if product.get("price_kes") else None,
                "description": product.get("description", ""),
                "source": product["source"],
                "url": product["url"],
                "logo_url": self._get_source_logo(product["source"])
            }
            formatted_products.append(formatted_product)
        
        return formatted_products
    
    def _get_source_logo(self, source: str) -> str:
        """Get logo URL for a source"""
        logos = {
            "Amazon": "/images/amazon-logo.png",
            "eBay": "/images/ebay-logo.png",
            "Jumia": "/images/jumia-logo.png",
            "Kilimall": "/images/kilimall-logo.png"
        }
        return logos.get(source, "/images/default-logo.png")