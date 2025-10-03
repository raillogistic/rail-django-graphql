# Installation

## Prerequisites
- Python 3.10+
- Pip
- Virtualenv (recommended)

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements/base.txt`
3. Apply migrations:
   - `python manage.py migrate`
4. Run development server:
   - `python manage.py runserver`

## Library Installation
This boilerplate installs `rail-django-graphql` directly from GitHub, pinned to `v1.0.0`.
The requirement line is in `requirements/base.txt`.