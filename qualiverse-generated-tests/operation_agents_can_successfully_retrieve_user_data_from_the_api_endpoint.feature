Feature: Operation agents can successfully retrieve user data from the API endpoint.

  Background:
    * url 'https://jsonplaceholder.typicode.com/users/'


  Scenario: Operation agents can successfully retrieve user data from the API endpoint.
    # step: Send GET /users with no parameters
    # step: Verify the response status code is 200
    # step: Check the response body contains the expected user data
    Given path '/users'
    And request {"username": "john_doe", "email": "john.doe@example.com", "password": "password123", "role": "agent"}
    When method GET
    Then status 200
