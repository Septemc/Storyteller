from backend.core.llm_client import _summarize_http_error


def test_summarize_http_error_for_cloudflare_html():
    body = '<!DOCTYPE html><html><head><title>ggchan.dev | 520: Web server is returning an unknown error</title></head></html>'
    message = _summarize_http_error(520, body, stream=True)
    assert 'HTTP 520' in message
    assert '???????????' in message
    assert '<html' not in message.lower()
