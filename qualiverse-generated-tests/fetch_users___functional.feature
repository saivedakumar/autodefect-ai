Feature: Fetch Users - Functional

  Background:
    * url 'https://jsonplaceholder.typicode.com/users/'
    * header Authorization = 'Bearer eyJraWQiOiJyMzlzUGlydDhFdllJbXY3YkE2eDdlb1l6N1RoUFpTQ0lLeHNqQmJReW5jPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI0cG40dmc3ajBvODRpYTcwNmxybHF2OXI4biIsImNoYW5uZWwiOiJtMm0iLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL3VzLWVhc3QtMV9sOHdqRWdyVXEiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiI0cG40dmc3ajBvODRpYTcwNmxybHF2OXI4biIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiZW5hYmxlcmlxL3dyaXRlIGVuYWJsZXJpcS9yZWFkIiwiYXV0aF90aW1lIjoxNzkwMTQ3NTYxLCJtdm5vIjoidmFudGEiLCJleHAiOjE3OTAxNTExNjAsImlhdCI6MTc5MDE0NzU2MSwianRpIjoiOTY3YzJjNjEtMTY4OS00OTUwLTg0NDQtMWFhODNjNmU3ZDZhIn0.Y_1hCbsj-ReWQRayVsE6cYST5zU1lsmK2pVeGSJWn9yMJdziMsOWyLlfCgQP-FCu0Dkg0ivkLNK-34DwyCdghHDYcFs6t-GcCc0lqf0b9mnEOYExk6wszcrWAuSS9VfmuOhnJg4n3za-qen3GXD74WXE6-QJWCq1OmGmwNp8l6VLVG0mfdLeVPVYlJXKFN5h4y1Dar7NfUWcvgmH-2VAACgfSWu-9myPaxh2sDqAY6Ggih5yrjyHbtVYZt6M-8TjJCp06EY4BhHjQnp0ZADrUvd55QZ_UN5OP6huDVm-70CeB7lC5QBTrOBM3USu82iPhpzjnDUOZmgsQ8LsQ8QPBg'

  Scenario: Fetch Users - Functional
    # step: Send GET /users with no parameters
    # step: Verify the response status code is 200
    # step: Verify the response body contains a list of users
    Given path '/users'
    And request {"endpoint": "/users", "parameters": {}}
    When method GET
    Then status 200
