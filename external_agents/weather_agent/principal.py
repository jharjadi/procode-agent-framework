"""
Weather Principal Agent - Provides weather information using real API data.

This is a simple pattern agent (all-in-one) that handles all weather queries
directly without delegating to task agents.

Uses OpenWeatherMap API for real weather data.
"""

import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from external_agents.shared.base_agent import BaseExternalAgent
from external_agents.shared.agent_config import AgentConfig
from external_agents.shared.agent_utils import extract_location


class WeatherPrincipal(BaseExternalAgent):
    """
    Principal Agent for Weather services (Simple Pattern).
    
    Handles all weather queries directly:
    - Current weather
    - Weather forecast
    - Weather alerts
    - Historical data (if available)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Weather Principal Agent.
        
        Args:
            config_path: Path to configuration file
        """
        super().__init__(agent_name="weather_principal")
        
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = AgentConfig(config_path)
        
        # Get API key from environment
        self.api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        
        # API configuration
        self.base_url = self.config.get("weather_api.base_url", "https://api.openweathermap.org/data/2.5")
        self.units = self.config.get("weather_api.default_units", "metric")
        
        # Simple cache for weather data
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.cache_ttl = self.config.get("weather_api.cache_ttl_seconds", 300)
        
        self.logger.info(f"Weather Principal Agent initialized (API key: {'✓' if self.api_key else '✗'})")
    
    async def _process_request(
        self,
        text: str,
        context: RequestContext,
        event_queue: EventQueue
    ) -> Optional[str]:
        """
        Process weather request.
        
        Args:
            text: User input text
            context: Request context
            event_queue: Event queue for responses
            
        Returns:
            Weather information as formatted string
        """
        try:
            text_lower = text.lower()
            
            # Extract location from text
            location = extract_location(text)
            if not location:
                # Try to find location in common patterns
                location = self._extract_location_fallback(text)
            
            if not location:
                return self._get_help_message()
            
            # Determine what type of weather info is requested
            if any(keyword in text_lower for keyword in ["forecast", "next", "tomorrow", "week"]):
                return await self._get_forecast(location)
            elif any(keyword in text_lower for keyword in ["alert", "warning", "severe"]):
                return await self._get_alerts(location)
            else:
                # Default to current weather
                return await self._get_current_weather(location)
                
        except Exception as e:
            self.logger.error(f"Error processing weather request: {e}", exc_info=True)
            return self._format_error(e)
    
    def _extract_location_fallback(self, text: str) -> Optional[str]:
        """Fallback location extraction for common patterns."""
        # Remove common question words using word boundaries
        import re
        text_lower = text.lower()
        
        # Remove question patterns
        text_lower = re.sub(r'\b(what\'?s|what\s+is|show\s+me|tell\s+me|get\s+me)\b', '', text_lower)
        text_lower = re.sub(r'\b(the|weather|forecast|temperature)\b', '', text_lower)
        text_lower = re.sub(r'\b(in|at|for|of)\s+', '', text_lower)
        text_lower = re.sub(r'\b(today|tomorrow|now)\b', '', text_lower)
        
        # Clean up and capitalize
        location = text_lower.strip().strip("?!.,")
        location = re.sub(r'\s+', ' ', location)  # Remove extra spaces
        
        if location and len(location) > 2:
            return location.title()
        
        return None
    
    async def _get_current_weather(self, location: str) -> str:
        """
        Get current weather for a location.
        
        Args:
            location: City name or location
            
        Returns:
            Formatted weather information
        """
        # Check cache first
        cache_key = f"current:{location.lower()}"
        if cache_key in self.cache:
            data, cached_at = self.cache[cache_key]
            if (datetime.now() - cached_at).total_seconds() < self.cache_ttl:
                self.logger.info(f"Using cached weather data for {location}")
                return self._format_current_weather(data, from_cache=True)
        
        # Check if API key is available
        if not self.api_key:
            return self._get_mock_current_weather(location)
        
        # Fetch from API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": location,
                        "appid": self.api_key,
                        "units": self.units
                    },
                    timeout=10.0
                )
                
                if response.status_code == 404:
                    return f"❌ Location '{location}' not found. Please check the spelling and try again."
                elif response.status_code == 401:
                    self.logger.warning("Invalid API key, falling back to mock data")
                    return self._get_mock_current_weather(location)
                
                response.raise_for_status()
                data = response.json()
                
                # Cache the result
                self.cache[cache_key] = (data, datetime.now())
                
                return self._format_current_weather(data)
                
        except httpx.TimeoutException:
            return "❌ Weather service timeout. Please try again."
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching weather: {e}")
            return f"❌ Error fetching weather data: {e}"
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._get_mock_current_weather(location)
    
    async def _get_forecast(self, location: str) -> str:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name or location
            
        Returns:
            Formatted forecast information
        """
        # Check cache
        cache_key = f"forecast:{location.lower()}"
        if cache_key in self.cache:
            data, cached_at = self.cache[cache_key]
            if (datetime.now() - cached_at).total_seconds() < self.cache_ttl:
                return self._format_forecast(data, from_cache=True)
        
        # Check if API key is available
        if not self.api_key:
            return self._get_mock_forecast(location)
        
        # Fetch from API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "q": location,
                        "appid": self.api_key,
                        "units": self.units,
                        "cnt": 8  # 8 forecasts (24 hours, 3-hour intervals)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 404:
                    return f"❌ Location '{location}' not found."
                elif response.status_code == 401:
                    return self._get_mock_forecast(location)
                
                response.raise_for_status()
                data = response.json()
                
                # Cache the result
                self.cache[cache_key] = (data, datetime.now())
                
                return self._format_forecast(data)
                
        except Exception as e:
            self.logger.error(f"Error fetching forecast: {e}")
            return self._get_mock_forecast(location)
    
    async def _get_alerts(self, location: str) -> str:
        """Get weather alerts for a location."""
        # Weather alerts require OneCall API (paid tier)
        return f"""⚠️ **Weather Alerts for {location}**

