import os
import time
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class TicketTool:
    """
    Ticket tool with support for both mocked and real GitHub Issues integration.
    """
    
    def __init__(self, use_real: bool = None):
        """
        Initialize the ticket tool.
        
        Args:
            use_real: If True, use real GitHub API. If False, use mocked responses.
                     If None, check USE_REAL_TOOLS environment variable (default: False)
        """
        if use_real is None:
            use_real = os.getenv("USE_REAL_TOOLS", "false").lower() == "true"
        
        self.use_real = use_real
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO")  # Format: "owner/repo"
        
        if self.use_real:
            if not self.github_token:
                print("Warning: GITHUB_TOKEN not set. Falling back to mocked tools.")
                self.use_real = False
            elif not self.github_repo:
                print("Warning: GITHUB_REPO not set. Falling back to mocked tools.")
                self.use_real = False
            else:
                print(f"✓ Using real GitHub Issues API for repository: {self.github_repo}")
    
    def create_ticket(self, title: str, description: str = "", labels: list = None) -> Dict[str, Any]:
        """
        Create a support ticket.
        
        Args:
            title: Ticket title
            description: Ticket description
            labels: List of labels to apply
            
        Returns:
            Dictionary with ticket information
        """
        if self.use_real:
            return self._create_github_issue(title, description, labels or [])
        else:
            return self._create_mocked_ticket(title, description, labels or [])
    
    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Get ticket information.
        
        Args:
            ticket_id: Ticket ID (issue number for GitHub)
            
        Returns:
            Dictionary with ticket information
        """
        if self.use_real:
            return self._get_github_issue(ticket_id)
        else:
            return self._get_mocked_ticket(ticket_id)
    
    def list_tickets(self, state: str = "open") -> list:
        """
        List tickets.
        
        Args:
            state: Ticket state ("open", "closed", "all")
            
        Returns:
            List of ticket dictionaries
        """
        if self.use_real:
            return self._list_github_issues(state)
        else:
            return self._list_mocked_tickets(state)
    
    # Mocked implementations
    
    def _create_mocked_ticket(self, title: str, description: str, labels: list) -> Dict[str, Any]:
        """Create a mocked ticket."""
        return {
            "id": "MOCK-001",
            "title": title,
            "description": description,
            "labels": labels,
            "status": "open",
            "url": "https://example.com/tickets/MOCK-001",
            "created_at": "2024-01-01T00:00:00Z",
            "mocked": True
        }
    
    def _get_mocked_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get a mocked ticket."""
        return {
            "id": ticket_id,
            "title": "Mocked Ticket",
            "description": "This is a mocked ticket",
            "labels": ["support"],
            "status": "open",
            "url": f"https://example.com/tickets/{ticket_id}",
            "created_at": "2024-01-01T00:00:00Z",
            "mocked": True
        }
    
    def _list_mocked_tickets(self, state: str) -> list:
        """List mocked tickets."""
        return [
            {
                "id": "MOCK-001",
                "title": "First mocked ticket",
                "status": state,
                "url": "https://example.com/tickets/MOCK-001",
                "mocked": True
            },
            {
                "id": "MOCK-002",
                "title": "Second mocked ticket",
                "status": state,
                "url": "https://example.com/tickets/MOCK-002",
                "mocked": True
            }
        ]
    
    # Real GitHub API implementations
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    def _create_github_issue(self, title: str, description: str, labels: list) -> Dict[str, Any]:
        """Create a real GitHub issue."""
        url = f"https://api.github.com/repos/{self.github_repo}/issues"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        data = {
            "title": title,
            "body": description,
            "labels": labels
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()
                issue = response.json()
                
                return {
                    "id": str(issue["number"]),
                    "title": issue["title"],
                    "description": issue["body"] or "",
                    "labels": [label["name"] for label in issue.get("labels", [])],
                    "status": issue["state"],
                    "url": issue["html_url"],
                    "created_at": issue["created_at"],
                    "mocked": False
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("GitHub authentication failed. Check your GITHUB_TOKEN.")
            elif e.response.status_code == 404:
                raise ValueError(f"Repository not found: {self.github_repo}")
            elif e.response.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded or insufficient permissions.")
            else:
                raise ValueError(f"GitHub API error: {e.response.status_code} - {e.response.text}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    def _get_github_issue(self, issue_number: str) -> Dict[str, Any]:
        """Get a real GitHub issue."""
        url = f"https://api.github.com/repos/{self.github_repo}/issues/{issue_number}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                issue = response.json()
                
                return {
                    "id": str(issue["number"]),
                    "title": issue["title"],
                    "description": issue["body"] or "",
                    "labels": [label["name"] for label in issue.get("labels", [])],
                    "status": issue["state"],
                    "url": issue["html_url"],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "mocked": False
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Issue #{issue_number} not found in {self.github_repo}")
            else:
                raise ValueError(f"GitHub API error: {e.response.status_code}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    def _list_github_issues(self, state: str = "open") -> list:
        """List real GitHub issues."""
        url = f"https://api.github.com/repos/{self.github_repo}/issues"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        params = {
            "state": state,
            "per_page": 10  # Limit to 10 most recent
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                issues = response.json()
                
                return [
                    {
                        "id": str(issue["number"]),
                        "title": issue["title"],
                        "status": issue["state"],
                        "url": issue["html_url"],
                        "created_at": issue["created_at"],
                        "mocked": False
                    }
                    for issue in issues
                ]
        except httpx.HTTPStatusError as e:
            raise ValueError(f"GitHub API error: {e.response.status_code}")
    
    async def create_ticket_streaming(
        self,
        title: str,
        description: str = "",
        labels: list = None
    ) -> AsyncGenerator[tuple[str, Optional[Dict[str, Any]]], None]:
        """
        Create a ticket with streaming progress updates.
        
        Args:
            title: Ticket title
            description: Ticket description
            labels: List of labels to apply
            
        Yields:
            Tuples of (progress_message, result). Final yield contains the result.
        """
        yield ("🔍 Preparing ticket creation...", None)
        await asyncio.sleep(0.1)
        
        if self.use_real:
            yield (f"📡 Connecting to GitHub API ({self.github_repo})...", None)
            await asyncio.sleep(0.1)
        else:
            yield ("📝 Creating mocked ticket...", None)
            await asyncio.sleep(0.1)
        
        # Execute the actual creation
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.create_ticket,
                title,
                description,
                labels
            )
            
            if result.get("mocked"):
                yield (f"✅ Ticket created (mocked): {result['id']}", result)
            else:
                yield (f"✅ Ticket created: Issue #{result['id']}", result)
        except Exception as e:
            yield (f"❌ Error creating ticket: {str(e)}", None)
    
    async def get_ticket_streaming(
        self,
        ticket_id: str
    ) -> AsyncGenerator[tuple[str, Optional[Dict[str, Any]]], None]:
        """
        Get ticket with streaming progress updates.
        
        Args:
            ticket_id: Ticket ID
            
        Yields:
            Tuples of (progress_message, result). Final yield contains the result.
        """
        yield (f"🔍 Fetching ticket {ticket_id}...", None)
        await asyncio.sleep(0.1)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.get_ticket, ticket_id)
            yield (f"✅ Ticket retrieved: {result['title']}", result)
        except Exception as e:
            yield (f"❌ Error fetching ticket: {str(e)}", None)
    
    async def list_tickets_streaming(
        self,
        state: str = "open"
    ) -> AsyncGenerator[tuple[str, Optional[list]], None]:
        """
        List tickets with streaming progress updates.
        
        Args:
            state: Ticket state
            
        Yields:
            Tuples of (progress_message, result). Final yield contains the result.
        """
        yield (f"🔍 Fetching {state} tickets...", None)
        await asyncio.sleep(0.1)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.list_tickets, state)
            yield (f"✅ Found {len(result)} tickets", result)
        except Exception as e:
            yield (f"❌ Error listing tickets: {str(e)}", None)


# Legacy function for backward compatibility
def mock_ticket_tool(action: str, params: Dict[str, Any]) -> str:
    """
    Legacy mocked ticket tool function.
    Kept for backward compatibility with existing tests.
    """
    return f"Mocked ticket tool: action={action}, params={params}"
