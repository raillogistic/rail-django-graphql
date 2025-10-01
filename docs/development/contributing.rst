Contributing
============

Welcome to Django GraphQL Auto! We're excited that you're interested in contributing to our project. This guide will help you get started with contributing code, documentation, and other improvements.

Code of Conduct
---------------

By participating in this project, you agree to abide by our Code of Conduct. We are committed to providing a welcoming and inclusive environment for all contributors.

**Our Standards:**

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior:**

- Harassment, trolling, or discriminatory comments
- Personal attacks or insults
- Publishing private information without permission
- Any conduct that would be inappropriate in a professional setting

Getting Started
---------------

Development Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fork and Clone the Repository**

.. code-block:: bash

   git clone https://github.com/yourusername/django-graphql-auto.git
   cd django-graphql-auto

2. **Set Up Virtual Environment**

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependencies**

.. code-block:: bash

   pip install -e ".[dev]"
   pip install -r requirements-dev.txt

4. **Set Up Pre-commit Hooks**

.. code-block:: bash

   pre-commit install

5. **Run Tests to Verify Setup**

.. code-block:: bash

   pytest
   coverage run -m pytest
   coverage report

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Create a Feature Branch**

.. code-block:: bash

   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description

2. **Make Your Changes**

   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass

3. **Commit Your Changes**

.. code-block:: bash

   git add .
   git commit -m "feat: add new feature description"
   # Follow conventional commit format

4. **Push and Create Pull Request**

.. code-block:: bash

   git push origin feature/your-feature-name

Types of Contributions
----------------------

Code Contributions
~~~~~~~~~~~~~~~~~~

**Bug Fixes:**
- Fix existing issues and improve stability
- Add regression tests to prevent future occurrences
- Update documentation if behavior changes

**New Features:**
- Implement new functionality requested by the community
- Ensure backward compatibility when possible
- Include comprehensive tests and documentation

**Performance Improvements:**
- Optimize existing code for better performance
- Add benchmarks to measure improvements
- Document performance gains and trade-offs

Documentation Contributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**API Documentation:**
- Improve docstrings and type hints
- Add examples and usage patterns
- Update reference documentation

**Tutorials and Guides:**
- Create step-by-step tutorials
- Write how-to guides for common use cases
- Improve existing documentation clarity

**Translation:**
- Translate documentation to other languages
- Maintain consistency across translations
- Update translations when content changes

Testing Contributions
~~~~~~~~~~~~~~~~~~~~~

**Test Coverage:**
- Add tests for uncovered code paths
- Improve test quality and reliability
- Add integration and end-to-end tests

**Test Infrastructure:**
- Improve testing tools and utilities
- Add performance and load testing
- Enhance CI/CD pipeline

Coding Standards
----------------

Python Code Style
~~~~~~~~~~~~~~~~~

We follow PEP 8 with some modifications:

.. code-block:: python

   # Good: Clear, descriptive names
   def generate_graphql_schema_from_models(models_list):
       """Generate GraphQL schema from Django models."""
       pass
   
   # Good: Type hints
   from typing import List, Optional, Dict, Any
   
   def process_query_results(
       results: List[Dict[str, Any]], 
       filters: Optional[Dict[str, Any]] = None
   ) -> List[Dict[str, Any]]:
       """Process query results with optional filtering."""
       pass

**Code Formatting:**
- Use `black` for code formatting
- Use `isort` for import sorting
- Maximum line length: 88 characters
- Use double quotes for strings

**Naming Conventions:**
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

Documentation Style
~~~~~~~~~~~~~~~~~~~

**Docstring Format:**

.. code-block:: python

   def complex_function(param1: str, param2: Optional[int] = None) -> bool:
       """
       Brief description of what the function does.
       
       Longer description explaining the purpose, behavior, and any
       important details about the function.
       
       Args:
           param1: Description of the first parameter
           param2: Description of the optional parameter, defaults to None
           
       Returns:
           bool: True if successful, False otherwise
           
       Raises:
           ValueError: When param1 is empty or invalid
           ConnectionError: When external service is unavailable
           
       Example:
           >>> complex_function("test", 42)
           True
           
           >>> complex_function("")
           Traceback (most recent call last):
           ValueError: param1 cannot be empty
       """
       pass

**Comment Guidelines:**
- Use comments to explain "why", not "what"
- Keep comments up-to-date with code changes
- Use TODO comments for future improvements
- Avoid obvious comments

Testing Guidelines
------------------

Test Structure
~~~~~~~~~~~~~~

**Test Organization:**

.. code-block:: text

   tests/
   ├── unit/                 # Unit tests
   │   ├── test_models.py
   │   ├── test_schema.py
   │   └── test_resolvers.py
   ├── integration/          # Integration tests
   │   ├── test_api.py
   │   └── test_database.py
   ├── e2e/                  # End-to-end tests
   │   └── test_workflows.py
   └── fixtures/             # Test data and fixtures
       ├── models.py
       └── sample_data.json

**Test Naming:**

.. code-block:: python

   class TestSchemaGeneration:
       def test_should_generate_schema_for_simple_model(self):
           """Test schema generation for a model with basic fields."""
           pass
       
       def test_should_handle_foreign_key_relationships(self):
           """Test schema generation for models with foreign keys."""
           pass
       
       def test_should_raise_error_for_invalid_model(self):
           """Test error handling for invalid model configurations."""
           pass

