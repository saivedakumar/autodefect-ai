Feature: POST /api/orders with missing customer_id

  Background:
    * url 'http://localhost:8085'


  Scenario: POST /api/orders with missing customer_id
    # step: Navigate to the POST /api/orders endpoint.
    # step: Submit a valid JSON order payload with the following fields: items and total.
    # step: The payload should be in the following format: { 'items': ['item1', 'item2'], 'total': 100.50 }.
    Given path '/api/orders'
    And request {"items": ["item1", "item2"], "total": 100.5, "customer_id": "missing"}
    When method POST
    Then status 400
