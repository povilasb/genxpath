from genxpath._gen import find_xpaths
from pydantic import BaseModel


class Product(BaseModel):
    price: str | None = None


def test_find_by_id():
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

    xpaths = find_xpaths(Product(price="€199.99"), html_doc)

    assert xpaths["price"] == ["//*[@id='sales-price']/text()"]


def test_find_in_attr():
    html_doc = """
    <html><body>
    <div class="product">
        <span class="price" data-price="199.99">€199.99</span>
    </div>
    </body></html>
    """

    xpaths = find_xpaths(Product(price="199.99"), html_doc)

    assert xpaths["price"] == ["//*[@class='price']/@data-price"]


def test_find_when_parent_is_unique():
    html_doc = """
    <html><body>
    <div class="product">
        <p class="price">
            <span>199.99 eur</span>
        </p>
    </div>
    </body></html>
    """

    xpaths = find_xpaths(Product(price="199.99 eur"), html_doc)

    assert xpaths["price"] == ["//*[@class='price']/span/text()"]
