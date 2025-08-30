"""
Overseerr API request management functionality.
Handles fetching, approving, and rejecting media requests with enhanced error handling.
"""
import logging
import requests
from typing import Optional, List, Dict, Any, Tuple
from requests.exceptions import RequestException, Timeout, ConnectionError

from config.constants import OVERSEERR_API_URL, OVERSEERR_API_KEY
from utils.error_handler import with_retry, safe_api_call, ErrorHandler

logger = logging.getLogger(__name__)


class RequestManager:
    """Manages Overseerr API calls for request approval/rejection."""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """Initialize with Overseerr API configuration."""
        self.api_url = api_url or OVERSEERR_API_URL
        self.api_key = api_key or OVERSEERR_API_KEY
        
        if not self.api_url or not self.api_key:
            logger.error(f"Missing Overseerr configuration: URL={bool(self.api_url)}, KEY={bool(self.api_key)}")
            raise ValueError("Overseerr API URL and API Key are required")
        
        logger.info(f"RequestManager initialized with URL: {self.api_url}")
    
    @with_retry(max_attempts=4, delay=2.0)  # Increased retries for first-time connection reliability
    @safe_api_call("fetch pending requests")
    def get_pending_requests(self, page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
        """
        Fetch pending requests from Overseerr API with retry logic and error handling.
        
        Args:
            page: Page number for pagination (default: 1)
            page_size: Number of results per page (default: 20)
            
        Returns:
            Dict containing request results and pagination info, or None on error
        """
        # Handle API URL properly - check if it already includes /api/v1
        base_url = self.api_url.rstrip('/')
        if base_url.endswith('/api/v1'):
            api_endpoint = f"{base_url}/request"
        else:
            api_endpoint = f"{base_url}/api/v1/request"
            
        params = {
            'filter': 'pending',
            'take': page_size,
            'skip': (page - 1) * page_size
        }
        
        logger.debug(f"Fetching pending requests from: {api_endpoint}")
        response = requests.get(
            api_endpoint,
            headers={"X-Api-Key": self.api_key},
            params=params,
            timeout=30  # Increased timeout to 30 seconds for better first-time connection reliability
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched {len(data.get('results', []))} pending requests")
        return data

    
    @with_retry(max_attempts=2, delay=1.5)
    @safe_api_call("approve request")
    def approve_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Approve a request via Overseerr API with enhanced error handling.
        
        Args:
            request_id: The ID of the request to approve
            
        Returns:
            Dict containing the updated request data, or None on error
        """
        # Handle API URL properly
        base_url = self.api_url.rstrip('/')
        if base_url.endswith('/api/v1'):
            api_endpoint = f"{base_url}/request/{request_id}/approve"
        else:
            api_endpoint = f"{base_url}/api/v1/request/{request_id}/approve"
        
        logger.info(f"Approving request {request_id}")
        response = requests.post(
            api_endpoint,
            headers={"X-Api-Key": self.api_key},
            timeout=15  # Increased timeout for approval operations
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully approved request {request_id}")
        return data
    
    @with_retry(max_attempts=2, delay=1.5)
    @safe_api_call("reject request")
    def reject_request(self, request_id: int, reason: str = None) -> Optional[Dict[str, Any]]:
        """
        Reject (decline) a request via Overseerr API with enhanced error handling.
        
        Args:
            request_id: The ID of the request to reject
            reason: Optional reason for rejection
            
        Returns:
            Dict containing the updated request data, or None on error
        """
        # Handle API URL properly
        base_url = self.api_url.rstrip('/')
        if base_url.endswith('/api/v1'):
            api_endpoint = f"{base_url}/request/{request_id}/decline"
        else:
            api_endpoint = f"{base_url}/api/v1/request/{request_id}/decline"
        
        # Include reason in request body if provided
        data = {}
        if reason:
            data['reason'] = reason
        
        logger.info(f"Rejecting request {request_id}" + (f" with reason: {reason}" if reason else ""))
        response = requests.post(
            api_endpoint,
            headers={"X-Api-Key": self.api_key},
            json=data if data else None,
            timeout=15  # Increased timeout for rejection operations
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Successfully rejected request {request_id}")
        return result
    
    def get_request_details(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific request.
        
        Args:
            request_id: The ID of the request to fetch
            
        Returns:
            Dict containing request details, or None on error
        """
        try:
            base_url = self.api_url.rstrip('/')
            if base_url.endswith('/api/v1'):
                api_endpoint = f"{base_url}/request/{request_id}"
            else:
                api_endpoint = f"{base_url}/api/v1/request/{request_id}"
            
            logger.debug(f"Fetching request details for {request_id}")
            response = requests.get(
                api_endpoint,
                headers={"X-Api-Key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching request {request_id}: {e}")
            return None
    @with_retry(max_attempts=2, delay=1.0)
    def get_media_details_from_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed media information from a request object with enhanced error handling.
        Uses the existing search/media endpoints to get complete details.
        
        Args:
            request: Request object from Overseerr API
            
        Returns:
            Dict with enhanced media information including title, poster, description
        """
        try:
            media = request.get('media', {})
            tmdb_id = media.get('tmdbId')
            media_type = media.get('mediaType', 'unknown')
            
            if not tmdb_id:
                logger.warning(f"No tmdbId found in request {request.get('id')}")
                return self._create_fallback_media_info(request)
            
            # Use existing API endpoint to get media details
            base_url = self.api_url.rstrip('/')
            if base_url.endswith('/api/v1'):
                if media_type == 'movie':
                    api_endpoint = f"{base_url}/movie/{tmdb_id}"
                elif media_type == 'tv':
                    api_endpoint = f"{base_url}/tv/{tmdb_id}"
                else:
                    logger.warning(f"Unknown media type: {media_type}")
                    return self._create_fallback_media_info(request)
            else:
                if media_type == 'movie':
                    api_endpoint = f"{base_url}/api/v1/movie/{tmdb_id}"
                elif media_type == 'tv':
                    api_endpoint = f"{base_url}/api/v1/tv/{tmdb_id}"
                else:
                    logger.warning(f"Unknown media type: {media_type}")
                    return self._create_fallback_media_info(request)
            
            logger.debug(f"Fetching media details from: {api_endpoint}")
            response = requests.get(
                api_endpoint,
                headers={"X-Api-Key": self.api_key},
                timeout=12  # Reasonable timeout for media details
            )
            response.raise_for_status()
            
            media_details = response.json()
            
            # Process media details similar to process_search_results
            return self._process_media_details(media_details, request)
            
        except Exception as e:
            logger.error(f"Error fetching media details for request {request.get('id', 'unknown')}: {e}")
            ErrorHandler.log_error("get media details", e, {"request_id": request.get('id')})
            return self._create_fallback_media_info(request)
    
    
    def _process_media_details(self, media_details: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """Process media details into standardized format with poster URL support."""
        media_type = media_details.get('mediaType', request.get('media', {}).get('mediaType', 'unknown'))
        
        # Extract title
        title = (
            media_details.get("title") or 
            media_details.get("name") or 
            media_details.get("originalTitle") or 
            media_details.get("originalName") or 
            "Unknown Title"
        )
        
        # Extract year
        date_key = "firstAirDate" if media_type == "tv" else "releaseDate"
        full_date_str = media_details.get(date_key, "")
        year = full_date_str.split("-")[0] if "-" in full_date_str else "Unknown Year"
        
        # Extract genres for anime detection
        genres = media_details.get("genres", [])
        genre_names = [g.get("name", "") for g in genres]
        
        # Determine if it's anime - check root folder or genres
        is_anime = False
        root_folder = request.get("rootFolder") or ""
        if root_folder and "anime" in root_folder.lower():
            is_anime = True
            media_type = "anime"
        elif any("anime" in genre.lower() for genre in genre_names):
            is_anime = True
            media_type = "anime"
        
        # Build full poster URL from posterPath
        poster_url = None
        poster_path = media_details.get('posterPath')
        if poster_path:
            # TMDB image base URL (w500 size for good quality without being too large)
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        return {
            'request_id': request.get('id'),
            'media_type': media_type,
            'title': title,
            'year': year,
            'poster_path': poster_path,
            'poster_url': poster_url,  # Full URL for Telegram
            'overview': media_details.get('overview', 'No description available'),
            'genres': genre_names,
            'rating': media_details.get('voteAverage', 0),  # TMDB rating
            'runtime': media_details.get('runtime', 0) or media_details.get('episodeRunTime', [0])[0] if media_details.get('episodeRunTime') else 0,
            'requested_by': self._extract_requester_info(request),
            'requested_at': request.get('createdAt'),
            'tmdb_id': media_details.get('id'),
            'is_anime': is_anime
        }
    
    def _create_fallback_media_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback media info when detailed lookup fails."""
        media = request.get('media', {})
        return {
            'request_id': request.get('id'),
            'media_type': media.get('mediaType', 'unknown'),
            'title': 'Unknown Title',
            'year': 'Unknown Year',
            'poster_path': None,
            'poster_url': None,
            'overview': 'Details unavailable',
            'genres': [],
            'rating': 0,
            'runtime': 0,
            'requested_by': self._extract_requester_info(request),
            'requested_at': request.get('createdAt'),
            'tmdb_id': media.get('tmdbId'),
            'is_anime': False
        }
    
    def _extract_requester_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requester information from request data."""
        requested_by = request.get('requestedBy', {})
        return {
            'id': requested_by.get('id'),
            'display_name': requested_by.get('displayName', 'Unknown User'),
            'username': requested_by.get('username', ''),
            'email': requested_by.get('email', '')
        }

    def get_pending_requests_with_details(self, page: int = 1, page_size: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch pending requests with full media details from Overseerr API.
        
        Args:
            page: Page number for pagination (default: 1)
            page_size: Number of results per page (default: 20)
            
        Returns:
            List of requests with full media details, or None on error
        """
        try:
            # First get the pending requests
            pending_data = self.get_pending_requests(page, page_size)
            if not pending_data:
                return None
            
            requests_with_details = []
            results = pending_data.get("results", [])
            
            for request in results:
                try:
                    # Get media details using TMDB ID
                    media = request.get('media', {})
                    tmdb_id = media.get('tmdbId')
                    media_type = request.get('type', 'unknown')  # 'tv' or 'movie'
                    
                    if tmdb_id:
                        media_details = self.get_media_details_by_tmdb(tmdb_id, media_type)
                        if media_details:
                            # Combine request data with media details
                            enhanced_request = {
                                **request,
                                'mediaDetails': media_details
                            }
                            requests_with_details.append(enhanced_request)
                        else:
                            # If we can't get details, still include the request but mark it
                            enhanced_request = {
                                **request,
                                'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                            }
                            requests_with_details.append(enhanced_request)
                    else:
                        logger.warning(f"No TMDB ID found for request {request.get('id')}")
                        enhanced_request = {
                            **request,
                            'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                        }
                        requests_with_details.append(enhanced_request)
                        
                except Exception as e:
                    logger.error(f"Error processing request {request.get('id')}: {e}")
                    # Still include the request with minimal info
                    enhanced_request = {
                        **request,
                        'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                    }
                    requests_with_details.append(enhanced_request)
            
            logger.info(f"Enhanced {len(requests_with_details)} requests with media details")
            return requests_with_details
            
        except Exception as e:
            logger.error(f"Error fetching requests with details: {e}")
            return None
    
    def get_media_details_by_tmdb(self, tmdb_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed media information using TMDB ID.
        
        Args:
            tmdb_id: The TMDB ID of the media
            media_type: 'tv' or 'movie'
            
        Returns:
            Dict containing media details, or None on error
        """
        try:
            base_url = self.api_url.rstrip('/')
            if base_url.endswith('/api/v1'):
                endpoint = f"{base_url}/{media_type}/{tmdb_id}"
            else:
                endpoint = f"{base_url}/api/v1/{media_type}/{tmdb_id}"
            
            logger.debug(f"Fetching media details: {endpoint}")
            response = requests.get(
                endpoint,
                headers={"X-Api-Key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching media details for TMDB ID {tmdb_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching media details for TMDB ID {tmdb_id}: {e}")
            return None


# Convenience functions for backward compatibility
def get_pending_requests(page: int = 1, page_size: int = 20) -> Optional[Dict[str, Any]]:
    """Get pending requests using default configuration."""
    manager = RequestManager()
    return manager.get_pending_requests(page, page_size)


def approve_request(request_id: int) -> Optional[Dict[str, Any]]:
    """Approve a request using default configuration."""
    manager = RequestManager()
    return manager.approve_request(request_id)


def reject_request(request_id: int, reason: str = None) -> Optional[Dict[str, Any]]:
    """Reject a request using default configuration."""
    manager = RequestManager()
    return manager.reject_request(request_id, reason)


    def get_pending_requests_with_details(self, page: int = 1, page_size: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch pending requests with full media details from Overseerr API.
        
        Args:
            page: Page number for pagination (default: 1)
            page_size: Number of results per page (default: 20)
            
        Returns:
            List of requests with full media details, or None on error
        """
        try:
            # First get the pending requests
            pending_data = self.get_pending_requests(page, page_size)
            if not pending_data:
                return None
            
            requests_with_details = []
            results = pending_data.get("results", [])
            
            for request in results:
                try:
                    # Get media details using TMDB ID
                    media = request.get('media', {})
                    tmdb_id = media.get('tmdbId')
                    media_type = request.get('type', 'unknown')  # 'tv' or 'movie'
                    
                    if tmdb_id:
                        media_details = self.get_media_details_by_tmdb(tmdb_id, media_type)
                        if media_details:
                            # Combine request data with media details
                            enhanced_request = {
                                **request,
                                'mediaDetails': media_details
                            }
                            requests_with_details.append(enhanced_request)
                        else:
                            # If we can't get details, still include the request but mark it
                            enhanced_request = {
                                **request,
                                'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                            }
                            requests_with_details.append(enhanced_request)
                    else:
                        logger.warning(f"No TMDB ID found for request {request.get('id')}")
                        enhanced_request = {
                            **request,
                            'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                        }
                        requests_with_details.append(enhanced_request)
                        
                except Exception as e:
                    logger.error(f"Error processing request {request.get('id')}: {e}")
                    # Still include the request with minimal info
                    enhanced_request = {
                        **request,
                        'mediaDetails': {'name': 'Unknown Title', 'title': 'Unknown Title'}
                    }
                    requests_with_details.append(enhanced_request)
            
            logger.info(f"Enhanced {len(requests_with_details)} requests with media details")
            return requests_with_details
            
        except Exception as e:
            logger.error(f"Error fetching requests with details: {e}")
            return None
    
    def get_media_details_by_tmdb(self, tmdb_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed media information using TMDB ID.
        
        Args:
            tmdb_id: The TMDB ID of the media
            media_type: 'tv' or 'movie'
            
        Returns:
            Dict containing media details, or None on error
        """
        try:
            base_url = self.api_url.rstrip('/')
            if base_url.endswith('/api/v1'):
                endpoint = f"{base_url}/{media_type}/{tmdb_id}"
            else:
                endpoint = f"{base_url}/api/v1/{media_type}/{tmdb_id}"
            
            logger.debug(f"Fetching media details: {endpoint}")
            response = requests.get(
                endpoint,
                headers={"X-Api-Key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching media details for TMDB ID {tmdb_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching media details for TMDB ID {tmdb_id}: {e}")
            return None
    """Get request details using default configuration."""
    manager = RequestManager()
    return manager.get_request_details(request_id)
