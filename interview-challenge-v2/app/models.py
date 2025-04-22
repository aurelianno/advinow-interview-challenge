from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

# Base class for our ORM models
Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"

    # IDs come from the CSV, so we disable autoincrement
    id   = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(100), nullable=False)

    # One business can have many symptom links
    symptoms = relationship("BusinessSymptom", back_populates="business")


class Symptom(Base):
    __tablename__ = "symptoms"

    # Use the CSV’s code (e.g. "SYMPT0001") as the primary key
    code = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)

    # One symptom can be linked to many businesses
    businesses = relationship("BusinessSymptom", back_populates="symptom")


class BusinessSymptom(Base):
    __tablename__ = "business_symptoms"

    # Composite PK on business_id + symptom_code ensures uniqueness
    business_id  = Column(Integer, ForeignKey("businesses.id"), primary_key=True)
    symptom_code = Column(String(20), ForeignKey("symptoms.code"), primary_key=True)
    diagnostic   = Column(Boolean, nullable=False)  # true/false from CSV

    # Timestamps auto‑set to track creation and updates
    created_at   = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime,
                          default=datetime.datetime.utcnow,
                          onupdate=datetime.datetime.utcnow,
                          nullable=False)

    # Relationships back to the parent tables
    business = relationship("Business", back_populates="symptoms")
    symptom  = relationship("Symptom", back_populates="businesses")