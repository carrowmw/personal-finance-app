# application/frontend/src/services/api_client.py
import aiohttp
import logging
import json

from application.backend.src.config import BackendConfig as Config

class APIClient:
    def __init__(self):
        self.base_url = Config.API_URL
        self.logger = logging.getLogger(__name__)
        
    async def fetch(self, endpoint, method='GET', data=None):
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            # Add any auth headers here
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                    cookies=None  # Session cookies will be handled automatically
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"API Error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise 