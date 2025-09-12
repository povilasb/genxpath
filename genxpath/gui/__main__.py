import typing as t
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Header,
    Static,
    Input,
    Markdown,
    Button,
    DataTable,
)
from textual.message import Message
from textual.containers import VerticalScroll, Horizontal, Vertical
from cache3 import DiskCache
from parsel import Selector

from genxpath._io import http_get
from genxpath._gen import find_xpaths_for


class FindValueInput(Input):
    BORDER_TITLE = "Find xpath to value"
    DEFAULT_CSS = """
    FindValueInput {
        border: solid $primary-background-lighten-2;
        border-title-align: center;
        margin: 1 1;
    }
    """


class QueryXpath(Horizontal):
    BORDER_TITLE = "Query xpath"
    DEFAULT_CSS = """
    QueryXpath {
        border: solid $primary-background-lighten-2;
        border-title-align: center;
        margin: 1 1;
    }
    """


class Controls(Static):
    class LoadingUrl(Message):
        def __init__(self, url: str):
            self.url = url
            super().__init__()

    class LoadedHtml(Message):
        def __init__(self, html: str):
            self.html = html
            super().__init__()

    class SelectedHtmlElements(Message):
        def __init__(self, elements: list[Selector]):
            self.elements = elements
            super().__init__()

    class FoundXpaths(Message):
        def __init__(self, xpaths: list[str]):
            self.xpaths = xpaths
            super().__init__()

    def __init__(self, cache: DiskCache, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

        self._cache = cache
        self._loaded_doc: Selector | None = None

    def compose(self) -> ComposeResult:
        yield Input(
            value=self._cache.get("last_url_loaded"),
            placeholder="URL or file path",
            id="url-input",
        )
        yield FindValueInput(
            placeholder="Sample text in the document", id="value-input"
        )
        yield QueryXpath(
            Button("Minimize", tooltip="Find a shorter XPath"),
            Input(placeholder="//*[@id='product']", id="xpath-input"),
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            self._fetch_html(event.value)
        elif event.input.id == "xpath-input" and event.value:
            self._query_xpath(event.value)
        elif event.input.id == "value-input" and event.value:
            self._query_xpath_for_value(event.value)

    # TODO: minimize xpath from full path

    def _fetch_html(self, url: str) -> None:
        self.post_message(self.LoadingUrl(url))

        try:
            html_doc = http_get(url, self._cache)
        except Exception as e:
            self.notify("Error fetching HTML: " + str(e), markup=False)
            return

        self.post_message(self.LoadedHtml(html_doc))
        self._loaded_doc = Selector(text=html_doc)

        self._cache.set("last_url_loaded", url)

    def _query_xpath(self, xpath: str) -> None:
        if not self._loaded_doc:
            return

        try:
            elements = self._loaded_doc.xpath(xpath)
            self.post_message(self.SelectedHtmlElements(elements))
        except ValueError:
            self.notify("Invalid XPath: " + xpath, markup=False)

    def _query_xpath_for_value(self, value: str) -> None:
        if not self._loaded_doc:
            return

        xpaths = find_xpaths_for(value, self._loaded_doc)
        self.post_message(self.FoundXpaths(xpaths))


class ViewHtml(Static):
    DEFAULT_CSS = """
    VerticalScroll {
        height: 50%;
    }

    DataTable {
        height: 50%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with VerticalScroll():
                yield Markdown()

            yield DataTable(name="HTML elements")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Nr.", "Element")

    def update_html(self, html: str) -> None:
        self.query_one(Markdown).update(html)

    def list_html_elements(self, elements: list[Selector]) -> None:
        table = self.query_one(DataTable)
        table.clear()
        for i, el in enumerate(elements):
            table.add_row(i, el.get())

    def list_xpaths(self, xpaths: list[str]) -> None:
        table = self.query_one(DataTable)
        table.clear()

        for i, xpath in enumerate(xpaths):
            table.add_row(i, Text(xpath))


class XpathGenerator(App):
    """A Textual app to manage stopwatches."""

    TITLE = "genxpath"
    SUB_TITLE = "Find XPaths for data in HTML"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+shift+q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    Vertical {
        width: 1fr;
    }

    Controls {
        border: solid $primary-background-lighten-2;
        width: 10fr;
        height: 1fr;
    }

    Controls:focus-within {
        border: double $primary-lighten-2;
    }

    ViewHtml {
        width: 10fr;
        height: 1fr;
        border: solid $primary-background-lighten-2;
    }

    ViewHtml:focus-within {
        border: double $primary-lighten-2;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._cache = DiskCache("cache")
        self.theme = "textual-light"
        self._loaded_doc: Selector | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical():
            with Horizontal():
                yield Controls(self._cache)
                yield ViewHtml()

            # with TabPane("Find values"):
            #     yield Input(placeholder="Value", id="find-value-input")
            #     yield DataTable(name="XPaths")

        yield Footer()

    def on_controls_loading_url(self, event: Controls.LoadingUrl) -> None:
        self.query_one(ViewHtml).update_html("Loading...")

    def on_controls_loaded_html(self, event: Controls.LoadedHtml) -> None:
        self.query_one(ViewHtml).update_html(f"```html\n{event.html}\n```")

    def on_controls_selected_html_elements(
        self, event: Controls.SelectedHtmlElements
    ) -> None:
        self.query_one(ViewHtml).list_html_elements(event.elements)

    def on_controls_found_xpaths(self, event: Controls.FoundXpaths) -> None:
        self.query_one(ViewHtml).list_xpaths(event.xpaths)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = XpathGenerator()
    app.run()
