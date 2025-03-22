from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
import logging
from ..models.product import SearchRequest, SearchResponse, ProductReponse
from ..services.product_services import ProductService
from datetime import datetime

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)

# Rate limiter middleware could be added here
@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_products(
    request: SearchRequest,
    product_service: ProductService = Depends(lambda: ProductService())
):
    """
    Search for products across multiple e-commerce platforms
    """
    try:
        # Validate and sanitize the query
        query = request.query.strip()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Search query cannot be empty"
            )
        
        # Call the search function (NO await, because it returns a DataFrame)
        products = await product_service.search_and_save_products(query)
        print(f"Type of products: {type(products)}")  # Debugging
        
        # If format_products_for_response is async, keep `await`, otherwise remove it
        formatted_products = await product_service.format_products_for_response(products)

        return SearchResponse(
            query=query,
            timestamp=datetime.now(),
            products=formatted_products
        )
    
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching products: {str(e)}"
        )
