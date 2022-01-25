from db_models import *
from sqlalchemy.orm import Session
from time import time

session = Session(bind=engine)


class Controller():
    '''Another class for requests from bot to database'''

    def create_user(self, tg_id):

        user = session.query(Users).filter_by(tg_id=tg_id).first()

        if not user:

            user = Users(tg_id=tg_id)
            session.add(user)
            session.commit()

    def get_regions():
        # getting all regions
        regions = session.query(Region).all()

        return regions

    def get_universities(regiona):
        # returning universities by region id
        region = session.query(Region).filter_by(id=regiona).first()

        return [uni for uni in region.university if uni.knowledge_area]

    def get_areas():

        areas = session.query(Knowledge_area).distinct(Knowledge_area.name)

        return areas

    def get_specs(area):

        specs = session.query(Speciality, Knowledge_area).join(
            Speciality, Speciality.area_id == Knowledge_area.id).filter(
            Knowledge_area.name.startswith(area)).distinct(Speciality.name).all()

        return specs

    def ma_balls(tg_id):

        user = session.query(Users).filter_by(tg_id=tg_id).first()

        return user.grades

    def get_znos():

        znos = session.query(Zno).all()

        return znos