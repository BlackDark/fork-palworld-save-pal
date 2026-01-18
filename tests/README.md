# Player Loading Tests

This test suite verifies that player loading from save files works correctly.

## Running Tests

### Using Docker Compose (Recommended)

Run tests using docker-compose:

```bash
# Run all player loading tests
docker-compose --profile test run --rm test

# Run all tests
docker-compose --profile test run --rm test pytest tests/ -v

# Run specific test file
docker-compose --profile test run --rm test pytest tests/test_player_loading.py::TestPlayerLoading::test_player_levels_correct -v

# Run with coverage
docker-compose --profile test run --rm test pytest tests/ --cov=palworld_save_pal --cov-report=html
```

### Using Docker Directly

```bash
# Build test image
docker build --target test-deps -t palworld-save-pal-test .

# Run tests
docker run --rm -v $(pwd)/tests:/app/tests -v $(pwd)/save:/app/save palworld-save-pal-test

# Run interactively
docker run --rm -it -v $(pwd)/tests:/app/tests -v $(pwd)/save:/app/save palworld-save-pal-test /bin/bash
```

### Local Development

Install test dependencies:
```bash
# Using uv (recommended)
uv pip install -e ".[test]"

# Or using pip
pip install -e ".[test]"
```

Run tests:
```bash
pytest tests/ -v
```

## Test Data

Tests use the save file located at:
- `save/0AF5EB784DD4DD7F83A17BBF74FC5DE3/`

Expected players:
- **Knecht** (level 47)
- **Nugget** (level 43)
- **BlackDark** (level 42)

## Test Coverage

The test suite verifies:
1. Player file references are correctly loaded
2. Save file loads successfully
3. Player summaries are extracted correctly
4. All expected players are loaded with correct names
5. Player levels are correctly extracted as integers
6. Player UUIDs match between CharacterSaveParameterMap and file references
7. No players are incorrectly filtered out
8. UUID normalization works correctly
