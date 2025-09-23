import typing as t
import asyncio

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
    Label,
)
from textual.message import Message
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.reactive import reactive
from cache3 import DiskCache
from parsel import Selector

from genxpath._io import http_get
from genxpath._gen import find_xpaths_for, minimize_xpath
from genxpath._browser import WebBrowser


class FindValueInput(Input):
    BORDER_TITLE = "Find xpath to value"
    DEFAULT_CSS = """
    FindValueInput {
        border: solid $primary-background-lighten-2;
        border-title-align: center;
        margin: 1 1;
    }
    """


class QueryXpath(Static):
    BORDER_TITLE = "Query xpath"
    DEFAULT_CSS = """
    QueryXpath {
        border: solid $primary-background-lighten-2;
        border-title-align: center;
        margin: 1 1;
    }
    """

    doc: reactive[Selector | None] = reactive(None)

    class SelectedHtmlElements(Message):
        def __init__(self, elements: list[Selector]):
            self.elements = elements
            super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Minimize", tooltip="Find a shorter XPath")
            yield Input(placeholder="//*[@id='product']")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.doc:
            self.notify("No document loaded")
            return

        xpath = event.value
        try:
            elements = self.doc.xpath(xpath)
            self.post_message(self.SelectedHtmlElements(elements))
        except ValueError:
            self.notify("Invalid XPath: " + xpath, markup=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.doc:
            self.notify("No document loaded")
            return

        curr_xpath = self.query_one(Input).value
        if not curr_xpath:
            self.notify("No XPath provided", severity="warning")
            return

        min_xpath = minimize_xpath(self.doc, curr_xpath)
        self.query_one(Input).value = min_xpath


class Controls(Static):
    loaded_doc: reactive[Selector | None] = reactive(None)

    class LoadingUrl(Message):
        def __init__(self, url: str):
            self.url = url
            super().__init__()

    class LoadedHtml(Message):
        def __init__(self, html: str):
            self.html = html
            super().__init__()

    class FoundXpaths(Message):
        def __init__(self, xpaths: list[str]):
            self.xpaths = xpaths
            super().__init__()

    def __init__(self, cache: DiskCache, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

        self._cache = cache

    def compose(self) -> ComposeResult:
        self._url_input = Input(placeholder="URL or file path", id="url-input")
        yield self._url_input
        yield FindValueInput(
            placeholder="Sample text in the document", id="value-input"
        )
        yield QueryXpath()

    def on_mount(self) -> None:
        # If it stays focused, for some reasons some random characters are inserted
        self._url_input.blur()

        if last_url := self._cache.get("last_url_loaded"):
            self._url_input.value = last_url
            self._fetch_html(last_url)

    def watch_loaded_doc(self, loaded_doc: Selector | None) -> None:
        self.query_one(QueryXpath).doc = loaded_doc

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            self._fetch_html(event.value)
        elif event.input.id == "value-input" and event.value:
            self._find_xpaths(event.value)

    def load_html(self, html: str) -> None:
        self.loaded_doc = Selector(text=html)
        self.post_message(self.LoadedHtml(html))

    def _fetch_html(self, url: str) -> None:
        self.post_message(self.LoadingUrl(url))

        try:
            html_doc = http_get(url, self._cache)
            self.load_html(html_doc)
            self._cache.set("last_url_loaded", url)
        except Exception as e:
            self.notify("Error fetching HTML: " + str(e), markup=False)

    def _find_xpaths(self, value: str) -> None:
        if not self.loaded_doc:
            self.notify("No document loaded")
            return

        xpaths = find_xpaths_for(value, self.loaded_doc)
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

    def __init__(self, *args, open_web_browser: bool = False, **kwargs):
        super().__init__(*args, **kwargs)

        self._web_browser = WebBrowser() if open_web_browser else None
        self._cache = DiskCache("cache")
        self.theme = "solarized-light"

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical():
            with Horizontal():
                yield Controls(self._cache)
                yield ViewHtml()

            self._xpath_from_browser = Label("")
            yield self._xpath_from_browser

        yield Footer()

    async def on_mount(self) -> None:
        if self._web_browser:
            await self._web_browser.start()

        self.run_worker(self._on_js_events)

    async def _on_js_events(self) -> None:
        """Listen to JavaScript events from the web browser and send them to the app."""
        if not self._web_browser:
            return

        while True:
            try:
                event = await self._web_browser.events.get()
                match event["event"]:
                    case "html_loaded":
                        self.query_one(Controls).load_html(event["html"])
                    case "element_hover":
                        min_xpath = event["xpath"]

                        # TODO: move loaded_doc ownership to the App instance?
                        if doc := self.query_one(Controls).loaded_doc:
                            try:
                                min_xpath = minimize_xpath(doc, event["xpath"])
                            except ValueError:
                                ...

                        self._xpath_from_browser.update(
                            Text(f"{event['xpath']} -> {min_xpath}")
                        )

            except asyncio.CancelledError:
                break

    def on_controls_loading_url(self, event: Controls.LoadingUrl) -> None:
        self.query_one(ViewHtml).update_html("Loading...")

    def on_controls_loaded_html(self, event: Controls.LoadedHtml) -> None:
        self.query_one(ViewHtml).update_html(f"```html\n{event.html}\n```")

    def on_controls_found_xpaths(self, event: Controls.FoundXpaths) -> None:
        self.query_one(ViewHtml).list_xpaths(event.xpaths)

    def on_query_xpath_selected_html_elements(
        self, event: QueryXpath.SelectedHtmlElements
    ) -> None:
        self.query_one(ViewHtml).list_html_elements(event.elements)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


app = XpathGenerator(open_web_browser=True)

if __name__ == "__main__":
    app.run()