Writing Good Tests
~~~~~~~~~~~~~~~~~~

**Test Structure (AAA Pattern):**

.. code-block:: python

   def test_user_creation_with_valid_data(self):
       """Test user creation with valid input data."""
       # Arrange
       user_data = {
           'username': 'testuser',
           'email': 'test@example.com',
           'password': 'securepassword123'
       }
       
       # Act
       user = create_user(user_data)
       
       # Assert
       assert user.username == 'testuser'
       assert user.email == 'test@example.com'
       assert user.check_password('securepassword123')

**Test Coverage Requirements:**
- Minimum 90% code coverage for new code
- 100% coverage for critical paths
- Include edge cases and error conditions
- Test both positive and negative scenarios

**Mocking and Fixtures:**

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   
   @pytest.fixture
   def sample_user():
       """Fixture providing a sample user for testing."""
       return User.objects.create(
           username='testuser',
           email='test@example.com'
       )
   
   @patch('django_graphql_auto.external_service.api_call')
   def test_external_api_integration(mock_api_call, sample_user):
       """Test integration with external API service."""
       mock_api_call.return_value = {'status': 'success'}
       
       result = process_user_data(sample_user)
       
       assert result['status'] == 'success'
       mock_api_call.assert_called_once()

Pull Request Process
--------------------

Before Submitting
~~~~~~~~~~~~~~~~~

**Pre-submission Checklist:**

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated for changes
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts with main branch
- [ ] Pre-commit hooks pass

**Commit Message Format:**

.. code-block:: text

   type(scope): description
   
   [optional body]
   
   [optional footer]

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

.. code-block:: text

   feat(schema): add support for custom scalar types
   
   - Implement CustomScalarType class
   - Add validation for scalar type definitions
   - Update schema generation to handle custom scalars
   
   Closes #123

   fix(resolver): handle null values in nested relationships
   
   Previously, null foreign key values would cause resolver
   to crash. Now properly handles null values by returning
   None for the relationship field.
   
   Fixes #456

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

**PR Title and Description:**
- Use clear, descriptive titles
- Reference related issues
- Explain the motivation for changes
- Describe the solution approach
- List any breaking changes

**PR Template:**

.. code-block:: markdown

   ## Description
   Brief description of changes and motivation.
   
   ## Type of Change
   - [ ] Bug fix (non-breaking change that fixes an issue)
   - [ ] New feature (non-breaking change that adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing performed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added and passing
   
   ## Related Issues
   Closes #123
   Related to #456

Review Process
~~~~~~~~~~~~~~

**What Reviewers Look For:**
- Code quality and maintainability
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Backward compatibility

**Addressing Review Feedback:**
- Respond to all review comments
- Make requested changes promptly
- Ask for clarification if needed
- Update tests and documentation as requested
- Re-request review after changes

Community Guidelines
--------------------

Communication Channels
~~~~~~~~~~~~~~~~~~~~~~

**GitHub Issues:**
- Bug reports and feature requests
- Technical discussions
- Project planning and roadmap

**GitHub Discussions:**
- General questions and help
- Ideas and brainstorming
- Community announcements

**Discord/Slack:**
- Real-time chat and collaboration
- Quick questions and support
- Community events and meetings

**Email:**
- Security vulnerability reports
- Private communications with maintainers

Issue Reporting
~~~~~~~~~~~~~~~

**Bug Reports:**

.. code-block:: markdown

   **Bug Description**
   Clear description of the bug and expected behavior.
   
   **Steps to Reproduce**
   1. Step one
   2. Step two
   3. Step three
   
   **Environment**
   - Django GraphQL Auto version: x.x.x
   - Django version: x.x.x
   - Python version: x.x.x
   - Operating System: xxx
   
   **Additional Context**
   Any additional information, logs, or screenshots.

**Feature Requests:**

.. code-block:: markdown

   **Feature Description**
   Clear description of the proposed feature.
   
   **Use Case**
   Explain why this feature would be useful.
   
   **Proposed Solution**
   Describe how you envision the feature working.
   
   **Alternatives Considered**
   Any alternative solutions you've considered.

Recognition and Attribution
---------------------------

**Contributor Recognition:**
- All contributors are listed in CONTRIBUTORS.md
- Significant contributions are highlighted in release notes
- Contributors can add themselves to the contributors list

**Attribution Guidelines:**
- Credit original authors when building on existing work
- Reference related issues and discussions
- Acknowledge reviewers and testers

Getting Help
------------

**For New Contributors:**
- Check the "good first issue" label on GitHub
- Join our Discord for real-time help
- Read through existing code and documentation
- Start with small contributions

**For Experienced Contributors:**
- Look for "help wanted" issues
- Propose new features and improvements
- Help review other contributors' work
- Mentor new contributors

**Resources:**
- `Developer Guide <developer-guide.html>`_
- `Testing Guide <testing.html>`_
- `Performance Guide <performance.html>`_
- `API Reference <../api/index.html>`_

Thank You!
----------

Thank you for contributing to Django GraphQL Auto! Your contributions help make this project better for everyone. Whether you're fixing bugs, adding features, improving documentation, or helping other users, every contribution is valuable and appreciated.

---

*For questions about contributing, please reach out to us on GitHub Discussions or Discord.*