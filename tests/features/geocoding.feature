Feature: Location geocoding
  As a user I want to resolve an address to coordinates
  so that the system can compute the night sky for that location.

  Background:
    Given the sky API is running

  Scenario: Valid Korean road address
    Given the address "서울특별시 종로구 창경궁로 185"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And the response contains "context"
    And the latitude is between 33.0 and 38.5
    And the longitude is between 125.0 and 130.0

  Scenario: Valid international address
    Given the address "New York, USA"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And the latitude is between 40.0 and 41.5
    And the longitude is between -75.0 and -73.0

  Scenario: Unresolvable address
    Given the address "asdfghjkl xyzzy qwerty"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 422
    And the response contains "error"

  Scenario: Invalid datetime format
    Given the address "Seoul, Korea"
    And the datetime "not-a-date"
    When I POST to "/api/sky"
    Then the response status is 422
