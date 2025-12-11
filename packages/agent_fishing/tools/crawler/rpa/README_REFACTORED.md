# Refactored RPA Crawler Architecture

## Overview

The RPA crawler has been completely refactored to follow Playwright best practices, improve maintainability, and enhance reliability. The new architecture implements the Page Object Model pattern, proper error handling, semantic locators, and comprehensive monitoring.

## Key Improvements

### 1. **Semantic Locators**
- Replaced fragile CSS selectors with Playwright's built-in locators
- Uses `get_by_role()`, `get_by_text()`, `get_by_label()` for robust element selection
- Multiple fallback strategies for finding elements

### 2. **Page Object Model**
- Clear separation between page objects and business logic
- Reusable page components (BasePage, TaobaoBasePage, TaobaoLoginPage, TaobaoShopPage)
- Each page object encapsulates specific page functionality

### 3. **Error Handling & Retry Mechanisms**
- Automatic retry with exponential backoff
- Specific error handlers for different error types
- Comprehensive error logging and screenshot capture

### 4. **Explicit Wait Strategies**
- Smart waits instead of fixed `time.sleep()`
- Configurable timeouts for different operations
- Waits for specific states (visible, hidden, attached)

### 5. **Monitoring & Logging**
- Operation metrics tracking
- Automatic screenshot on errors
- Detailed logging for debugging
- Performance statistics

### 6. **Configuration Management**
- Type-safe configuration with validation
- Environment variable support
- JSON configuration files
- Sub-configurations for different aspects

### 7. **Anti-Detection Features**
- Stealth mode with browser fingerprint masking
- Human-like delays and mouse movements
- Random user agents
- Configurable proxy support

## Architecture

```
rpa/
├── core/
│   ├── base_page.py          # Base page object with common functionality
│   ├── spider_manager.py     # Browser and operation management
│   └── config_validator.py   # Configuration validation and types
├── pages/
│   ├── taobao_base_page.py   # Base Taobao page functionality
│   ├── taobao_login_page.py  # Login page object
│   └── taobao_shop_page.py   # Shop page object
├── improved/
│   └── taobao_rpa_v2.py      # Refactored main crawler
├── example_usage.py          # Usage examples
└── README_REFACTORED.md      # This documentation
```

## Usage Examples

### Basic Shop Crawling

```python
from tools.crawler.rpa.improved.taobao_rpa_v2 import TaobaoRPAV2
from tools.crawler.rpa.core.config_validator import RPAConfigV2

# Load configuration
config = RPAConfigV2.from_env()
crawler = TaobaoRPAV2(config)

# Crawl shop
result = crawler.crawl_shop_products(
    shop_url="https://shop437350870.taobao.com",
    category="路亚竿",  # Optional
    max_items=100
)

print(f"Crawled {len(result.items)} products")
```

### Custom Configuration

```python
from tools.crawler.rpa.core.config_validator import RPAConfigV2, BrowserConfig

# Create custom configuration
config = RPAConfigV2()
config.browser.headless = False
config.browser.timeout = 60000
config.crawl.max_retries = 5

# Save to file
config.save_to_file("my_config.json")

# Load from file
config = RPAConfigV2.load_from_file("my_config.json")
```

### Error Handling

```python
try:
    result = crawler.crawl_shop_products(
        shop_url="https://example.taobao.com",
        max_items=50
    )
except Exception as e:
    logger.error(f"Crawling failed: {e}")

    # Check statistics
    stats = crawler.get_crawl_statistics()
    print(f"Success rate: {stats.get('success_rate', 0):.2%}")
```

## Configuration

### Environment Variables

```bash
# Browser settings
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_TIMEOUT=30000

# Login settings
TAOBAO_COOKIE_PATH=shared/data/cookies/taobao_session.json
TAOBAO_AUTO_LOGIN=true

# Anti-detection
RPA_ENABLE_STEALTH=true
RPA_RANDOM_DELAYS=true
RPA_MIN_DELAY=0.5
RPA_MAX_DELAY=3.0

# Crawling settings
RPA_MAX_RETRIES=3
TAOBAO_MAX_PAGES=20
TAOBAO_MAX_ITEMS_PER_PAGE=100
```

