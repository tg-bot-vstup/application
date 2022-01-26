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
        if not user.grades:
            return ['У вас немає оцiнок']
        return [str(grade) for grade in user.grades]

    def get_znos():

        znos = session.query(Zno).all()

        return znos

    def set_grade(tg_id, zno, grade: int):
        # setting grade for particular user

        user = session.query(Users).filter_by(tg_id=tg_id).first()
        user_grade = session.query(Grades).filter(
            Grades.zno_id == zno, Grades.user_id == user.id).first()

        if not user_grade:
            if grade == 0:
                return 'У вас немає оцiнки з цього предмету'
            else:
                user_grade = Grades(
                    user_id=user.id, grade=grade, zno_id=zno)
                session.add(user_grade)
                session.commit()
                return 'Оцiнка додана'
        else:
            if grade == 0:
                session.delete(user_grade)
                session.commit()
                return 'Оцiнка видалена'
            else:
                print(grade)
                user_grade.grade = grade
                session.commit()
                return 'Оцiнка оновлена'

    def get_chances(tg_id, region, spec):

        user = session.query(Users).filter_by(
            tg_id=tg_id).first()
        print(spec)
        user_grades = user.grades
        '''Getting coefs for speciality in every univercity at the region'''
        coefficients = session.query(
            University, Region, Knowledge_area, Speciality).filter(
            University.region_id == Region.id,
            Region.id == region,
            Knowledge_area.university_id == University.id,
            Knowledge_area.id == Speciality.area_id,
            Speciality.name.startswith(spec)).distinct(University.name)
        print(coefficients)

        return [str(x.University) for x in coefficients]

    def checking(grades,speciality_data):

        coefficients = speciality_data.coefficients
        for coef in coefficients:
            print(coef.required)
'''
areas = session.query(University, Region, Knowledge_area, Speciality).join(
    University,
    University.region_id == Region.id).filter(
    Region.id == 1,
    Knowledge_area.university_id == University.id,
    Knowledge_area.id == Speciality.area_id,
    Speciality.name == "121 Інженерія програмного забезпечення").all()

for i in areas:
    print(i)
#    Controller.checking(2,i)
'''