from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import math
import time
import os
from dotenv import load_dotenv
import supabase
from datetime import datetime, timedelta

# Import your scraper
from .productscraper import ProductScraper

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Price Comparison API", 
              description="API for comparing product prices across Amazon, eBay, Jumia, and Kilimall")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = supabase.create_client(supabase_url, supabase_key)

# Initialize scraper
scraper = ProductScraper()

# Cache for recent searches (to reduce redundant scraping)
search_cache = {}
CACHE_EXPIRY = 3600  # Cache results for 1 hour

# Pydantic models
class ProductBase(BaseModel):
    title: str
    price: float
    currency: str
    source: str
    url: str
    description: Optional[str] = ""
    price_kes: Optional[float] = None
    price_usd: Optional[float] = None

class ProductResponse(ProductBase):
    id: Optional[int] = None
    search_query: str
    search_timestamp: datetime
    display_price: str

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    search_id: int
    results: List[ProductResponse]
    timestamp: datetime
    query: str

# Function to store search results in Supabase
async def store_search_results(query: str, results: List[dict]):
    # Create a search record
    search_data = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "result_count": len(results)
    }
    
    # Insert search data
    search_response = supabase_client.table("searches").insert(search_data).execute()
    
    if len(search_response.data) == 0:
        print("Failed to insert search data")
        return
        
    search_id = search_response.data[0]["id"]
    
    # Prepare product data with search_id reference
    products_data = []
    for product in results:
        product_data = {
            "search_id": search_id,
            "title": product["title"],
            "price": product["price"],
            "currency": product["currency"],
            "source": product["source"],
            "url": product["url"],
            "description": product.get("description", ""),
            "price_kes": product.get("price_kes"),
            "price_usd": product.get("price_usd")
        }
        products_data.append(product_data)
    
    # Insert products in batches of 100
    batch_size = 100
    cleaned_products_data = []

# Clean the data before insertion
    for product in products_data:
    # Replace infinity and NaN values
        for key, value in product.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    product[key] = None
    
    # Ensure price fields are valid numbers
    for price_field in ['price', 'price_kes', 'price_usd']:
        if price_field in product and product[price_field] is not None:
            # If it's a string with currency code, extract just the number
            if isinstance(product[price_field], str) and any(currency in product[price_field] for currency in ['KES', 'USD']):
                try:
                    product[price_field] = float(product[price_field].split()[0])
                except ValueError:
                    product[price_field] = None
    
    cleaned_products_data.append(product)

# Insert the cleaned data
    for i in range(0, len(cleaned_products_data), batch_size):
        batch = cleaned_products_data[i:i+batch_size]
        supabase_client.table("products").insert(batch).execute()

    print(f"Stored {len(cleaned_products_data)} products for search query: {query}")
    return search_id

# Check if search results already exist in database
async def get_recent_search(query: str):
    # Check for recent searches (within last 24 hours)
    time_24h_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    
    response = supabase_client.table("searches") \
        .select("id, query, timestamp") \
        .eq("query", query) \
        .gte("timestamp", time_24h_ago) \
        .order("timestamp", desc=True) \
        .limit(1) \
        .execute()
    
    if response.data and len(response.data) > 0:
        search_id = response.data[0]["id"]
        
        # Get products for this search
        products_response = supabase_client.table("products") \
            .select("*") \
            .eq("search_id", search_id) \
            .execute()
        
        if products_response.data and len(products_response.data) > 0:
            return {
                "search_id": search_id,
                "results": products_response.data,
                "timestamp": response.data[0]["timestamp"],
                "query": query
            }
    
    return None

# API endpoints
@app.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest, background_tasks: BackgroundTasks):
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # Check cache first
    cache_key = query.lower()
    if cache_key in search_cache:
        cached_data, timestamp = search_cache[cache_key]
        # Check if cache is still valid
        if time.time() - timestamp < CACHE_EXPIRY:
            print(f"Returning cached results for '{query}'")
            return cached_data
    
    # Check if we have recent results in the database
    recent_search = await get_recent_search(query)
    if recent_search:
        print(f"Returning recent search results from database for '{query}'")
        # Update cache
        search_cache[cache_key] = (recent_search, time.time())
        return recent_search
    
    # Run scraper to get fresh results
    print(f"Running scraper for '{query}'")
    df = scraper.search_products(query)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No products found")
    
    # Convert DataFrame to list of dictionaries
    results = df.to_dict('records')
    
    # Store results in database as a background task
    search_id = await store_search_results(query, results)
    
    # Format the response
    response_data = {
        "search_id": search_id,
        "results": results,
        "timestamp": datetime.now().isoformat(),
        "query": query
    }
    
    # Update cache
    search_cache[cache_key] = (response_data, time.time())
    
    return response_data

@app.get("/search/{search_id}", response_model=SearchResponse)
async def get_search_by_id(search_id: int):
    # Get search record
    search_response = supabase_client.table("searches") \
        .select("*") \
        .eq("id", search_id) \
        .limit(1) \
        .execute()
    
    if not search_response.data or len(search_response.data) == 0:
        raise HTTPException(status_code=404, detail="Search not found")
    
    search_data = search_response.data[0]
    
    # Get products for this search
    products_response = supabase_client.table("products") \
        .select("*") \
        .eq("search_id", search_id) \
        .execute()
    
    # Format the response
    response_data = {
        "search_id": search_id,
        "results": products_response.data,
        "timestamp": search_data["timestamp"],
        "query": search_data["query"]
    }
    
    return response_data

@app.get("/recent-searches", response_model=List[dict])
async def get_recent_searches(limit: int = Query(10, ge=1, le=50)):
    response = supabase_client.table("searches") \
        .select("id, query, timestamp, result_count") \
        .order("timestamp", desc=True) \
        .limit(limit) \
        .execute()
    
    return response.data

@app.on_event("startup")
async def startup_event():
    # Create tables if they don't exist
    # In practice, you would use database migrations for this
    # This is just a simple example
    try:
        # Check if tables exist
        searches_exists = supabase_client.table("searches").select("id").limit(1).execute()
        products_exists = supabase_client.table("products").select("id").limit(1).execute()
    except Exception as e:
        print(f"Tables might not exist yet: {e}")
        # You would implement proper table creation here
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)