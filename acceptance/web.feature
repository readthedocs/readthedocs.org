

Feature: View projects

  Scenario: View a list of projects
    When I view /projects
    Then I should see a list of projects
