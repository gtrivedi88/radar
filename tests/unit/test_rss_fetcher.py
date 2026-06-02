# tests/unit/test_rss_fetcher.py
import pytest
import re
from unittest.mock import AsyncMock, patch
from radar.adapters.fetchers.rss import RSSFetcher
from radar.core.models import SourceConfig, SourceType

@pytest.fixture
def rss_source_config():
    return SourceConfig(
        id="test-rss",
        name="Test RSS Feed",
        type=SourceType.rss,
        config={"feed_url": "https://example.com/feed.xml"},
        signal_type=["news"],
        audience_tags=["tech_writer"]
    )

@pytest.fixture
def mock_feed_data():
    return {
        'bozo': False,  # feedparser attribute indicating parsing quality
        'entries': [
            {
                'title': 'AI Tool Revolution',
                'link': 'https://example.com/ai-tool',
                'published': '2026-05-30T10:00:00Z',
                'published_parsed': (2026, 5, 30, 10, 0, 0, 0, 0, 0),  # time.struct_time format
                'summary': 'New AI tools are changing development workflows...',
                'id': 'https://example.com/ai-tool'
            }
        ]
    }

@pytest.mark.asyncio
async def test_rss_fetcher_basic_functionality(rss_source_config, mock_feed_data):
    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = mock_feed_data

        fetcher = RSSFetcher(rss_source_config)
        items = await fetcher.fetch_items()

        assert len(items) == 1
        assert items[0]['title'] == 'AI Tool Revolution'
        assert items[0]['source_id'] == 'test-rss'
        assert 'item_id' in items[0]

@pytest.mark.asyncio
async def test_rss_fetcher_malformed_feed(rss_source_config):
    """Test handling of malformed RSS feeds"""
    malformed_data = {'bozo': True, 'bozo_exception': Exception('Parse error'), 'entries': []}

    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = malformed_data

        fetcher = RSSFetcher(rss_source_config)
        items = await fetcher.fetch_items()

        assert len(items) == 0  # Should handle malformed feed gracefully

@pytest.mark.asyncio
async def test_rss_fetcher_missing_feed_url():
    """Test validation of missing feed_url config"""
    config = SourceConfig(
        id="test-invalid",
        name="Test Invalid RSS",
        type=SourceType.rss,
        config={},  # Missing feed_url
        signal_type=["news"],
        audience_tags=["test"]
    )

    fetcher = RSSFetcher(config)

    with pytest.raises(ValueError, match="missing required 'feed_url' config"):
        await fetcher.fetch_items()

@pytest.mark.asyncio
async def test_rss_fetcher_invalid_url_scheme(rss_source_config):
    """Test filtering of invalid URL schemes"""
    invalid_url_data = {
        'entries': [
            {
                'title': 'Valid Entry',
                'link': 'https://example.com/valid',
                'summary': 'Valid content'
            },
            {
                'title': 'Invalid Entry',
                'link': 'javascript:alert("xss")',  # Invalid scheme
                'summary': 'Invalid content'
            }
        ]
    }

    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = invalid_url_data

        fetcher = RSSFetcher(rss_source_config)
        items = await fetcher.fetch_items()

        assert len(items) == 1  # Should filter out invalid URL
        assert items[0]['url'] == 'https://example.com/valid'

@pytest.mark.asyncio
async def test_rss_fetcher_content_sanitization(rss_source_config):
    """Test enhanced content sanitization"""
    html_content_data = {
        'entries': [
            {
                'title': 'HTML Content Test',
                'link': 'https://example.com/html',
                'summary': '<p>This has <strong>HTML</strong> tags and   extra   spaces</p>'
            }
        ]
    }

    with patch('feedparser.parse') as mock_parse:
        mock_parse.return_value = html_content_data

        fetcher = RSSFetcher(rss_source_config)
        items = await fetcher.fetch_items()

        assert len(items) == 1
        # Check HTML tags are removed and whitespace normalized
        content = items[0]['raw_text']
        assert '<' not in content and '>' not in content
        assert 'This has HTML tags and extra spaces' in content

@pytest.mark.asyncio
async def test_rss_fetcher_retry_logic(rss_source_config):
    """Test retry logic on network failures"""
    call_count = 0

    def mock_parse_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Network error")
        return {'entries': [{'title': 'Success', 'link': 'https://example.com/success'}]}

    with patch('feedparser.parse', side_effect=mock_parse_side_effect):
        fetcher = RSSFetcher(rss_source_config)
        items = await fetcher.fetch_items()

        assert len(items) == 1
        assert items[0]['title'] == 'Success'
        assert call_count == 2  # Should have retried

def test_rss_fetcher_shared_executor():
    """Test shared executor pattern"""
    config1 = SourceConfig(
        id="test1", name="Test 1", type=SourceType.rss,
        config={"feed_url": "https://example.com/1"},
        signal_type=["news"], audience_tags=["test"]
    )
    config2 = SourceConfig(
        id="test2", name="Test 2", type=SourceType.rss,
        config={"feed_url": "https://example.com/2"},
        signal_type=["news"], audience_tags=["test"]
    )

    # Test that multiple fetchers share the same executor
    fetcher1 = RSSFetcher(config1)
    fetcher2 = RSSFetcher(config2)

    executor1 = fetcher1.get_executor()
    executor2 = fetcher2.get_executor()

    assert executor1 is executor2  # Should be the same instance

    # Test cleanup
    RSSFetcher.shutdown_executor()
    assert RSSFetcher._shared_executor is None

def test_rss_fetcher_registration(rss_source_config):
    from radar.adapters.fetchers.registry import FetcherRegistry

    fetcher_class = FetcherRegistry.get_fetcher(rss_source_config)
    assert fetcher_class is not None
    assert fetcher_class.__name__ == "RSSFetcher"