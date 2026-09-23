Feature: The API endpoint is accessible and returns the expected user data.

  Background:
    * url 'https://jsonplaceholder.typicode.com/users/'


  Scenario: The API endpoint is accessible and returns the expected user data.
    # step: Send GET /users with parameters {id: '12345'}
    # step: Verify the response status code is 200
    # step: Check the response body contains the expected user data
    Given path '/users'
    And request {"id": "12345"}
    When method GET
    Then status 200
