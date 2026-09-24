"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from secrets import token_urlsafe
from hashlib import pbkdf2_hmac
from hmac import compare_digest
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

security = HTTPBearer()

# In-memory identity store. Replace with a database-backed store in production.
users = {}
sessions = {}


class UserCredentials(BaseModel):
    email: str
    password: str
    role: str = "student"


class LoginCredentials(BaseModel):
    email: str
    password: str


def hash_password(password: str, salt: bytes) -> str:
    return pbkdf2_hmac("sha256", password.encode(), salt, 120_000).hex()


def create_user(email: str, password: str, role: str) -> None:
    salt = token_urlsafe(16).encode()
    users[email] = {
        "email": email,
        "role": role,
        "salt": salt,
        "password_hash": hash_password(password, salt),
    }


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="A valid email is required")
    return email


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_email = sessions.get(credentials.credentials)
    user = users.get(user_email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_staff(current_user=Depends(get_current_user)):
    if current_user["role"] not in {"teacher", "coordinator", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only teachers and administrators can manage registrations",
        )
    return current_user


# Demo accounts make the role-protected workflow usable immediately.
create_user("teacher@mergington.edu", "teacherpass", "teacher")
create_user("student@mergington.edu", "studentpass", "student")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/register")
def register(credentials: UserCredentials):
    email = normalize_email(credentials.email)
    if email in users:
        raise HTTPException(status_code=409, detail="An account already exists")
    if len(credentials.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )
    if credentials.role not in {"student", "parent"}:
        raise HTTPException(
            status_code=400, detail="Self-registration is limited to students and parents"
        )
    create_user(email, credentials.password, credentials.role)
    return {"message": "Account created", "email": email, "role": credentials.role}


@app.post("/auth/login")
def login(credentials: LoginCredentials):
    email = normalize_email(credentials.email)
    user = users.get(email)
    if not user or not compare_digest(
        hash_password(credentials.password, user["salt"]), user["password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = token_urlsafe(32)
    sessions[token] = email
    return {"access_token": token, "token_type": "bearer", "email": email, "role": user["role"]}


@app.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    sessions.pop(credentials.credentials, None)
    return {"message": f"Logged out {current_user['email']}"}


@app.get("/auth/me")
def current_user(current_user=Depends(get_current_user)):
    return {"email": current_user["email"], "role": current_user["role"]}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    current_user=Depends(get_current_user),
):
    """Sign up a student for an activity"""
    email = normalize_email(email)
    if current_user["role"] == "student" and current_user["email"] != email:
        raise HTTPException(
            status_code=403, detail="Students can only manage their own enrollment"
        )
    if current_user["role"] not in {"student", "parent", "teacher", "coordinator", "admin"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to enroll students")
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    current_user=Depends(get_current_user),
):
    """Unregister a student from an activity"""
    email = normalize_email(email)
    if current_user["role"] == "student" and current_user["email"] != email:
        raise HTTPException(
            status_code=403, detail="Students can only manage their own enrollment"
        )
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
