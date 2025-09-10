from pydantic import BaseModel
import typer
from parsel import Selector
from pathlib import Path
from genxpath._gen import find_xpaths
from genxpath._cache import Cache
from rnet.blocking import Client as RnetClient
from rnet.emulation import EmulationOption
import rich
from rich.console import Console
from rich.logging import RichHandler
from datetime import timedelta
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=Console(), rich_tracebacks=True)],
)


class Product(BaseModel):
    name: str | None = None
    price: str | None = None
    views: str | None = None


def main(url: str):
    # TODO: OSS cache lib?
    cache = Cache.load("cache.json")

    if url.startswith("https://"):
        html_doc = _http_get(url, cache)
    else:
        html_doc = Path(url).read_text()

    product = find_xpaths(
        Product(
            name="Trek Fx 1",
            price="300 €",
            views="17",
        ),
        html_doc,
    )
    rich.print(product)

    _xpath_shell(html_doc)

    # TODO: minimize xpath from full path


def _xpath_shell(html_doc: str):
    doc = Selector(text=html_doc)

    history = InMemoryHistory()
    shell_session = PromptSession(history=history)

    while True:
        xpath = shell_session.prompt("xpath: ")
        try:
            elements = doc.xpath(xpath)
            for i, el in enumerate(elements):
                rich.print(f"{i}: {el.get()}")
        except ValueError:
            logging.error(f"Invalid XPath: {xpath}")


def _http_get(url: str, cache: Cache) -> str:
    if cached := cache.get(url):
        logging.info(f"Cache hit for {url}")
        return cached

    http_client = RnetClient(emulation=EmulationOption.random(), allow_redirects=True)
    resp = http_client.get(url)
    html_doc = resp.text()
    cache.set(url, html_doc, timedelta(days=1))
    logging.info(f"Cached {url}")

    assert resp.status.as_int() == 200
    return html_doc


if __name__ == "__main__":
    typer.run(main)
