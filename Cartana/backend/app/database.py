from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

#set up supabase interface
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

#async function to get recent searches

async def get_recent_searches(limit: int = 10):
    response = supabase.table("searches").select("*").order("created_at", desc=True).limit(limit).execute()
    return response.data


#save product results to database

async def save_product_results(query: str, products: list):
    #we save the search query first
    search_data = {"query": query, "results_count": len(products)}
    search_response = supabase.table("searches").insert(search_data).execute()
    search_id = search_response.data[0]["id"] if search_response.data else None

    if search_id and products:

        for product in products:
            product["search_id"] = search_id

        product_response = supabase.table("products").insert(products).execute()
        return product_response.data
    
    return []


async def get_products_by_query(query: str):

    search_response = supabase.table("searches").select("id").eq("query", query).order("created_at", desc=True).limit(1).execute()

    if search_response.data:
        search_id = search_response.data[0]["id"]

        products_response = supabase.table("product").select("*").eq("search_id", search_id).execute()
        return products_response.data
    
    return []
    

