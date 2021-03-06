import os

from dotenv import load_dotenv
from sqlalchemy import (Boolean, Column, Float, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

load_dotenv()
db_link = "postgresql+psycopg2:" + os.environ.get("DATABASE_URL")
engine = create_engine(db_link, pool_pre_ping=True)

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True)


class Zno(Base):
    __tablename__ = "zno"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __repr__(self):
        return self.name


class Grades(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", backref="grades")
    zno_id = Column(Integer, ForeignKey("zno.id"))
    zno = relationship("Zno", backref="grades")
    grade = Column(Integer)

    def __repr__(self):
        return f"Ваш бал з {self.zno}: {self.grade}"


class Coefficient(Base):
    __tablename__ = "coefficient"

    id = Column(Integer, primary_key=True)
    speciality_id = Column(Integer, ForeignKey("speciality.id"))
    speciality = relationship("Speciality", backref="coefficients")
    zno_id = Column(Integer, ForeignKey("zno.id"))
    zno = relationship("Zno", backref="coefficients")
    coefficient = Column(Float)
    required = Column(Boolean)

    def __repr__(self):
        return f"ЗНО {self.zno} має коефiцiєнт {self.coefficient}"


class Knowledge_area(Base):
    __tablename__ = "knowledge_area"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    university = relationship("University", backref="knowledge_area")
    university_id = Column(Integer, ForeignKey("university.id"))

    def __repr__(self):
        return self.name


class Speciality(Base):
    __tablename__ = "speciality"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    program = Column(String(255))
    min_rate_budget = Column(Float)
    average_rate_contract = Column(Float)
    area_id = Column(Integer, ForeignKey("knowledge_area.id"))
    area = relationship("Knowledge_area", backref="specialities")
    faculty = Column(String(255))
    speciality_url = Column(String(255))
    speciality_coefficient = Column(Float)

    def __repr__(self):

        return self.name


class Region(Base):
    __tablename__ = "region"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    region_coefficient = Column(Float)

    def __repr__(self):

        return self.name


class University(Base):
    __tablename__ = "university"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    region_id = Column(Integer, ForeignKey("region.id"))
    region = relationship("Region", backref="university")

    def __repr__(self):
        return self.name


Base.metadata.create_all(engine)
