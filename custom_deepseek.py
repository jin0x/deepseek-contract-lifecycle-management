import httpx
from typing import Optional

class CustomDeepSeek:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.aimlapi.com/v1"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def generate(self, prompt: str, system_message: str = None) -> str:
        """Send a request to aimlapi.com"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": messages,
            "stream": False
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Error calling aimlapi: {str(e)}")
