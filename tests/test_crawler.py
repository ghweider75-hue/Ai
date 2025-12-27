from crawler.naver_store import NaverStoreCrawler


def test_parse_embedded_json_from_sample_html():
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"initialState": {"products": [
            {"item": {"id": 1001, "productName": "A", "price": "1,000", "reviewCount": 10}},
            {"item": {"id": 1002, "productName": "B", "price": 2000, "reviewCount": 20}}
          ]}}}}
        </script>
      </body>
    </html>
    """
    products = NaverStoreCrawler.parse_embedded_json(html)
    assert [product.product_id for product in products] == ["1001", "1002"]
    assert products[0].name == "A"
    assert products[0].price == 1000
    assert products[1].price == 2000


def test_parse_embedded_json_from_nested_structure():
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"dehydratedState": {
            "queries": [{"state": {"data": {"content": [
              {"item": {"id": 2001, "productName": "Nested", "price": 5550, "reviewCount": 5, "purchaseCnt": null}}
            ]}}}]}}}}
        </script>
      </body>
    </html>
    """
    products = NaverStoreCrawler.parse_embedded_json(html)
    assert [product.product_id for product in products] == ["2001"]
    assert products[0].name == "Nested"
    assert products[0].purchase_count is None


def test_parse_embedded_json_uses_next_data_script_id():
    html = """
    <html>
      <body>
        <script>console.log("ignore me")</script>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"initialState": {"products": [
            {"item": {"id": 3001, "productName": "Pick", "price": 900, "reviewCount": 3}}
          ]}}}}
        </script>
      </body>
    </html>
    """
    products = NaverStoreCrawler.parse_embedded_json(html)
    assert [product.product_id for product in products] == ["3001"]


def test_parse_embedded_json_missing_payload_returns_empty():
    html = "<html><body><script>var x = 1;</script></body></html>"
    assert NaverStoreCrawler.parse_embedded_json(html) == []
