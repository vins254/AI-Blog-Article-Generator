"""
=============================================================================
FILE: server/blog_generator/tests.py
PURPOSE: The test suite for the blog_generator application. Test cases live
         here and are run with the command `python manage.py test`.
=============================================================================

HOW IT WORKS:
- Django's test runner discovers all classes that inherit from TestCase in
  files named tests.py across the project.
- Each test method (must start with `test_`) is run in isolation, with a
  clean temporary database created and destroyed for every test run.
- This means tests never pollute each other or the real database.

WHAT TO TEST HERE (suggested test cases to add):
  - Test that the /login page returns HTTP 200 for anonymous users.
  - Test that the / (dashboard) redirects to /login for anonymous users.
  - Test that user_signup creates a User record in the database.
  - Test that generate_blog returns 405 for a GET request.
  - Test that generate_blog returns 400 for an invalid URL.
  - Test that blog_details returns 404 when accessing another user's article.

TOOLS:
  - django.test.TestCase: Base class that wraps each test in a database
    transaction and rolls it back afterward, keeping tests isolated.
  - self.client: A built-in test HTTP client that simulates browser requests
    without needing a real server running.
  - Run tests: `python manage.py test blog_generator`
=============================================================================
"""
from django.test import TestCase


# Create your tests here.
