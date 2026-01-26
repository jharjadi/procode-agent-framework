"""
Middleware to add classification metadata to JSON-RPC responses.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json


class MetadataMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts JSON-RPC responses and adds classification metadata.
    """
    
    def __init__(self, app, agent_router):
        super().__init__(app)
        self.agent_router = agent_router
    
    async def dispatch(self, request: Request, call_next):
        # Call the next middleware/handler
        response = await call_next(request)
        
        # Only process JSON-RPC responses
        if request.url.path == "/" and request.method == "POST":
            # Read the response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # Parse JSON response
                data = json.loads(body.decode())
                
                # Add metadata if this is a successful result
                if "result" in data and hasattr(self.agent_router, 'intent_classifier'):
                    metadata = self.agent_router.intent_classifier.get_classification_metadata()
                    
                    # Add metadata to the result
                    if isinstance(data["result"], dict):
                        if "metadata" not in data["result"]:
                            data["result"]["metadata"] = {}
                        data["result"]["metadata"].update(metadata)
                    
                    # Return JSONResponse which handles Content-Length properly
                    return JSONResponse(
                        content=data,
                        status_code=response.status_code
                    )
            except (json.JSONDecodeError, AttributeError) as e:
                # If parsing fails, return original response
                print(f"Metadata middleware error: {e}")
                pass
            
            # Return original response if we couldn't modify it
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        return response
