from crawler.naver_store import NaverStoreCrawler


def test_parse_embedded_json_from_sample_html():
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"initialState": {"products": [
            {"item": {"id": 1001, "productName": "A", "price": 1000, "reviewCount": 10}},
            {"item": {"id": 1002, "productName": "B", "price": 2000, "reviewCount": 20}}
          ]}}}}
        </script>
      </body>
    </html>
    """
    products = NaverStoreCrawler.parse_embedded_json(html)
    assert [product.product_id for product in products] == ["1001", "1002"]
    assert products[0].name == "A"
    assert products[1].price == 2000


def test_parse_embedded_json_from_nested_structure():
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"dehydratedState": {
            "queries": [{"state": {"data": {"content": [
              {"item": {"id": 2001, "productName": "Nested", "price": 5550, "reviewCount": 5}}
            ]}}}]}}}}
        </script>
      </body>
    </html>
    """
    products = NaverStoreCrawler.parse_embedded_json(html)
    assert [product.product_id for product in products] == ["2001"]
    assert products[0].name == "Nested"
