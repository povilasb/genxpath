import pytest
from genxpath._gen import find_xpaths, minimize_xpath
from cache3 import DiskCache


@pytest.fixture
def cache() -> DiskCache:
    return DiskCache("cache")


class TestFindXpaths:
    def test_by_id(self):
        html_doc = """
        <html><body>
        <div class="product">
            <span class="price" id="sales-price">€199.99</span>
        </div>
        <div class="product">
            <span class="price">€299.99</span>
        </div>
        </body></html>
        """

        xpaths = find_xpaths({"price": "€199.99"}, html_doc)

        assert xpaths["price"] == ["//*[@id='sales-price']/text()"]

    def test_in_attr(self):
        html_doc = """
        <html><body>
        <div class="product">
            <span class="price" data-price="199.99">€199.99</span>
        </div>
        </body></html>
        """

        xpaths = find_xpaths({"price": "199.99"}, html_doc)

        assert xpaths["price"] == ["//*[@class='price']/@data-price"]

    def test_when_parent_is_unique(self):
        html_doc = """
        <html><body>
        <div class="product">
            <p class="price">
                <span>199.99 eur</span>
            </p>
        </div>
        </body></html>
        """

        xpaths = find_xpaths({"price": "199.99 eur"}, html_doc)

        assert xpaths["price"] == ["//*[@class='price']/span/text()"]


class TestMinimizeXpath:
    def test_by_id(self, cache: DiskCache):
        html_doc = """
        <html><body>
        <div class="product">
            <span>Trek Fx 1</span>
            <span class="price" id="sales-price">300.00</span>
        </div>
        </body></html>
        """

        cache.set("last_url_loaded", "https://local.test/test_by_id")
        cache.set("https://local.test/test_by_id", html_doc)

        min_xpath = minimize_xpath(html_doc, "/html/body/div/span[2]")

        assert min_xpath == "//*[@id='sales-price']"

    def test_xpath_with_text_selector(self, cache: DiskCache):
        html_doc = """
        <html><body>
        <div class="product">
            <span>Trek Fx 1</span>
            <span class="price" id="sales-price">300.00</span>
        </div>
        </body></html>
        """

        cache.set("last_url_loaded", "https://local.test/test_by_id")
        cache.set("https://local.test/test_by_id", html_doc)

        min_xpath = minimize_xpath(html_doc, "/html/body/div/span[2]/text()")

        assert min_xpath == "//*[@id='sales-price']/text()"
