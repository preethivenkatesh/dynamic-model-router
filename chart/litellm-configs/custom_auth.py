from fastapi import Request
from litellm.proxy._types import UserAPIKeyAuth

async def user_api_key_auth(request: Request, api_key: str) -> UserAPIKeyAuth: 
    api_key="noneneeded"
    return UserAPIKeyAuth(api_key=api_key)
