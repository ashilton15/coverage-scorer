"""Article fetching utilities with simplified, reliable approach.

Supports two-tier fetching:
1. Fast requests-based fetch for most sites
2. Playwright headless browser fallback for JavaScript-rendered pages
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Tuple, List
import re
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Single reliable user agent (Chrome on Mac - widely accepted)
CHROME_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Default timeout 30 seconds, only 2 retries (1 initial + 1 retry)
DEFAULT_TIMEOUT = 30
PLAYWRIGHT_TIMEOUT = 45000  # 45 seconds for playwright (in milliseconds)
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds between retries

# Minimum content thresholds for triggering headless browser fallback
MIN_CONTENT_CHARS_FOR_SUCCESS = 500  # If less than this, try headless
MIN_PARAGRAPHS_FOR_JS_CHECK = 3  # If fewer paragraphs than this with many scripts, it's JS-rendered

# Sites known to require JavaScript rendering
JS_HEAVY_DOMAINS = [
    'coindesk.com',
    'msn.com',
    'bloomberg.com',
    'forbes.com',
    'businessinsider.com',
]

# Playwright availability flag
_playwright_available = None

def check_playwright_available() -> bool:
    """Check if playwright is installed and available."""
    global _playwright_available
    if _playwright_available is None:
        try:
            from playwright.sync_api import sync_playwright
            _playwright_available = True
            logger.info("[PLAYWRIGHT] Playwright is available")
        except ImportError:
            _playwright_available = False
            logger.warning("[PLAYWRIGHT] Playwright not installed - headless browser fallback disabled")
    return _playwright_available


def get_browser_headers() -> Dict[str, str]:
    """Get headers that mimic a real Chrome browser on Mac.

    Note: We use 'gzip, deflate' instead of 'gzip, deflate, br' because
    Python's requests library doesn't natively support Brotli decompression,
    which causes parsing failures when servers return Brotli-compressed content.
    """
    return {
        "User-Agent": CHROME_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",  # No 'br' - Python doesn't support Brotli natively
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def fetch_with_playwright(url: str, timeout: int = PLAYWRIGHT_TIMEOUT) -> Tuple[bool, str, Dict]:
    """
    Fetch article content using playwright headless browser.

    This is used as a fallback for JavaScript-rendered pages that
    don't return proper content with simple requests.

    Args:
        url: The URL to fetch
        timeout: Timeout in milliseconds (default 45000ms = 45 seconds)

    Returns:
        Tuple of (success, content_or_error, metadata)
    """
    metadata = {
        "url": url,
        "domain": "",
        "title": "",
        "author": "",
        "fetch_errors": [],
        "http_status": None,
        "fetch_method": "playwright"
    }

    try:
        parsed_url = urlparse(url)
        metadata["domain"] = parsed_url.netloc.replace("www.", "")

        from playwright.sync_api import sync_playwright

        logger.info(f"[PLAYWRIGHT] Starting headless browser fetch for: {url[:60]}")

        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=CHROME_USER_AGENT,
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                # Navigate to the page and wait for network to be idle
                response = page.goto(url, wait_until='networkidle', timeout=timeout)

                if response:
                    metadata["http_status"] = response.status
                    logger.info(f"[PLAYWRIGHT] HTTP {response.status} for {url[:60]}")

                    if response.status >= 400:
                        error_msg = f"HTTP {response.status} - Page returned error status"
                        metadata["fetch_errors"].append(error_msg)
                        browser.close()
                        return False, error_msg, metadata

                # Wait a bit more for any lazy-loaded content
                page.wait_for_timeout(2000)  # 2 second extra wait

                # Get the page content after JavaScript has executed
                html_content = page.content()

                browser.close()

                # Parse the rendered HTML
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract content
                success, content = extract_content_from_html(soup, metadata)

                if success:
                    word_count = len(content.split())
                    logger.info(f"[PLAYWRIGHT] SUCCESS - Extracted {word_count} words from {url[:60]}")
                    return True, content, metadata
                else:
                    error_msg = f"Content extraction failed: {content}"
                    metadata["fetch_errors"].append(error_msg)
                    return False, error_msg, metadata

            except Exception as e:
                browser.close()
                raise e

    except ImportError:
        error_msg = "Playwright not installed - cannot use headless browser"
        logger.error(f"[PLAYWRIGHT] {error_msg}")
        metadata["fetch_errors"].append(error_msg)
        return False, error_msg, metadata

    except Exception as e:
        error_msg = f"Playwright error: {type(e).__name__}: {str(e)[:100]}"
        logger.error(f"[PLAYWRIGHT] {error_msg}")
        metadata["fetch_errors"].append(error_msg)
        return False, error_msg, metadata


def is_js_heavy_domain(url: str) -> bool:
    """Check if the URL is from a domain known to require JavaScript rendering."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        for js_domain in JS_HEAVY_DOMAINS:
            if js_domain in domain:
                return True
        return False
    except:
        return False


