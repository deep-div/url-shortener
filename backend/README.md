# URL Shortener — Backend

FastAPI backend for the URL Shortener service.

---

## Prerequisites

- Python **3.13.0**

---

## Setup

### 1. Navigate to the backend directory

```bash
cd backend
```

### 2. Create a virtual environment

```bash
py -m venv .venv
```

### 3. Activate the virtual environment
**Windows (CMD):**
```cmd
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials.

---

## Run the development server

```bash
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API will be available at: `http://127.0.0.1:8000`

Interactive docs: `http://127.0.0.1:8000/docs`
