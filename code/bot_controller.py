from db_models import *
from time import time
from utils import default_znos

Session = sessionmaker(bind=engine)


session = Session()


class Controller():
    '''Another class for requests from bot to database'''

    def create_user(tg_id):

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

        try:
            areas = session.query(Knowledge_area.name, Speciality.name).filter(
                Speciality.area_id == Knowledge_area.id,).distinct(
                Knowledge_area.name).all()
        except:
            session.rollback()
            Controller.get_areas()
        
        return [{'name': area[0], 'specs': area[1]} for area in areas]

    def get_specs(area):

        specs = session.query(Speciality, Knowledge_area).filter(
            Speciality.area_id == Knowledge_area.id,
            Knowledge_area.name.startswith(area)).distinct(
            Speciality.name).all()

        return specs

    def ma_balls(tg_id):

        user = session.query(Users).filter_by(tg_id=tg_id).first()
        return user.grades

    def get_znos():

        znos = session.query(Zno.id,Zno.name).filter(Zno.name.in_(default_znos)).all()

        return znos

    def get_zno_id(name):

        zno = session.query(Zno.id).filter(Zno.name==name).first()[0]

        return zno

    def set_grade(tg_id, zno, grade: int):
        # setting grade for particular user
        user_id = session.query(Users.id).filter(
            Users.tg_id == tg_id).first()[0]
        user_grade = session.query(Grades).filter(
            Grades.zno_id == zno,
            Grades.user_id == user_id).first()

        if not user_grade:
            if grade == 0:
                return 'У вас немає оцiнки з цього предмету'
            else:
                user_grade = Grades(
                    user_id=user_id, grade=grade, zno_id=zno)
                session.add(user_grade)
                session.commit()
                return 'Оцiнка додана'
        else:
            if grade == 0:
                session.delete(user_grade)
                session.commit()
                return 'Оцiнка видалена'
            else:
                user_grade.grade = grade
                session.commit()
                return 'Оцiнка оновлена'

    def get_chances(tg_id, region, spec):

        user = session.query(Users).filter_by(
            tg_id=tg_id).first()
        user_grades = user.grades
        '''Getting coefs for speciality in every univercity at the region'''
        specialities = session.query(
            University, Region, Knowledge_area, Speciality).filter(
            University.region_id == Region.id,
            Region.id == region,
            Knowledge_area.university_id == University.id,
            Knowledge_area.id == Speciality.area_id,
            Speciality.name.startswith(spec)).distinct(University.name)
        # lists for final generation response
        additionals = []
        required = []
        budg = []
        cont = []
        for spec in specialities:
            results = Controller.checking(user_grades, spec.Speciality)
            # Checking if user haven't some required zno
            # or any not additional
            if results[1]:
                if results[0] == 'additional':
                    [additionals.append(zno) for zno in results[1]
                     if zno not in additionals]
                else:
                    [required.append(zno)
                     for zno in results[1] if zno not in required]
            else:
                rate = results[0] * spec.Region.region_coefficient

                if spec.Speciality.min_rate_budget:
                    if rate >= spec.Speciality.min_rate_budget:
                        budg.append(str(spec.University.name))
                    elif spec.Speciality.min_rate_budget and not spec.Speciality.average_rate_contract:
                        if rate >= 110 and spec.University.name not in budg:
                            cont.append(str(spec.University.name))

                if spec.Speciality.average_rate_contract:
                    if rate >= spec.Speciality.average_rate_contract - 10 and spec.University.name not in budg:
                        cont.append(str(spec.University.name))

        # Define why user can't go to any university
        if not budg and not cont:
            # If user haven't required zno
            if required:
                return {'result': False,
                        'data': list(required)}
            # If user haven't any additional zno
            elif additionals:
                return{'result': 'additional',
                       'data': list(additionals)}
        # If user have all znos, but haven't enough score
        return {'result': True,
                'data': {'budget': budg, 'contract': cont}}

    def checking(grades, speciality_data):
        '''Checking having user all the required grades
            and any of additional, then calculate maximum
            additional and returning result'''

        coefficients = speciality_data.coefficients
        max_nr = 0
        znos = []
        invalid_znos = []
        for coef in coefficients:
            if coef.required:
                zno = [grade for grade in grades if grade.zno_id == coef.zno_id]
                if zno:
                    znos.append(zno[0].grade * coef.coefficient)
                    continue
                else:
                    invalid_znos.append(str(coef.zno))
            else:
                score = [grade for grade in grades if grade.zno_id == coef.zno_id]
                if score:
                    if score[0].grade >= max_nr:
                        max_nr = score[0].grade * coef.coefficient

        if invalid_znos:
            # Firstly checking if user haven't required znos
            return ('invalid', invalid_znos)
        if max_nr == 0:
            # Then check if user haven't any additional zno
            return('additional', [str(coef.zno) for coef in coefficients if not coef.required])
        znos.append(max_nr)
        zno_score = sum(znos) * speciality_data.speciality_coefficient
        # Finally, if user have both, returning result
        return (zno_score, invalid_znos)