def is_bloomberg_url(url: str) -> bool:
    """Check if the URL is from Bloomberg."""
    try:
        parsed = urlparse(url)
        return 'bloomberg.com' in parsed.netloc.lower()
    except:
        return False


def handle_bloomberg_content(content: str, metadata: Dict) -> Tuple[str, Dict]:
    """
    Special handling for Bloomberg articles/newsletters.

    Bloomberg often shows preview/paywall content. This function:
    1. Checks if the content seems too short for a feature article
    2. Flags partial content for manual review

    Returns:
        Tuple of (content, updated_metadata)
    """
    char_count = len(content)
    word_count = len(content.split())

    # Bloomberg feature articles and newsletters are typically long
    # If we got less than 1000 chars, it's likely partial/preview content
    if char_count < 1000:
        metadata["partial_content"] = True
        metadata["partial_content_reason"] = f"Bloomberg content too short ({char_count} chars, {word_count} words) - may need manual review"
        logger.warning(f"[BLOOMBERG] Partial content detected: {char_count} chars, {word_count} words")

    return content, metadata


def extract_original_url_from_msn(url: str) -> Optional[str]:
    """
    Extract the original source URL from MSN article URLs.
    MSN often wraps original articles with their own URLs.
    """
    try:
        parsed = urlparse(url)
        if 'msn.com' in parsed.netloc.lower():
            # Try to find original URL in query params
            query_params = parse_qs(parsed.query)
            if 'url' in query_params:
                return query_params['url'][0]
            if 'originalUrl' in query_params:
                return query_params['originalUrl'][0]
        return None
    except Exception:
        return None


