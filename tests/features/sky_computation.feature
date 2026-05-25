Feature: Sky computation
  As a user I want accurate stellar positions and constellation data
  so that the chart reflects the real night sky.

  Background:
    Given the sky API is running

  Scenario: Stars above horizon only
    Given the address "Seoul, Korea"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And all returned stars have alt_deg >= 0
    And all returned stars have magnitude <= 6.5

  Scenario: Orion visible from Seoul in January 2000
    Given the address "Seoul, Korea"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And a star with hip 27989 is present in the results
    And the constellation "Ori" is present in constellation_lines

  Scenario: Constellation lines reference visible stars only
    Given the address "Seoul, Korea"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And all constellation lines reference stars present in the star list

  Scenario: Constellation positions use circular azimuth mean
    Given the address "Seoul, Korea"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And all constellation_positions have az_deg between 0 and 360
    And all constellation_positions have alt_deg >= 0

  Scenario: Timezone conversion — Seoul midnight becomes 15:00 previous day UTC
    Given the address "Seoul, Korea"
    And the datetime "2000-01-01 00:00"
    When I POST to "/api/sky"
    Then the response status is 200
    And the utc_dt starts with "1999-12-31T15:00"
