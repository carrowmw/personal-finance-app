class PlaidService:
    def __init__(self, api_client):
        self.api_client = api_client
        
    async def create_link_token(self):
        return await self.api_client.fetch('/api/create_link_token')
        
    async def exchange_public_token(self, public_token):
        return await self.api_client.fetch(
            '/api/exchange_public_token',
            method='POST',
            data={'public_token': public_token}
        ) 