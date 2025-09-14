import typer
from parsel import Selector
from pathlib import Path
from genxpath._gen import find_xpaths_for, minimize_xpath
import rich
from rich.console import Console
from rich.logging import RichHandler
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
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

    _run_shell(html_doc)


def _run_shell(html_doc: str):
    doc = Selector(text=html_doc)

    print("HELP:")
    print("   q - query xpath")
    print("   m - minimize xpath")
    print("   f - find xpath by value")
    print("   d - print loaded document")

    history = InMemoryHistory()
    auto_complete = WordCompleter(["q", "m", "f"])
    shell_session = PromptSession[str](history=history, completer=auto_complete)

    while True:
        prompt = shell_session.prompt("> ")
        if prompt == "d":
            cmd = "d"
        else:
            cmd, args = prompt.split(maxsplit=1)

        match cmd:
            case "q":
                _query_xpath(doc, args)
            case "m":
                print(minimize_xpath(doc, args))
            case "f":
                for xpath in find_xpaths_for(args, doc):
                    print(xpath)
            case "d":
                rich.print(html_doc)
            case _:
                logging.error(f"Invalid command: {cmd}")


def _query_xpath(doc: Selector, xpath: str):
    try:
        elements = doc.xpath(xpath)
        for i, el in enumerate(elements):
            rich.print(f"{i}: {el.get()}")
    except ValueError:
        logging.error(f"Invalid XPath: {xpath}")


if __name__ == "__main__":
    typer.run(main)
