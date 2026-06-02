# Scratch Task Manager API 🚀

A robust, production-ready backend for a Task Management (To-Do) application built with **FastAPI**. This project features secure JWT-based authentication, multi-tenant data privacy, and a comprehensive admin system.

## 🌟 Features

-   **User Authentication**: Secure registration and login using `PBKDF2-SHA256` password hashing.
-   **JWT Security**: Stateless authentication using JSON Web Tokens (Bearer Token).
-   **Task Management (CRUD)**: Create, read, update, and delete tasks.
-   **Data Privacy**: Strict ownership logic — users can only access and modify their own tasks.
-   **Admin System**: Advanced permissions for administrators (view all users, delete accounts) via a secret admin registration code.
-   **Auto-Documentation**: Fully interactive API documentation via Swagger UI.
-   **Bulletproof Testing**: 100% coverage of core logic using `Pytest` and an in-memory SQLite database for isolation.

## 🛠 Tech Stack

-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
-   **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
-   **Database**: MySQL (Production), SQLite (Testing)
-   **Security**: Passlib & PyJWT
-   **Validation**: Pydantic v2
-   **Environment Management**: Python-dotenv

## 📋 Requirements

-   Python 3.12+
-   MySQL Server
-   Virtual Environment (venv)

## ⚙️ Setup & Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Buskud0/Scratch.git
    cd Scratch/backend
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv env
    # Linux/macOS:
    source env/bin/activate
    # Windows:
    .\env\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the `backend/` folder:
    ```text
    DATABASE_URL=mysql+pymysql://user:password@localhost/db_name
    SECRET_KEY=your_super_secret_jwt_key
    ADMIN_CODE=your_secret_admin_registration_pass
    ```

5.  **Run the application**:
    ```bash
    fastapi dev main.py
    ```
    Access the API at `http://127.0.0.1:8000` and the interactive docs at `/docs`.

## 🧪 Running Tests

The project includes a suite of integration tests that verify authentication, privacy, and database integrity.

```bash
pytest
```

*Tests use an in-memory SQLite database and do not affect your local MySQL data.*

## 🔗 API Overview

### Authentication
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/users/register` | Register a new user account | None |
| `POST` | `/users/login` | Log in and receive JWT access token | None |

### Tasks
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/tasks` | List all tasks owned by user (filter with `?done=`) | JWT |
| `GET` | `/tasks/{id}` | Get details of a specific owned task | JWT |
| `POST` | `/tasks` | Create a new task | JWT |
| `PATCH` | `/tasks/{id}` | Partially update task title or status | JWT |
| `DELETE` | `/tasks` | Delete all tasks owned by the user | JWT |
| `DELETE` | `/tasks/{id}` | Delete a specific owned task | JWT |

### Users (Administrative)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/users` | List all registered users | JWT (Admin) |
| `GET` | `/users/{id}` | Get profile details for a specific user | JWT (Admin/Self) |
| `PATCH` | `/users/{id}` | Update user details or Admin status | JWT (Admin/Self) |
| `DELETE` | `/users/{id}` | Delete a user account | JWT (Admin/Self) |

## 🛡 Security Notes
- **Password Protection**: No plain-text passwords are ever stored; all are hashed using `PBKDF2-SHA256`.
- **JWT**: Secure stateless session management with configurable expiration.
- **Privacy**: The API uses dependency-injected ownership checks to prevent unauthorized data access between users.

---
*Maintained by [Buskud0](https://github.com/Buskud0)*