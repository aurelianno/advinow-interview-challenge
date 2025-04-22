from fastapi import APIRouter, Query, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from io import StringIO
import csv

from pydantic import BaseModel

from app.database import SessionLocal
from app.models import Business, Symptom, BusinessSymptom

# As part of my AdviNow interview challenge submission, I group all endpoints
# under a single APIRouter for clean separation.
router = APIRouter()


# ——————————————————————————————————————————————
# Pydantic schema for GET /business-symptoms
# I defined this exactly per spec: it returns Business ID, Business Name,
# Symptom Code, Symptom Name, and the diagnostic flag.
# Using orm_mode allows FastAPI to read directly from SQLAlchemy models.
# ——————————————————————————————————————————————
class BusinessSymptomOut(BaseModel):
    business_id: int
    business_name: str
    symptom_code: str
    symptom_name: str
    diagnostic: bool

    class Config:
        orm_mode = True


# ——————————————————————————————————————————————
# Dependency to provide a fresh database session per request.
# I used SQLAlchemy’s sessionmaker and ensure we close the session
# after each call to avoid connection leaks. This pattern is common
# in production-quality FastAPI apps.
# ——————————————————————————————————————————————
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ——————————————————————————————————————————————
# 1) GET /business-symptoms
#    I join the three tables to return human-readable names and codes.
#    I support two optional query parameters (business_id, diagnostic)
#    as required, and return 404 if nothing matches.
# ——————————————————————————————————————————————
@router.get(
    "/business-symptoms",
    response_model=List[BusinessSymptomOut],
    summary="List business ↔ symptom mappings",
)
def read_business_symptoms(
    business_id: Optional[int]   = Query(None, description="Filter by business ID"),
    diagnostic: Optional[bool]   = Query(None, description="Filter by diagnostic flag"),
    db: Session                  = Depends(get_db),
):
    # Build base query joining the link table to both Business and Symptom
    query = db.query(BusinessSymptom).join(Business).join(Symptom)

    # Apply optional filters if provided by the client
    if business_id is not None:
        query = query.filter(BusinessSymptom.business_id == business_id)
    if diagnostic is not None:
        query = query.filter(BusinessSymptom.diagnostic == diagnostic)

    results = query.all()

    # If no matches, return a 404 per challenge instruction
    if not results:
        raise HTTPException(status_code=404, detail="No business-symptom data found")

    # Convert ORM objects into our Pydantic schema for the response
    return [
        BusinessSymptomOut(
            business_id   = bs.business_id,
            business_name = bs.business.name,
            symptom_code  = bs.symptom_code,
            symptom_name  = bs.symptom.name,
            diagnostic    = bs.diagnostic
        )
        for bs in results
    ]


# ——————————————————————————————————————————————
# 2) POST /import-business-symptoms
#    I accept a CSV file (multipart/form-data) and upsert it into the DB.
#    To avoid duplicate-key errors, I use SQLAlchemy’s merge() and
#    track which rows I've already merged in memory.
#    Finally, I commit once for efficiency.
# ——————————————————————————————————————————————
@router.post("/import-business-symptoms", summary="Import business–symptom data from CSV")
async def import_business_symptoms(
    file: UploadFile = File(..., description="CSV file matching business_symptom_data.csv"),
    db:   Session    = Depends(get_db),
):
    # Read and decode the uploaded file into text
    text   = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.DictReader(StringIO(text))

    # Track seen businesses and symptoms to only schedule one insert per entity
    seen_businesses = set()
    seen_symptoms   = set()
    row_count       = 0

    for row in reader:
        row_count += 1

        # Parse each CSV column, converting types as needed
        biz_id   = int(row["Business ID"])
        biz_name = row["Business Name"].strip()
        sym_code = row["Symptom Code"].strip()
        sym_name = row["Symptom Name"].strip()
        diag     = row["Symptom Diagnostic"].strip().lower() in ("true", "1", "yes")

        # Only upsert each business once
        if biz_id not in seen_businesses:
            db.merge(Business(id=biz_id, name=biz_name))
            seen_businesses.add(biz_id)

        # Only upsert each symptom once
        if sym_code not in seen_symptoms:
            db.merge(Symptom(code=sym_code, name=sym_name))
            seen_symptoms.add(sym_code)

        # Upsert the BusinessSymptom link (composite PK handles duplicates)
        db.merge(
            BusinessSymptom(
                business_id  = biz_id,
                symptom_code = sym_code,
                diagnostic   = diag
            )
        )

    # Commit all changes in one transaction
    db.commit()

    # Return status and number of processed lines for transparency
    return {"status": "import complete", "rows_processed": row_count}