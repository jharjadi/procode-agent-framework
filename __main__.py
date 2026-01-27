import os
import uvicorn
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, Message
from core.agent_router import ProcodeAgentRouter
from core.custom_request_handler import MetadataTrackingRequestHandler
from core.metadata_middleware import MetadataMiddleware
from security.api_security import APISecurityMiddleware, get_allowed_origins
import json

# Import API key authentication components (optional)
try:
    from core.api_key_middleware import APIKeyMiddleware
    from api.admin_api_keys import admin_routes
    API_KEY_AUTH_AVAILABLE = True
except ImportError:
    API_KEY_AUTH_AVAILABLE = False
    print("⚠️  API Key authentication not available (missing dependencies)")

if __name__ == "__main__":
    print("Starting Procode Agent...", flush=True)
    print(f"ENABLE_API_SECURITY={os.getenv('ENABLE_API_SECURITY', 'NOT SET')}", flush=True)
    print(f"DEMO_API_KEY={'SET' if os.getenv('DEMO_API_KEY') else 'NOT SET'}", flush=True)
    
    # Define skills for the principal agent
    tickets_skill = AgentSkill(
        id="tickets",
        name="Tickets",
        description="Handle ticket-related tasks",
        tags=["tickets"],
        examples=["create ticket", "get ticket status"],
    )
    account_skill = AgentSkill(
        id="account",
        name="Account",
        description="Handle account-related tasks",
        tags=["account"],
        examples=["get account info"],
    )
    payments_skill = AgentSkill(
        id="payments",
        name="Payments",
        description="Handle payment-related tasks (stubbed/refused)",
        tags=["payments"],
        examples=["make payment"],
    )

    agent_card = AgentCard(
        name="Procode Principal Agent",
        description="Routes requests to task agents: tickets, account, payments (stubbed)",
        url="http://localhost:9998/",
        version="0.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[tickets_skill, account_skill, payments_skill],
        supports_authenticated_extended_card=False,
    )

    # Create agent router instance (shared for middleware and handler)
    agent_router = ProcodeAgentRouter()
    
    # Use custom request handler that tracks and returns classification metadata
    request_handler = MetadataTrackingRequestHandler(
        agent_executor=agent_router,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    # Define streaming endpoint handler
    async def stream_endpoint(request: Request):
        """
        Streaming endpoint for real-time response delivery.
        
        Accepts a message and streams the response using Server-Sent Events (SSE).
        """
        try:
            # Parse request body
            body = await request.json()
            
            # Create a simple request context
            class SimpleRequestContext:
                def __init__(self, message_data):
                    # Parse message from request
                    if isinstance(message_data, dict):
                        self.message = Message(**message_data)
                    else:
                        self.message = message_data
                    self.task_id = body.get("task_id", "stream-task")
            
            context = SimpleRequestContext(body.get("message", {}))
            
            # Create router instance
            router = ProcodeAgentRouter()
            
            # Stream generator
            async def generate():
                try:
                    async for part in router.execute_streaming(context):
                        # Format as SSE
                        if hasattr(part, 'text'):
                            data = {"text": part.text}
                        else:
                            data = {"text": str(part)}
                        
                        yield f"data: {json.dumps(data)}\n\n"
                except Exception as e:
                    error_data = {"error": str(e)}
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        except Exception as e:
            return StreamingResponse(
                iter([f"data: {json.dumps({'error': str(e)})}\n\n"]),
                media_type="text/event-stream"
            )
    
    # Build the base app
    app = server.build()
    
    # Add metadata middleware to inject classification metadata into responses
    # This must be added FIRST so it executes LAST (after CORS)
    print("Adding Metadata Middleware...")
    app.add_middleware(MetadataMiddleware, agent_router=agent_router)
    print("Metadata Middleware added")
    
    # Add CORS middleware to allow frontend requests
    # Get allowed origins from environment (supports production domain restriction)
    # NOTE: Middleware is executed in REVERSE order (LIFO)
    allowed_origins = get_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add security middleware (rate limiting + API key validation)
    # Added AFTER CORS so it executes BEFORE CORS (reverse order)
    print("Adding API Security Middleware...")
    app.add_middleware(APISecurityMiddleware)
    print("API Security Middleware added")
    
    # Add API Key authentication middleware (optional, controlled by env var)
    enable_api_key_auth = os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
    
    if enable_api_key_auth and API_KEY_AUTH_AVAILABLE:
        print("Adding API Key Authentication Middleware...")
        
        # Define public paths that don't require API key
        public_paths = [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/stream"  # Keep streaming endpoint public for now
        ]
        
        app.add_middleware(
            APIKeyMiddleware,
            public_paths=public_paths
        )
        print("✓ API Key Authentication Middleware added")
        
        # Add admin routes for API key management
        for route in admin_routes:
            app.routes.append(route)
        print(f"✓ Added {len(admin_routes)} admin routes")
    else:
        if enable_api_key_auth:
            print("⚠️  API Key authentication enabled but not available")
        else:
            print("ℹ️  API Key authentication disabled (set ENABLE_API_KEY_AUTH=true to enable)")
    
    # Add custom streaming route to the Starlette app
    app.routes.append(Route("/stream", stream_endpoint, methods=["POST"]))

    uvicorn.run(app, host="0.0.0.0", port=9998)
