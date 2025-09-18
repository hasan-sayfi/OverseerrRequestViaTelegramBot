#!/usr/bin/env python3
"""
Integration test for Request More Seasons feature
Tests the complete workflow from button click to UI update
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import asyncio

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRequestMoreSeasonsIntegration(unittest.TestCase):
    """Integration tests for the complete Request More Seasons workflow"""
    
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
            'status_hd': 2,  # Pending - reportable
            'status_4k': 1   # Unknown
        }

    @patch('api.overseerr_api.requests.get')
    @patch('api.overseerr_api.user_can_request_4k')
    @patch('utils.telegram_utils.is_reportable')
    def test_complete_request_more_workflow(self, mock_is_reportable, mock_can_request_4k, mock_requests_get):
        """Test the complete workflow: UI generation -> button click -> season selection"""
        # Mock API responses for season data
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'seasons': [
                {'seasonNumber': 1, 'episodeCount': 10, 'status': 5},  # Available
                {'seasonNumber': 2, 'episodeCount': 12, 'status': 2},  # Pending (unavailable)
                {'seasonNumber': 3, 'episodeCount': 8, 'status': 1},   # Unknown (unavailable)
            ]
        }
        mock_requests_get.return_value = mock_response
        mock_can_request_4k.return_value = False
        mock_is_reportable.return_value = True
        
        # Import here to ensure mocks are in place
        from handlers.ui_handlers import build_media_details_message
        from handlers.callback_handlers import handle_request_more_seasons
        
        # Step 1: Test UI generation shows Request More button
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123,
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generate initial UI
            media_text, keyboard = loop.run_until_complete(
                build_media_details_message(self.sample_tv_show, mock_context, set())
            )
            
            # Verify Request More button is present
            button_texts = [button.text for row in keyboard for button in row]
            self.assertIn("📥 Request More", button_texts, "Request More button should be present when unavailable seasons exist")
            
            # Verify button callback data
            request_more_button = None
            for row in keyboard:
                for button in row:
                    if button.text == "📥 Request More":
                        request_more_button = button
                        break
            
            self.assertIsNotNone(request_more_button, "Request More button should exist")
            self.assertEqual(request_more_button.callback_data, "request_more_12345")
            
            # Step 2: Test button click handler
            mock_query = AsyncMock()
            mock_query.edit_message_caption = AsyncMock()
            
            # Prepare context for button handler
            mock_context.user_data = {
                'search_results': [self.sample_tv_show],
                'selected_seasons': [1]  # Previously selected season
            }
            
            # Call the handler
            loop.run_until_complete(handle_request_more_seasons(mock_query, mock_context, 12345))
            
            # Step 3: Verify the handler updated the UI correctly
            mock_query.edit_message_caption.assert_called_once()
            
            # Verify context was updated correctly
            self.assertEqual(mock_context.user_data['seasons_12345'], [2, 3], "Should cache only unavailable seasons")
            self.assertNotIn('selected_seasons', mock_context.user_data, "Should clear previous season selection")
            self.assertEqual(mock_context.user_data['selected_result'], self.sample_tv_show, "Should set selected result")
            
            print("✅ Complete Request More workflow test passed!")
            
        finally:
            loop.close()

    @patch('api.overseerr_api.requests.get')
    @patch('api.overseerr_api.user_can_request_4k')
    @patch('utils.telegram_utils.is_reportable')
    def test_no_request_more_when_all_available(self, mock_is_reportable, mock_can_request_4k, mock_requests_get):
        """Test that Request More button doesn't appear when all seasons are available"""
        # Mock API responses - all seasons available
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'seasons': [
                {'seasonNumber': 1, 'episodeCount': 10, 'status': 5},  # Available
                {'seasonNumber': 2, 'episodeCount': 12, 'status': 5},  # Available
            ]
        }
        mock_requests_get.return_value = mock_response
        mock_can_request_4k.return_value = False
        mock_is_reportable.return_value = True
        
        from handlers.ui_handlers import build_media_details_message
        
        mock_context = Mock()
        mock_context.user_data = {'overseerr_telegram_user_id': 123}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            media_text, keyboard = loop.run_until_complete(
                build_media_details_message(self.sample_tv_show, mock_context, set())
            )
            
            # Verify Request More button is NOT present
            button_texts = [button.text for row in keyboard for button in row]
            self.assertNotIn("📥 Request More", button_texts, "Request More button should not appear when all seasons are available")
            
            print("✅ No Request More button when all available test passed!")
            
        finally:
            loop.close()

    def test_ui_layout_order(self):
        """Test that buttons appear in the correct order"""
        # This test verifies the UI structure matches requirements:
        # [Season toggles] -> [Request Selected] -> [All 1080p/4K] -> [Request More] -> [Report Issue] -> [Back]
        
        from handlers.ui_handlers import build_media_details_message
        
        # Create a mock that will trigger all buttons
        mock_context = Mock()
        mock_context.user_data = {
            'overseerr_telegram_user_id': 123,
            'seasons_12345': [1, 2, 3],  # Multiple seasons
            'selected_seasons': {2}  # One season selected
        }
        
        with patch('api.overseerr_api.get_unavailable_seasons') as mock_get_unavailable, \
             patch('api.overseerr_api.user_can_request_4k') as mock_can_request_4k, \
             patch('utils.telegram_utils.is_reportable') as mock_is_reportable:
            
            mock_get_unavailable.return_value = [3]  # Season 3 is unavailable
            mock_can_request_4k.return_value = True  # Enable 4K button
            mock_is_reportable.return_value = True   # Enable Report Issue button
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                media_text, keyboard = loop.run_until_complete(
                    build_media_details_message(self.sample_tv_show, mock_context, {2})
                )
                
                # Extract all button texts in order
                all_buttons = []
                for row in keyboard:
                    for button in row:
                        all_buttons.append(button.text)
                
                # Verify key buttons are present and in correct order
                request_more_index = next((i for i, text in enumerate(all_buttons) if "Request More" in text), None)
                report_issue_index = next((i for i, text in enumerate(all_buttons) if "Report Issue" in text), None)
                back_index = next((i for i, text in enumerate(all_buttons) if "Back" in text), None)
                
                self.assertIsNotNone(request_more_index, "Request More button should be present")
                self.assertIsNotNone(report_issue_index, "Report Issue button should be present")
                self.assertIsNotNone(back_index, "Back button should be present")
                
                # Verify order: Request More -> Report Issue -> Back
                self.assertLess(request_more_index, report_issue_index, "Request More should come before Report Issue")
                self.assertLess(report_issue_index, back_index, "Report Issue should come before Back")
                
                print("✅ UI layout order test passed!")
                
            finally:
                loop.close()

    def test_error_handling_robustness(self):
        """Test that the system handles various error conditions gracefully"""
        from handlers.callback_handlers import handle_request_more_seasons
        
        # Test 1: API error during season fetch
        with patch('api.overseerr_api.get_unavailable_seasons') as mock_get_unavailable:
            mock_get_unavailable.side_effect = Exception("API Error")
            
            mock_query = AsyncMock()
            mock_query.answer = AsyncMock()
            
            mock_context = Mock()
            mock_context.user_data = {'search_results': [self.sample_tv_show]}
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Should not raise exception
                loop.run_until_complete(handle_request_more_seasons(mock_query, mock_context, 12345))
                mock_query.answer.assert_called_with("Failed to load more seasons", show_alert=True)
                
                print("✅ API error handling test passed!")
                
            finally:
                loop.close()


def run_integration_tests():
    """Run all integration tests and return success rate"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRequestMoreSeasonsIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 Integration Test Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {total_tests - failures - errors}")
    print(f"   Failed: {failures}")
    print(f"   Errors: {errors}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    return success_rate


if __name__ == '__main__':
    run_integration_tests()