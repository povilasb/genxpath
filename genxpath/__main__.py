import typer
from parsel import Selector
from pathlib import Path
from genxpath._gen import find_xpaths, find_xpaths_for
import rich
from rich.console import Console
from rich.logging import RichHandler
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from cache3 import DiskCache
from genxpath._io import http_get


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=Console(), rich_tracebacks=True)],
)


def main(url: str):
    cache = DiskCache("cache")

    if url.startswith("https://"):
        html_doc = http_get(url, cache)
    else:
        html_doc = Path(url).read_text()

    product = find_xpaths(
        {
            "name": "Parduodamas Trek dviratis",
            "price": "299 €",
            "views": "3",
        },
        html_doc,
    )
    rich.print(product)

    xpaths = find_xpaths_for("Parduodamas Trek dviratis", Selector(text=html_doc))
    rich.print(xpaths)

    _xpath_shell(html_doc)


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


if __name__ == "__main__":
    typer.run(main)
