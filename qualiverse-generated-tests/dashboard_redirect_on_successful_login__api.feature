Feature: Dashboard Redirect on Successful Login (API)

  Background:
    * url 'http://localhost:8085'


  Scenario: Dashboard Redirect on Successful Login (API)
    # step: Navigate to the login page.
    # step: Enter valid username and password.
    # step: Click the 'Login' button.
    # step: The user should be redirected to the dashboard.
    Given path '/'
    And request {"username": "validUsername", "password": "validPassword"}
    When method GET
    Then status 200