### Configuration File Structure

```json
{
  "browser": {
    "headless": true,
    "browser_type": "chromium",
    "timeout": 30000,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "enable_stealth": true
  },
  "login": {
    "cookie_path": "shared/data/cookies/taobao_session.json",
    "auto_login": true,
    "max_login_attempts": 3
  },
  "anti_detection": {
    "enable_stealth": true,
    "random_delays": true,
    "min_delay": 0.5,
    "max_delay": 3.0
  },
  "crawl": {
    "max_retries": 3,
    "retry_delay": 2.0,
    "max_pages_per_shop": 20,
    "max_items_per_page": 100
  }
}
```

## Best Practices Implemented

### 1. **Locator Strategies**
```python
# Good: Semantic locators
page.get_by_role("button", name="Submit").click()
page.get_by_text("路亚竿").click()
page.get_by_label("Username").fill("user123")

# Avoid: Fragile CSS selectors
page.locator(".btn-primary.mt-2").click()  # Bad
```

### 2. **Waits**
```python
# Good: Smart waits
page.wait_for_load_state("networkidle")
element.wait_for(state="visible")

# Avoid: Fixed delays
time.sleep(3)  # Bad
```

### 3. **Error Handling**
```python
# Good: Retry with decorator
@retry_operation(max_attempts=3, delay=1.0)
def click_element():
    page.get_by_text("Submit").click()

# Good: Multiple strategies
self.safe_click_with_multiple_strategies(
    "Submit",
    element_type="text",
    fallback_selectors=[".submit-btn", "#submit"]
)
```

### 4. **Page Objects**
```python
class LoginPage(BasePage):
    def login(self, username, password):
        self.get_by_label("Username").fill(username)
        self.get_by_label("Password").fill(password)
        self.get_by_role("button", name="Login").click()
```

## Migration Guide

### From Old to New Architecture

1. **Replace direct element access:**
   ```python
   # Old
   page.click(".submit-btn")

   # New
   page.get_by_role("button", name="Submit").click()
   ```

2. **Use page objects:**
   ```python
   # Old
   def login(page, username, password):
       page.fill("#username", username)
       page.click(".login-btn")

   # New
   login_page = TaobaoLoginPage(page)
   login_page.login_with_credentials(username, password)
   ```

3. **Add error handling:**
   ```python
   # Old
   page.goto(url)

   # New
   with spider_manager.browser_session():
       if not page.navigate_to_url(url):
           logger.error("Navigation failed")
   ```

## Testing

### Running Examples

```bash
cd /Users/zen/projects/fishing_agent
python -m tools.crawler.rpa.example_usage
```

### Debug Mode

```python
config = RPAConfigV2.from_env()
config.browser.headless = False  # Show browser
config.browser.slow_mo = 100    # Slow operations
```

## Monitoring

### Metrics Available
- Total operations
- Success rate
- Average duration
- Items extracted
- Screenshots taken
- Error messages

### Accessing Metrics
```python
stats = crawler.get_crawl_statistics()
print(f"Success rate: {stats['success_rate']:.2%}")
```

## Troubleshooting

### Common Issues

1. **Element not found:**
   - Check if page is fully loaded
   - Use semantic locators instead of CSS
   - Add explicit waits

2. **Login failures:**
   - Check cookie file permissions
   - Verify QR code is visible
   - Check network connectivity

3. **Performance issues:**
   - Disable image loading
   - Increase timeouts
   - Use headless mode

### Debug Screenshots
Screenshots are automatically saved to:
- `shared/data/screenshots/` - Normal operation
- `shared/data/screenshots/error/` - Error conditions

## Future Enhancements

1. **Parallel crawling** with multiple browser instances
2. **Proxy rotation** for large-scale crawling
3. **CAPTCHA solving** integration
4. **Data validation** and schema enforcement
5. **Distributed crawling** support
6. **Real-time monitoring** dashboard

## Dependencies

- playwright >= 1.20.0
- Python >= 3.8
- Type hints support

## License

See project license file.