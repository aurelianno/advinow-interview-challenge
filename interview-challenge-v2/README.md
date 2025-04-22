# AdviNow Interview Challenge

This repository demonstrates a FastAPI application with SQLAlchemy models, Alembic migrations, and endpoints to import and query business–symptom data. It also documents the errors encountered and how they were resolved.

## Prerequisites

- **Windows 11**  
- **Python 3.10+**  
- **PostgreSQL** (installed via Windows installer)  
- **Git**

## 1. Clone & Create a Virtual Environment

```powershell
# Clone the repo and navigate
git clone https://gitfront.io/r/user-8330764/24pYzvQfcYBi/interview-challenge-v2.git
cd interview-challenge-v2

# Temporarily allow script execution
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create and activate venv (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
cd requirements
pip install -r requirements.txt
cd ..
```

## 2. Define SQLAlchemy Data Models

Models live in **`app/models.py`**:

- **Business**  
  - `id` (int PK, no auto‑increment—IDs come from CSV)  
  - `name` (str)  
  - `symptoms` relationship to `BusinessSymptom`

- **Symptom**  
  - `code` (str PK, e.g. "SYMPT0001")  
  - `name` (str)  
  - `businesses` relationship to `BusinessSymptom`

- **BusinessSymptom**  
  - composite PK: `(business_id, symptom_code)`  
  - `diagnostic` (bool)  
  - `created_at` & `updated_at` timestamps  
  - FKs to `businesses.id` and `symptoms.code`

These mirror the CSV at `app/data/business_symptom_data.csv`.

## 3. Configure the Database

Create a `.env` in project root:

```ini
DB_HOST=localhost
DB_NAME=postgres
DB_USER=user
DB_PASSWORD=password
```

Verify in **`settings.py`**:

```python
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
```

## 4. Recreate the `public` Schema (if needed)

If you get permission or “no schema selected” errors:

1. Open **pgAdmin 4**, connect as superuser (`postgres`).  
2. Right‑click your DB → **Query Tool**.  
3. Run:

   ```sql
   DROP SCHEMA IF EXISTS public CASCADE;
   CREATE SCHEMA public AUTHORIZATION "user";
   GRANT ALL ON SCHEMA public TO "user";
   GRANT ALL ON SCHEMA public TO PUBLIC;
   ```

## 5. Fix Module Import Errors

If you see `ModuleNotFoundError: No module named 'app'` or similar, ensure **`app/run.py`** reads:

```python
from fastapi import FastAPI
from app.views import router

app = FastAPI(title="AdviNow Interview Challenge", version="1.6")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.run:app", host="127.0.0.1", port=8013, reload=True)
```

## 6. Run Alembic Migrations

From the project root with `.venv` active:

```powershell
python -m alembic revision --autogenerate -m "create business/symptom tables"
python -m alembic upgrade head
```

Confirm in pgAdmin under **Schemas → public → Tables** you have:
- alembic_version  
- businesses  
- symptoms  
- business_symptoms  

## 7. Start the FastAPI Server

```powershell
python -m uvicorn app.run:app --reload --port 8013
```

- Swagger UI: http://127.0.0.1:8013/docs

## 8. Import Business–Symptom Data

### Using Swagger UI

1. Open **`/docs`**.  
2. Expand **POST /import-business-symptoms** → **Try it out**.  
3. Upload `app/data/business_symptom_data.csv` → **Execute**.

Expected response:

```json
{
  "status": "import complete",
  "rows_processed": 12
}
```

## 9. Query the Data with Swagger UI

1. In **`/docs`**, expand **GET /business-symptoms** → **Try it out**.  
2. (Optional) Fill `business_id` and/or toggle `diagnostic`.  
3. Click **Execute** to see the JSON array of mappings.

---

By following these steps in order, you’ll have:
- **SQLAlchemy models** aligned to the CSV  
- **Alembic migrations** setting up your schema  
- **CSV import endpoint** with idempotent upserts  
- **Query endpoint** supporting optional filters  
- **Swagger UI** for all your interactive tests  