def extract_content_from_html(soup: BeautifulSoup, metadata: Dict) -> Tuple[bool, str]:
    """
    Extract article content from parsed HTML with detailed validation.
    Returns (success, content_or_error)

    Validation checks:
    - Response must have meaningful HTML structure
    - Content must have at least 200 characters of text
    - Content must have at least 50 words
    """
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        metadata["title"] = title_tag.get_text().strip()

    # Try to find headline
    headline_selectors = [
        'h1.headline', 'h1.article-title', 'h1.post-title',
        'h1[class*="headline"]', 'h1[class*="title"]',
        'article h1', '.article-header h1', 'h1'
    ]
    for selector in headline_selectors:
        headline = soup.select_one(selector)
        if headline:
            metadata["title"] = headline.get_text().strip()
            break

    # Try to find author
    author_selectors = [
        '[class*="author"] a', '[class*="byline"]',
        'a[rel="author"]', '[class*="author-name"]',
        'span[class*="author"]', '.author', '.byline'
    ]
    for selector in author_selectors:
        author = soup.select_one(selector)
        if author:
            author_text = author.get_text().strip()
            # Clean up common prefixes
            author_text = re.sub(r'^(By|Written by|Author:)\s*', '', author_text, flags=re.IGNORECASE)
            metadata["author"] = author_text
            break

    # BEFORE removing scripts: check for JavaScript-rendered single-page apps
    # These have many scripts but no actual content paragraphs
    script_count = len(soup.find_all('script'))
    p_count = len(soup.find_all('p'))

    if script_count > 20 and p_count < 3:
        # Check if there's meaningful text content before declaring it JS-rendered
        all_text_preview = soup.get_text(separator=' ', strip=True)
        if len(all_text_preview) < 500:  # Very little actual text content
            return False, f"JavaScript-rendered page (React/Vue/etc.) - requires browser to access content ({script_count} scripts, {p_count} paragraphs)"

    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                   'aside', 'iframe', 'noscript', 'form']):
        element.decompose()

    # Check if page has any meaningful structure after cleanup
    all_text = soup.get_text(separator=' ', strip=True)

    if len(all_text) < 100:
        return False, f"Page has no meaningful content (only {len(all_text)} chars of text)"

    # Try to find article content using various selectors
    content_selectors = [
        'article', '[class*="article-body"]', '[class*="article-content"]',
        '[class*="post-content"]', '[class*="entry-content"]',
        '[class*="story-body"]', '[class*="story-content"]',
        '[class*="main-content"]', '[class*="page-content"]',
        '.content', 'main', '[role="main"]'
    ]

    content = ""
    matched_selector = None
    for selector in content_selectors:
        article_elem = soup.select_one(selector)
        if article_elem:
            paragraphs = article_elem.find_all('p')
            content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if len(content.split()) >= 100:
                matched_selector = selector
                break

    # Fallback to all paragraphs
    if len(content.split()) < 100:
        all_paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text().strip() for p in all_paragraphs if p.get_text().strip()])
        matched_selector = "fallback (all paragraphs)"

    # Validation checks
    char_count = len(content)
    word_count = len(content.split())

    # Check minimum character count (200 chars)
    if char_count < 200:
        return False, f"Content too short ({char_count} chars, need 200+)"

    # Check minimum word count (50 words)
    if word_count < 50:
        return False, f"Content too short ({word_count} words, need 50+)"

    logger.info(f"[EXTRACT] Used selector: {matched_selector}, got {word_count} words")
    return True, content


