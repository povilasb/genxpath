from rnet.blocking import Client as RnetClient
from rnet.emulation import EmulationOption
import logging
from cache3 import DiskCache


def http_get(url: str, cache: DiskCache) -> str:
    if cached := cache.get(url):
        logging.info(f"Cache hit for {url}")
        return cached

    http_client = RnetClient(emulation=EmulationOption.random(), allow_redirects=True)
    resp = http_client.get(url)
    html_doc = resp.text()
    cache.set(url, html_doc, timeout=24 * 3600)
    logging.info(f"Cached {url}")

    assert resp.status.as_int() == 200
    return html_doc
