Feature: API health check
  As an operator I want a health endpoint
  so that load balancers and container orchestration can verify the service is up.

  Scenario: Health endpoint returns OK
    Given the sky API is running
    When I GET "/api/health"
    Then the response status is 200
    And the response contains "ok"
