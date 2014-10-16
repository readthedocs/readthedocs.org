

Feature: Build documentation for projects

  Scenario: View a list of builds for a project
    When I view /builds/pip
    Then I should see a list of builds
