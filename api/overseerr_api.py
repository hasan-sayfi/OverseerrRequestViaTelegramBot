"""
Overseerr API integration functions.
"""
import logging
import requests
import urllib.parse
from typing import Optional, Tuple, List

from config.constants import OVERSEERR_API_URL, OVERSEERR_API_KEY, CURRENT_MODE, BotMode

logger = logging.getLogger(__name__)

###############################################################################
#                      OVERSEERR API: FETCH USERS
###############################################################################

def get_overseerr_users():
    """
    Fetch all Overseerr users via /api/v1/user.
    Returns a list of users or an empty list on error.
    """
    try:
        url = f"{OVERSEERR_API_URL}/user?take=256"
        logger.info(f"Fetching Overseerr users from: {url}")
        response = requests.get(
            url,
            headers={"X-Api-Key": OVERSEERR_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        logger.info(f"Fetched {len(results)} Overseerr users.")
        return results
    except requests.RequestException as e:
        logger.error(f"Error fetching Overseerr users: {e}")
        return []

###############################################################################
#                     OVERSEERR API: SEARCH
###############################################################################

def search_media(media_name: str):
    """
    Search for media by title in Overseerr.
    Returns the JSON result or None on error.
    """
    try:
        logger.info(f"Searching for media: {media_name}")
        query_params = {'query': media_name}
        encoded_query = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
        url = f"{OVERSEERR_API_URL}/search?{encoded_query}"
        response = requests.get(
            url,
            headers={"X-Api-Key": OVERSEERR_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error during media search: {e}")
        return None

def process_search_results(results: list):
    """
    Process Overseerr search results into a simplified list of dicts.
    Each dict contains relevant fields (title, year, mediaType, etc.).
    """
    processed_results = []
    for result in results:
        media_title = (
            result.get("name")
            or result.get("originalName")
            or result.get("title")
            or "Unknown Title"
        )

        date_key = "firstAirDate" if result["mediaType"] == "tv" else "releaseDate"
        full_date_str = result.get(date_key, "")  # e.g. "2024-05-12"

        # Extract just the year from the date (if it exists)
        media_year = full_date_str.split("-")[0] if "-" in full_date_str else "Unknown Year"

        media_info = result.get("mediaInfo", {})
        overseerr_media_id = media_info.get("id")
        hd_status = media_info.get("status", 1)
        uhd_status = media_info.get("status4k", 1)

        processed_results.append({
            "title": media_title,
            "year": media_year,
            "id": result["id"],  # usually the TMDb ID
            "mediaType": result["mediaType"],
            "poster": result.get("posterPath"),
            "description": result.get("overview", "No description available"),
            "overseerr_id": overseerr_media_id,
            "release_date_full": full_date_str,
            "status_hd": hd_status,
            "status_4k": uhd_status
        })

    logger.info(f"Processed {len(results)} search results.")
    return processed_results

###############################################################################
#                     OVERSEERR API: AUTHENTICATION
###############################################################################

def overseerr_login(email: str, password: str) -> str | None:
    """Führt einen Login über die Overseerr-API aus und gibt den Session-Cookie zurück."""
    url = f"{OVERSEERR_API_URL}/auth/local"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        cookie = response.cookies.get("connect.sid")
        logger.info(f"Login erfolgreich für {email}")
        return cookie
    except requests.RequestException as e:
        logger.error(f"Login fehlgeschlagen für {email}: {e}")
        return None

def overseerr_logout(session_cookie: str) -> bool:
    """Führt einen Logout über die Overseerr-API aus."""
    url = f"{OVERSEERR_API_URL}/auth/logout"
    try:
        response = requests.post(
            url,
            headers={"Cookie": f"connect.sid={session_cookie}"},
            timeout=10
        )
        response.raise_for_status()
        logger.info("Logout erfolgreich")
        return True
    except requests.RequestException as e:
        logger.error(f"Logout fehlgeschlagen: {e}")
        return False

def check_session_validity(session_cookie: str) -> bool:
    """Prüft, ob der Session-Cookie gültig ist, indem eine einfache API-Anfrage gestellt wird."""
    url = f"{OVERSEERR_API_URL}/auth/me"
    try:
        response = requests.get(
            url,
            headers={"Cookie": f"connect.sid={session_cookie}"},
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False

###############################################################################
#              OVERSEERR API: REQUEST & ISSUE CREATION
###############################################################################

def request_media(media_id: int, media_type: str, requested_by: int = None, is4k: bool = False, 
                 session_cookie: str = None, seasons: str = "all", serverId: int = None, 
                 rootFolderOverride: str = None) -> Tuple[bool, str]:
    
    payload = {"mediaType": media_type, "mediaId": media_id, "is4k": is4k}
    if requested_by is not None:  # Only in API Mode
        payload["userId"] = requested_by
    
    if media_type == "tv":
        if seasons == "all" or seasons is None:
            payload["seasons"] = "all"
        elif isinstance(seasons, list):
            payload["seasons"] = [int(s) for s in seasons]  # Handle list of seasons
        else:
            payload["seasons"] = [int(seasons)]
    
    # ===== Service routing parameters =====
    if serverId is not None:
        payload["serverId"] = serverId

    if rootFolderOverride is not None:
        payload["rootFolder"] = rootFolderOverride
    # =====================================================

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if session_cookie:
        headers["Cookie"] = f"connect.sid={session_cookie}"
    elif CURRENT_MODE == BotMode.API:
        headers["X-Api-Key"] = OVERSEERR_API_KEY
    else:
        return False, "No authentication provided."

    try:
        response = requests.post(f"{OVERSEERR_API_URL}/request", json=payload, headers=headers, timeout=10)
        logger.info(f"Request response: Status {response.status_code}, Body: {response.text}")
        if response.status_code == 201:
            return True, "Request successful"
        elif response.status_code == 202:
            return True, "Season already requested"
        return False, f"Failed: {response.status_code} - {response.text}"
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return False, f"Error: {str(e)}"

def create_issue(media_id: int, media_type: str, issue_description: str, issue_type: int, 
                user_id: int = None, session_cookie: str = None) -> bool:
    """
    Create an issue on Overseerr via the API.
    Uses session cookies in NORMAL or SHARED mode, or the API key in ADMIN mode.
    """
    # Prepare the payload for the API request
    payload = {
        "mediaId": media_id,
        "mediaType": media_type,
        "issueType": issue_type,
        "message": issue_description,
    }
    if user_id is not None:
        payload["userId"] = user_id

    # Log the payload being sent
    logger.info(f"Sending issue payload to Overseerr: {payload}")

    # Set up headers based on the current mode
    headers = {"Content-Type": "application/json"}
    if session_cookie and CURRENT_MODE != BotMode.API:
        headers["Cookie"] = f"connect.sid={session_cookie}"
    else:
        headers["X-Api-Key"] = OVERSEERR_API_KEY

    # Send the POST request to create the issue
    try:
        response = requests.post(
            f"{OVERSEERR_API_URL}/issue",
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Issue creation successful for mediaId {media_id}.")
        return True
    except requests.RequestException as e:
        logger.error(f"Error during issue creation: {e}")
        if e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return False

###############################################################################
#                     OVERSEERR API: UTILITIES
###############################################################################

def get_latest_version_from_github():
    """
    Check GitHub releases to find the latest version name (if any).
    Returns a string like 'v2.4.0' or an empty string on error.
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/LetsGoDude/OverseerrRequestViaTelegramBot/releases/latest",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        latest_version = data.get("tag_name", "")
        return latest_version
    except requests.RequestException as e:
        logger.warning(f"Failed to check latest version on GitHub: {e}")
        return ""

async def get_tv_show_seasons(tv_show_id: int) -> List:
    """Retrieve seasons for a TV show from Overseerr."""
    try:
        url = f"{OVERSEERR_API_URL}/tv/{tv_show_id}"
        response = requests.get(
            url,
            headers={"X-Api-Key": OVERSEERR_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        seasons = data.get("seasons", [])
        # Filter out season 0 (specials) and return season numbers
        valid_seasons = [
            season["seasonNumber"]
            for season in seasons
            if season.get("seasonNumber", 0) > 0 and season.get("episodeCount", 0) > 0
        ]
        logger.info(f"Found {len(valid_seasons)} valid seasons for TV show {tv_show_id}: {valid_seasons}")
        return valid_seasons
    except requests.RequestException as e:
        logger.error(f"Error fetching seasons for TV show {tv_show_id}: {e}")
        return []

def user_can_request_4k(overseerr_user_id: int, media_type: str) -> bool:
    """
    Check if a user has permissions to request 4K content.
    """
    from config.constants import PERMISSION_4K_MOVIE, PERMISSION_4K_TV
    
    try:
        url = f"{OVERSEERR_API_URL}/user/{overseerr_user_id}"
        response = requests.get(
            url,
            headers={"X-Api-Key": OVERSEERR_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        user_data = response.json()
        
        permissions = user_data.get("permissions", 0)
        
        if media_type == "movie":
            return bool(permissions & PERMISSION_4K_MOVIE)
        elif media_type == "tv":
            return bool(permissions & PERMISSION_4K_TV)
        else:
            return False
            
    except requests.RequestException as e:
        logger.error(f"Error checking 4K permissions for user {overseerr_user_id}: {e}")
        return False
