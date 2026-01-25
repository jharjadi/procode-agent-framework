from tasks.tools import TicketTool

class TicketsAgent:
    """Handles ticket-related tasks with real or mocked tool integration."""
    
    def __init__(self):
        self.ticket_tool = TicketTool()
    
    async def invoke(self, context=None):
        # Extract text from context
        text = getattr(context.input, "text", "").strip().lower() if context else ""
        
        # Check conversation history for context
        history = getattr(context.input, "history", []) if context else []
        has_previous_ticket = any(
            "ticket" in msg.get("content", "").lower()
            for msg in history
            if msg.get("role") == "agent"
        )
        
        # Handle follow-up questions
        if has_previous_ticket and ("status" in text or "update" in text or "check" in text):
            # User is asking about a previous ticket
            return "I can see you asked about a ticket earlier. To check ticket status, please provide the ticket ID or issue number."
        
        # Simple intent detection for ticket operations
        if "create" in text or "new" in text or "open" in text:
            # Create a ticket
            result = self.ticket_tool.create_ticket(
                title="Support Request",
                description=f"User request: {text}",
                labels=["support", "auto-created"]
            )
            if result.get("mocked"):
                return f"Ticket processed (mocked). Ticket ID: {result['id']}"
            else:
                return f"Ticket created successfully! Issue #{result['id']}: {result['url']}"
        
        elif "list" in text or "show" in text:
            # List tickets
            tickets = self.ticket_tool.list_tickets(state="open")
            if tickets and tickets[0].get("mocked"):
                return f"Ticket processed (mocked). Found {len(tickets)} tickets."
            else:
                ticket_list = "\n".join([f"- Issue #{t['id']}: {t['title']}" for t in tickets[:5]])
                return f"Found {len(tickets)} open tickets:\n{ticket_list}"
        
        else:
            # Default: create a ticket
            result = self.ticket_tool.create_ticket(
                title="Support Request",
                description=f"User request: {text}",
                labels=["support"]
            )
            if result.get("mocked"):
                return f"Ticket processed (mocked). Ticket ID: {result['id']}"
            else:
                return f"Ticket created successfully! Issue #{result['id']}: {result['url']}"