def fetch_article(url: str, timeout: int = DEFAULT_TIMEOUT, use_playwright_fallback: bool = True) -> Tuple[bool, str, Dict]:
    """
    Fetch article content from URL with two-tier approach.

    Tier 1: Fast requests-based fetch
    Tier 2: Playwright headless browser fallback (if tier 1 fails or returns insufficient content)

    Features:
    - Single reliable Chrome user-agent
    - 30 second timeout for requests, 45 seconds for playwright
    - One retry after 2 second delay if first attempt fails
    - Detailed error logging with HTTP status codes
    - Special handling for MSN redirect URLs
    - Special handling for Bloomberg newsletters
    - Automatic fallback to headless browser for JS-rendered pages

    Args:
        url: The URL to fetch
        timeout: Timeout in seconds for requests-based fetch
        use_playwright_fallback: Whether to try playwright if requests-based fetch fails/returns little content

    Returns:
        Tuple of (success, content_or_error, metadata)
        - metadata includes 'fetch_errors' list with specific error messages
        - metadata includes 'http_status' with the response status code
        - metadata includes 'fetch_method' ('requests' or 'playwright')
        - metadata includes 'partial_content' if Bloomberg content seems truncated
    """
    metadata = {
        "url": url,
        "domain": "",
        "title": "",
        "author": "",
        "fetch_errors": [],
        "http_status": None,
        "fetch_method": "requests"
    }

    # Track if we should try playwright fallback
    should_try_playwright = False
    playwright_reason = ""

    try:
        parsed_url = urlparse(url)
        metadata["domain"] = parsed_url.netloc.replace("www.", "")
        domain_lower = parsed_url.netloc.lower()

        # Check if this is an MSN URL and try to extract original source
        if 'msn.com' in domain_lower:
            original_url = extract_original_url_from_msn(url)
            if original_url:
                logger.info(f"MSN redirect detected. Trying original URL: {original_url}")
                result = fetch_article(original_url, timeout)
                if result[0]:  # If successful with original URL
                    return result
                else:
                    logger.info(f"Original URL failed, trying MSN URL directly")

        all_errors = []
        headers = get_browser_headers()

        # Attempt fetch with one retry
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"[Attempt {attempt + 1}/{MAX_RETRIES}] Fetching: {url[:100]}")

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True
                )

                # Log HTTP status for every request
                status_code = response.status_code
                metadata["http_status"] = status_code
                logger.info(f"[HTTP {status_code}] {url[:60]}")

                # Handle specific HTTP errors
                if status_code == 403:
                    error_msg = f"HTTP 403 Forbidden - Site is blocking access"
                    logger.warning(f"[BLOCKED] {error_msg}")
                    all_errors.append(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Waiting {RETRY_DELAY}s before retry...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        metadata["fetch_errors"] = all_errors
                        return False, error_msg, metadata

                if status_code == 404:
                    error_msg = f"HTTP 404 Not Found - Article does not exist"
                    logger.warning(f"[NOT FOUND] {error_msg}")
                    all_errors.append(error_msg)
                    metadata["fetch_errors"] = all_errors
                    return False, error_msg, metadata  # Don't retry 404s

                if status_code == 429:
                    error_msg = f"HTTP 429 Rate Limited - Too many requests"
                    logger.warning(f"[RATE LIMITED] {error_msg}")
                    all_errors.append(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Waiting {RETRY_DELAY}s before retry...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        metadata["fetch_errors"] = all_errors
                        return False, error_msg, metadata

                if status_code >= 500:
                    error_msg = f"HTTP {status_code} Server Error"
                    logger.warning(f"[SERVER ERROR] {error_msg}")
                    all_errors.append(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Waiting {RETRY_DELAY}s before retry...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        metadata["fetch_errors"] = all_errors
                        return False, error_msg, metadata

                # Check for other non-success status codes
                if status_code != 200:
                    error_msg = f"HTTP {status_code} - Unexpected status"
                    logger.warning(error_msg)
                    all_errors.append(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue

                # Check response has content
                content_length = len(response.content)
                logger.info(f"[CONTENT] Received {content_length} bytes")

                if content_length == 0:
                    error_msg = "Empty response - No content received"
                    logger.warning(f"[EMPTY] {error_msg}")
                    all_errors.append(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        metadata["fetch_errors"] = all_errors
                        return False, error_msg, metadata

                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')

                # Check for paywall indicators
                paywall_indicators = ['paywall', 'subscribe-wall', 'subscription-required', 'premium-content']
                page_text_lower = str(soup).lower()
                detected_paywall = None
                for indicator in paywall_indicators:
                    if indicator in page_text_lower:
                        detected_paywall = indicator
                        break

                if detected_paywall and len(soup.find_all('p')) < 5:
                    error_msg = f"Paywall detected ({detected_paywall}) - Content behind subscription"
                    logger.warning(f"[PAYWALL] {error_msg}")
                    all_errors.append(error_msg)
                    metadata["fetch_errors"] = all_errors
                    return False, error_msg, metadata

                # Extract content
                success, content = extract_content_from_html(soup, metadata)

                if success:
                    word_count = len(content.split())
                    char_count = len(content)
                    logger.info(f"[REQUESTS] Extracted {word_count} words ({char_count} chars) - Title: {metadata.get('title', 'Unknown')[:50]}")

                    # Check if content is too short - might need playwright
                    if char_count < MIN_CONTENT_CHARS_FOR_SUCCESS:
                        should_try_playwright = True
                        playwright_reason = f"Content too short ({char_count} chars < {MIN_CONTENT_CHARS_FOR_SUCCESS})"
                        logger.info(f"[REQUESTS] {playwright_reason} - will try playwright fallback")
                        # Don't return yet - fall through to playwright attempt
                        all_errors.append(f"Requests fetch returned insufficient content: {char_count} chars")
                        break  # Exit retry loop, try playwright

                    # Check if this is a JS-heavy domain and content seems thin
                    if is_js_heavy_domain(url) and (char_count < 1000 or word_count < 200):
                        should_try_playwright = True
                        playwright_reason = f"JS-heavy domain with thin content ({char_count} chars, {word_count} words)"
                        logger.info(f"[REQUESTS] {playwright_reason} - will try playwright fallback")
                        all_errors.append(f"JS-heavy domain returned thin content")
                        break  # Exit retry loop, try playwright

                    # Bloomberg special handling
                    if is_bloomberg_url(url):
                        content, metadata = handle_bloomberg_content(content, metadata)

                    metadata["fetch_method"] = "requests"
                    return True, content, metadata
                else:
                    # content contains the error message
                    error_msg = f"Content extraction failed: {content}"
                    logger.warning(f"[EXTRACTION FAILED] {error_msg}")
                    all_errors.append(error_msg)

                    # Check if it's a JS-rendered page error - should try playwright
                    if "JavaScript-rendered" in content or "requires browser" in content:
                        should_try_playwright = True
                        playwright_reason = "Detected JavaScript-rendered page"
                        logger.info(f"[REQUESTS] {playwright_reason} - will try playwright fallback")
                        break  # Exit retry loop, try playwright

                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        metadata["fetch_errors"] = all_errors
                        # Fall through to check if we should try playwright
                        should_try_playwright = True
                        playwright_reason = "All request attempts failed"
                        break

            except requests.exceptions.Timeout:
                error_msg = f"Timeout after {timeout}s - Site too slow to respond"
                logger.warning(f"[TIMEOUT] {error_msg}")
                all_errors.append(error_msg)
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Waiting {RETRY_DELAY}s before retry...")
                    time.sleep(RETRY_DELAY)
                    continue

            except requests.exceptions.SSLError as e:
                error_msg = f"SSL/TLS Error - Certificate problem: {str(e)[:80]}"
                logger.warning(f"[SSL ERROR] {error_msg}")
                all_errors.append(error_msg)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue

            except requests.exceptions.ConnectionError as e:
                error_str = str(e)
                if "Name or service not known" in error_str or "getaddrinfo failed" in error_str:
                    error_msg = "DNS Error - Domain not found"
                elif "Connection refused" in error_str:
                    error_msg = "Connection Refused - Server not accepting connections"
                else:
                    error_msg = f"Connection Error: {error_str[:80]}"
                logger.warning(f"[CONNECTION ERROR] {error_msg}")
                all_errors.append(error_msg)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue

            except Exception as e:
                error_msg = f"Unexpected Error ({type(e).__name__}): {str(e)[:80]}"
                logger.error(f"[UNEXPECTED] {error_msg}")
                all_errors.append(error_msg)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue

        # All retries exhausted for requests-based fetch
        metadata["fetch_errors"] = all_errors

        # Try playwright fallback if enabled and appropriate
        if use_playwright_fallback and should_try_playwright and check_playwright_available():
            logger.info(f"[PLAYWRIGHT FALLBACK] Attempting playwright due to: {playwright_reason}")

            pw_success, pw_content, pw_metadata = fetch_with_playwright(url)

            if pw_success:
                # Merge metadata
                metadata.update(pw_metadata)
                metadata["fetch_method"] = "playwright"
                metadata["fetch_errors"] = all_errors + pw_metadata.get("fetch_errors", [])

                # Bloomberg special handling
                if is_bloomberg_url(url):
                    pw_content, metadata = handle_bloomberg_content(pw_content, metadata)

                logger.info(f"[PLAYWRIGHT FALLBACK] SUCCESS - playwright retrieved content")
                return True, pw_content, metadata
            else:
                # Playwright also failed
                all_errors.extend(pw_metadata.get("fetch_errors", []))
                metadata["fetch_errors"] = all_errors
                logger.warning(f"[PLAYWRIGHT FALLBACK] Also failed: {pw_content}")

        final_error = all_errors[-1] if all_errors else "Unknown error"
        logger.error(f"[FAILED] All fetch attempts failed for {url[:60]}")
        return False, final_error, metadata

    except Exception as e:
        error_msg = f"Fatal Error ({type(e).__name__}): {str(e)}"
        logger.error(f"[FATAL] {error_msg}")
        metadata["fetch_errors"] = [error_msg]
        return False, error_msg, metadata


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return ""


def test_fetch_urls(urls: List[str]) -> List[Dict]:
    """
    Test function to diagnose fetching issues with specific URLs.

    Args:
        urls: List of URLs to test

    Returns:
        List of test result dictionaries with detailed diagnostic info
    """
    results = []

    print("\n" + "="*70)
    print("ARTICLE FETCHER DIAGNOSTIC TEST")
    print("="*70)

    for i, url in enumerate(urls, 1):
        print(f"\n[Test {i}/{len(urls)}] Testing: {url[:70]}...")
        print("-" * 70)

        result = {
            "url": url,
            "domain": extract_domain(url),
            "success": False,
            "http_status": None,
            "error": None,
            "content_length": 0,
            "word_count": 0,
            "title": "",
            "details": []
        }

        start_time = time.time()
        success, content_or_error, metadata = fetch_article(url)
        elapsed = time.time() - start_time

        result["success"] = success
        result["http_status"] = metadata.get("http_status")
        result["title"] = metadata.get("title", "")
        result["elapsed_seconds"] = round(elapsed, 2)

        if success:
            result["content_length"] = len(content_or_error)
            result["word_count"] = len(content_or_error.split())
            result["details"].append(f"SUCCESS in {elapsed:.1f}s")
            result["details"].append(f"HTTP Status: {metadata.get('http_status', 'N/A')}")
            result["details"].append(f"Content: {result['word_count']} words, {result['content_length']} chars")
            result["details"].append(f"Title: {result['title'][:60]}...")

            print(f"  [SUCCESS] Fetched in {elapsed:.1f}s")
            print(f"  HTTP Status: {metadata.get('http_status', 'N/A')}")
            print(f"  Content: {result['word_count']} words ({result['content_length']} chars)")
            print(f"  Title: {result['title'][:60]}")
        else:
            result["error"] = content_or_error
            result["fetch_errors"] = metadata.get("fetch_errors", [])
            result["details"].append(f"FAILED in {elapsed:.1f}s")
            result["details"].append(f"HTTP Status: {metadata.get('http_status', 'N/A')}")
            result["details"].append(f"Error: {content_or_error}")
            if metadata.get("fetch_errors"):
                result["details"].append(f"All errors: {metadata['fetch_errors']}")

            print(f"  [FAILED] in {elapsed:.1f}s")
            print(f"  HTTP Status: {metadata.get('http_status', 'N/A')}")
            print(f"  Error: {content_or_error}")
            if metadata.get("fetch_errors"):
                for err in metadata["fetch_errors"]:
                    print(f"    - {err}")

        results.append(result)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    print(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")

    if failed > 0:
        print("\nFailed URLs:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['domain']}: {r['error']}")

    print("="*70 + "\n")

    return results


def test_specific_urls():
    """
    Test the specific URLs that are failing.
    Run this function directly to diagnose issues.
    """
    test_urls = [
        "https://thelogic.co/news/open-banking-stablecoins-legislation/",
        "https://blockonomi.com/canada-moves-forward-with-stablecoin-regulation-in-new-federal-budget/",
        "https://www.coindesk.com/policy/2025/11/18/canada-approves-budget-that-advances-policy-for-stablecoins"
    ]
    return test_fetch_urls(test_urls)


# Allow running this file directly for testing
if __name__ == "__main__":
    test_specific_urls()
