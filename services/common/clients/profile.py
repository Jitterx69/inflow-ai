import httpx
from typing import Dict, Any, Optional

class ProfileServiceError(Exception):
    """Base exception for profile service errors."""
    pass

class ProfileNotFoundError(ProfileServiceError):
    """Raised when a profile is not found."""
    pass

class ProfileClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(2.0)  # Hard timeout of 2.0s

    async def get_creator_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Fetches a creator profile by user_id.
        """
        url = f"{self.base_url}/profiles/{user_id}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise ProfileNotFoundError(f"Profile {user_id} not found")
                else:
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                raise ProfileServiceError(f"Timeout connecting to Profile Service for {user_id}")
            except httpx.HTTPStatusError as e:
                 raise ProfileServiceError(f"Profile Service Error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise ProfileServiceError(f"Connection error to Profile Service: {e}")
            except Exception as e:
                 # Catch-all re-raise to ensure custom exception type if needed, or just let it bubble
                 if isinstance(e, ProfileServiceError):
                     raise e
                 raise ProfileServiceError(f"Unexpected error: {e}")
