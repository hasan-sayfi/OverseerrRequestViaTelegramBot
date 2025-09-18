# Tests for the Request More Seasons feature
import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.overseerr_api import get_tv_show_seasons_with_status, get_unavailable_seasons
from handlers.ui_handlers import build_media_details_message
from handlers.callback_handlers import handle_request_more_seasons


class TestRequestMoreSeasons(unittest.TestCase):
    """Test cases for Request More Seasons functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_tv_show = {
            'id': 12345,
            'title': 'Test TV Show',
            'year': '2023',
            'mediaType': 'tv',
            'poster': '/test_poster.jpg',
            'description': 'Test description for a TV show',
            'overseerr_id': 67890,
            'release_date_full': '2023-01-01',
            'status_hd': 2,  # Pending
            'status_4k': 1   # Unknown
        }
        
        self.sample_movie = {
            'id': 54321,
            'title': 'Test Movie',
            'year': '2023',
            'mediaType': 'movie',
            'poster': '/test_movie.jpg',
            'description': 'Test description for a movie',
            'overseerr_id': 98765,
            'release_date_full': '2023-06-15',
            'status_hd': 3,  # Processing
            'status_4k': 1   # Unknown
        }

    @patch('api.overseerr_api.requests.get')
    def test_get_tv_show_seasons_with_status_success(self, mock_get):
        """Test successful retrieval of TV show seasons with status"""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'seasons': [
                {'seasonNumber': 0, 'episodeCount': 1, 'status': 5},  # Specials - should be filtered
                {'seasonNumber': 1, 'episodeCount': 10, 'status': 5},  # Available
                {'seasonNumber': 2, 'episodeCount': 12, 'status': 2},  # Pending (unavailable)
                {'seasonNumber': 3, 'episodeCount': 8, 'status': 1},   # Unknown (unavailable)
                {'seasonNumber': 4, 'episodeCount': 0, 'status': 1}    # No episodes - should be filtered
            ]
        }
        mock_get.return_value = mock_response
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_tv_show_seasons_with_status(12345))
        loop.close()
        
        # Verify results
        self.assertEqual(len(result), 3)  # Should have 3 valid seasons (1, 2, 3)
        
        # Check season 1 (available)
        season1 = next(s for s in result if s['seasonNumber'] == 1)
        self.assertTrue(season1['isAvailable'])
        self.assertEqual(season1['status'], 5)
        
        # Check season 2 (unavailable)
        season2 = next(s for s in result if s['seasonNumber'] == 2)
        self.assertFalse(season2['isAvailable'])
        self.assertEqual(season2['status'], 2)
        
        # Check season 3 (unavailable)
        season3 = next(s for s in result if s['seasonNumber'] == 3)
        self.assertFalse(season3['isAvailable'])
        self.assertEqual(season3['status'], 1)

    @patch('api.overseerr_api.requests.get')
    def test_get_tv_show_seasons_with_status_api_error(self, mock_get):
        """Test handling of API errors when fetching seasons"""
        # Mock a requests.RequestException which is what the function actually catches
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("API connection failed")
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_tv_show_seasons_with_status(12345))
        loop.close()
        
        # Should return empty list on error
        self.assertEqual(result, [])

    @patch('api.overseerr_api.get_tv_show_seasons_with_status')
    def test_get_unavailable_seasons_success(self, mock_get_seasons):
        """Test successful retrieval of unavailable seasons"""
        # Mock detailed seasons data
        mock_get_seasons.return_value = [
            {'seasonNumber': 1, 'episodeCount': 10, 'status': 5, 'isAvailable': True},
            {'seasonNumber': 2, 'episodeCount': 12, 'status': 2, 'isAvailable': False},
            {'seasonNumber': 3, 'episodeCount': 8, 'status': 1, 'isAvailable': False}
        ]
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_unavailable_seasons(12345))
        loop.close()
        
        # Should return only unavailable season numbers
        self.assertEqual(result, [2, 3])

    @patch('api.overseerr_api.get_tv_show_seasons_with_status')
    def test_get_unavailable_seasons_all_available(self, mock_get_seasons):
        """Test when all seasons are already available"""
        # Mock all seasons as available
        mock_get_seasons.return_value = [
            {'seasonNumber': 1, 'episodeCount': 10, 'status': 5, 'isAvailable': True},
            {'seasonNumber': 2, 'episodeCount': 12, 'status': 5, 'isAvailable': True}
        ]
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(get_unavailable_seasons(12345))
        loop.close()
        
        # Should return empty list when all seasons are available
        self.assertEqual(result, [])

    @patch('handlers.ui_handlers.get_unavailable_seasons')
    def test_build_media_details_message_tv_with_unavailable_seasons(self, mock_get_unavailable):
        """Test UI generation for TV show with unavailable seasons"""
        # Mock unavailable seasons
        mock_get_unavailable.return_value = [2, 3]
        
        # Mock context
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123,
            'seasons_12345': [1, 2, 3]
        }
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        media_text, keyboard = loop.run_until_complete(
            build_media_details_message(self.sample_tv_show, mock_context, set())
        )
        loop.close()
        
        # Check that Request More button is included
        button_texts = [button.text for row in keyboard for button in row]
        self.assertIn("📥 Request More", button_texts)
        
        # Verify button callback data
        request_more_button = None
        for row in keyboard:
            for button in row:
                if button.text == "📥 Request More":
                    request_more_button = button
                    break
        
        self.assertIsNotNone(request_more_button)
        self.assertEqual(request_more_button.callback_data, "request_more_12345")

    @patch('handlers.ui_handlers.get_unavailable_seasons')
    def test_build_media_details_message_tv_no_unavailable_seasons(self, mock_get_unavailable):
        """Test UI generation for TV show with no unavailable seasons"""
        # Mock no unavailable seasons
        mock_get_unavailable.return_value = []
        
        # Mock context
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123,
            'seasons_12345': [1, 2, 3]
        }
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        media_text, keyboard = loop.run_until_complete(
            build_media_details_message(self.sample_tv_show, mock_context, set())
        )
        loop.close()
        
        # Check that Request More button is NOT included
        button_texts = [button.text for row in keyboard for button in row]
        self.assertNotIn("📥 Request More", button_texts)

    @patch('handlers.ui_handlers.get_unavailable_seasons')
    def test_build_media_details_message_movie_no_request_more(self, mock_get_unavailable):
        """Test UI generation for movie (should never show Request More)"""
        # Mock context
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123
        }
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        media_text, keyboard = loop.run_until_complete(
            build_media_details_message(self.sample_movie, mock_context, set())
        )
        loop.close()
        
        # Check that Request More button is NOT included for movies
        button_texts = [button.text for row in keyboard for button in row]
        self.assertNotIn("📥 Request More", button_texts)
        
        # get_unavailable_seasons should not be called for movies
        mock_get_unavailable.assert_not_called()

    @patch('handlers.ui_handlers.get_unavailable_seasons')
    def test_build_media_details_message_api_error_handling(self, mock_get_unavailable):
        """Test UI generation handles API errors gracefully"""
        # Mock API error
        mock_get_unavailable.side_effect = Exception("API Error")
        
        # Mock context
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123,
            'seasons_12345': [1, 2, 3]
        }
        
        # Run the async function - should not raise exception
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            media_text, keyboard = loop.run_until_complete(
                build_media_details_message(self.sample_tv_show, mock_context, set())
            )
            # Should still return valid UI without Request More button
            button_texts = [button.text for row in keyboard for button in row]
            self.assertNotIn("📥 Request More", button_texts)
        except Exception as e:
            self.fail(f"build_media_details_message raised an exception: {e}")
        finally:
            loop.close()

    @patch('api.overseerr_api.get_unavailable_seasons')
    @patch('handlers.ui_handlers.build_media_details_message')
    def test_handle_request_more_seasons_success(self, mock_build_message, mock_get_unavailable):
        """Test successful handling of Request More callback"""
        # Mock unavailable seasons
        mock_get_unavailable.return_value = [2, 3]
        
        # Mock UI generation
        mock_build_message.return_value = ("Test message", [])
        
        # Mock query and context
        mock_query = AsyncMock()
        mock_query.edit_message_caption = AsyncMock()
        
        mock_context = Mock()
        mock_context.user_data = {
            'search_results': [self.sample_tv_show],
            'selected_seasons': [1]  # Should be cleared
        }
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_request_more_seasons(mock_query, mock_context, 12345))
        loop.close()
        
        # Verify unavailable seasons were cached
        self.assertEqual(mock_context.user_data['seasons_12345'], [2, 3])
        
        # Verify previous season selection was cleared
        self.assertNotIn('selected_seasons', mock_context.user_data)
        
        # Verify UI was updated
        mock_query.edit_message_caption.assert_called_once()

    @patch('api.overseerr_api.get_unavailable_seasons')
    def test_handle_request_more_seasons_no_unavailable(self, mock_get_unavailable):
        """Test handling when no unavailable seasons exist"""
        # Mock no unavailable seasons
        mock_get_unavailable.return_value = []
        
        # Mock query
        mock_query = AsyncMock()
        mock_query.answer = AsyncMock()
        
        mock_context = Mock()
        mock_context.user_data = {'search_results': [self.sample_tv_show]}
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_request_more_seasons(mock_query, mock_context, 12345))
        loop.close()
        
        # Should show alert message
        mock_query.answer.assert_called_with("No more seasons available to request.", show_alert=True)

    def test_handle_request_more_seasons_media_not_found(self):
        """Test handling when media is not found in search results"""
        # Mock query
        mock_query = AsyncMock()
        mock_query.edit_message_text = AsyncMock()
        
        mock_context = Mock()
        mock_context.user_data = {'search_results': []}  # Empty search results
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_request_more_seasons(mock_query, mock_context, 12345))
        loop.close()
        
        # Should show error message
        mock_query.edit_message_text.assert_called_with("❌ Media not found.")


if __name__ == '__main__':
    unittest.main()