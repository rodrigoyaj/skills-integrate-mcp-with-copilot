# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities with authenticated accounts
- Role-based enrollment controls for students, parents, teachers, coordinators, and admins

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/register`                                                   | Create a student or parent account                                  |
| POST   | `/auth/login`                                                      | Log in and receive a bearer token                                   |
| POST   | `/auth/logout`                                                     | Revoke the current bearer token                                     |
| GET    | `/auth/me`                                                         | Get the current user's email and role                               |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (authentication required)                  |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister (authentication required)                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data, users, and sessions are stored in memory, which means they will be reset when the server restarts. A demo teacher account is `teacher@mergington.edu` / `teacherpass`.
