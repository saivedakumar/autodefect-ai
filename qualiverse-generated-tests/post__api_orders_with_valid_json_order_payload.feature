Feature: POST /api/orders with valid JSON order payload

  Background:
    * url 'http://localhost:8085'


  Scenario: POST /api/orders with valid JSON order payload
    # step: Navigate to the POST /api/orders endpoint.
    # step: Submit a valid JSON order payload with the following fields: customer_id, items, and total.
    # step: The payload should be in the following format: { 'customer_id': '12345', 'items': ['item1', 'item2'], 'total': 100.50 }.
    Given path '/api/orders'
    And request {"customer_id": "12345", "items": ["item1", "item2"], "total": 100.5}
    When method POST
    Then status 200