Weather alerts require a premium API subscription.

**Alternative Options:**
• Check current weather conditions
• View the forecast for severe weather indicators
• Visit your local weather service website

💡 Try: "What's the weather in {location}?" """
    
    def _format_current_weather(self, data: Dict[str, Any], from_cache: bool = False) -> str:
        """Format current weather data."""
        try:
            location = data["name"]
            country = data["sys"]["country"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind_speed = data["wind"]["speed"]
            description = data["weather"][0]["description"].title()
            icon = data["weather"][0]["main"]
            
            # Map weather icons to emojis
            emoji_map = {
                "Clear": "☀️",
                "Clouds": "☁️",
                "Rain": "🌧️",
                "Drizzle": "🌦️",
                "Thunderstorm": "⛈️",
                "Snow": "❄️",
                "Mist": "🌫️",
                "Fog": "🌫️"
            }
            emoji = emoji_map.get(icon, "🌤️")
            
            cache_note = " (cached)" if from_cache else ""
            
            result = f"""{emoji} **Current Weather in {location}, {country}**{cache_note}

**Conditions:** {description}
**Temperature:** {temp}°C (feels like {feels_like}°C)
**Humidity:** {humidity}%
**Pressure:** {pressure} hPa
**Wind Speed:** {wind_speed} m/s

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💡 Want more? Ask for the forecast!"""
            
            return result
            
        except KeyError as e:
            self.logger.error(f"Missing key in weather data: {e}")
            return "❌ Error parsing weather data"
    
    def _format_forecast(self, data: Dict[str, Any], from_cache: bool = False) -> str:
        """Format forecast data."""
        try:
            location = data["city"]["name"]
            country = data["city"]["country"]
            forecasts = data["list"][:8]  # Next 24 hours
            
            cache_note = " (cached)" if from_cache else ""
            
            result = f"""📅 **24-Hour Forecast for {location}, {country}**{cache_note}\n\n"""
            
            for forecast in forecasts:
                dt = datetime.fromtimestamp(forecast["dt"])
                temp = forecast["main"]["temp"]
                description = forecast["weather"][0]["description"].title()
                
                result += f"**{dt.strftime('%H:%M')}** - {temp}°C, {description}\n"
            
            result += f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return result
            
        except KeyError as e:
            self.logger.error(f"Missing key in forecast data: {e}")
            return "❌ Error parsing forecast data"
    
    def _get_mock_current_weather(self, location: str) -> str:
        """Return mock weather data when API is unavailable."""
        return f"""🌤️ **Current Weather in {location}** (Demo Data)

**Conditions:** Partly Cloudy
**Temperature:** 22°C (feels like 21°C)
**Humidity:** 65%
**Pressure:** 1013 hPa
**Wind Speed:** 3.5 m/s

⚠️ **Note:** This is demo data. To get real weather information:
1. Sign up for a free API key at https://openweathermap.org/api
2. Set the OPENWEATHER_API_KEY environment variable
3. Restart the weather agent

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""
    
    def _get_mock_forecast(self, location: str) -> str:
        """Return mock forecast data when API is unavailable."""
        return f"""📅 **24-Hour Forecast for {location}** (Demo Data)

**12:00** - 22°C, Partly Cloudy
**15:00** - 24°C, Sunny
**18:00** - 21°C, Partly Cloudy
**21:00** - 18°C, Clear
**00:00** - 16°C, Clear
**03:00** - 15°C, Clear
**06:00** - 14°C, Partly Cloudy
**09:00** - 17°C, Partly Cloudy

⚠️ **Note:** This is demo data. Set OPENWEATHER_API_KEY for real forecasts.

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def _get_help_message(self) -> str:
        """Return help message when location is not provided."""
        return """🌤️ **Weather Information Service**

I can provide weather information for any location worldwide!

**Examples:**
• "What's the weather in Melbourne?"
• "Show me the forecast for Sydney"
• "Weather in Tokyo"
• "Is it raining in London?"

**Available Information:**
• Current weather conditions
• 24-hour forecast
• Temperature, humidity, wind speed
• Weather descriptions

💡 **Tip:** Just mention a city name and I'll get the weather for you!

🔑 **API Setup:**
For real weather data, set the OPENWEATHER_API_KEY environment variable.
Get a free key at: https://openweathermap.org/api"""
