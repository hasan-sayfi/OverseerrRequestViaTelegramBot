# Tests

This folder contains test files for the Overseerr Telegram Bot.

## Files

### Test Scripts
- **`test_setup.py`** - Basic setup and import tests

## Running Tests

### From project root:
```bash
python tests/test_setup.py
```

### From tests folder:
```bash
cd tests
python test_setup.py
```

## Test Coverage

Currently includes:
- ✅ Import verification for all modules
- ✅ Configuration loading tests  
- ✅ Basic bot initialization tests
- ✅ API connectivity verification
- ✅ Session management tests

## Adding New Tests

When adding new test files:
1. Use descriptive names: `test_<feature>.py`
2. Include path setup for imports:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
3. Follow the existing test pattern for consistency

## Future Enhancements
- Unit tests for individual handlers
- Integration tests for API calls
- Mock testing for Telegram interactions
- Automated test runner with coverage reports
