import asyncio
import datetime

import aiohttp
from sqlalchemy.orm import Session

from parser import main, get_areas_dict
from db_models import Zno, Coefficient, Knowledge_area, Speciality, Region, University, engine

session = Session(bind=engine)

region_coefficient_dict = {'м. Київ': 1.00,
                           'Донецька область': 1.04,
                           'Луганська область': 1.04,
                           'Кіровоградська область': 1.04,
                           'Миколаївська область': 1.04,
                           'Рівненська область': 1.04,
                           'Сумська область': 1.04,
                           'Херсонська область': 1.04,
                           'Житомирська область': 1.04,
                           'Черкаська область': 1.04,
                           'Чернігівська область': 1.04,
                           'Івано-Франківська область': 1.02,
                           'Вінницька область': 1.02,
                           'Волинська область': 1.02,
                           'Дніпропетровська область': 1.02,
                           'Закарпатська область': 1.02,
                           'Запорізька область': 1.02,
                           'Київська область': 1.00,
                           'Львівська область': 1.02,
                           'Одеська область': 1.02,
                           'Полтавська область': 1.02,
                           'Тернопільська область': 1.02,
                           'Харківська область': 1.02,
                           'Хмельницька область': 1.02,
                           'Чернівецька область': 1.02
                           }

specialities_coefficient_dict = {
    "012": 1.02,
    "013": 1.02,
    "014": 1.02,
    "015": 1.02,
    "091": 1.02,
    "101": 1.02,
    "102": 1.02,
    "103": 1.02,
    "104": 1.02,
    "105": 1.02,
    "106": 1.02,
    "111": 1.02,
    "112": 1.02,
    "124": 1.02,
    "131": 1.02,
    "132": 1.02,
    "133": 1.02,
    "134": 1.02,
    "135": 1.02,
    "136": 1.02,
    "141": 1.02,
    "142": 1.02,
    "143": 1.02,
    "144": 1.02,
    "145": 1.02,
    "151": 1.02,
    "152": 1.02,
    "153": 1.02,
    "161": 1.02,
    "171": 1.02,
    "172": 1.02,
    "173": 1.02,
    "181": 1.02,
    "182": 1.02,
    "183": 1.02,
    "184": 1.02,
    "185": 1.02,
    "186": 1.02,
    "187": 1.02,
    "192": 1.02,
    "193": 1.02,
    "194": 1.02,
    "201": 1.02,
    "202": 1.02,
    "203": 1.02,
    "204": 1.02,
    "205": 1.02,
    "206": 1.02,
    "207": 1.02,
    "208": 1.02,
    "251": 1.02,
    "252": 1.02,
    "253": 1.02,
    "254": 1.02,
    "255": 1.02,
    "261": 1.02,
    "263": 1.02,
    "271": 1.02,
    "272": 1.02,
    "273": 1.02,
    "274": 1.02,
    "275": 1.02
}


async def get_all_areas_to_db():
    tasks = []
    request_list = []
    areas = await get_areas_dict()
    connector = aiohttp.TCPConnector(limit=10, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    if areas:
        for area, area_url in areas.items():
            region = session.query(Region).filter(Region.name == area).first()
            if not region:
                result_list = await main(area=area, area_url=area_url, request=request)
                for area, universities_dict in result_list.items():
                    print(area)
                    region = Region(name=area,
                                    region_coefficient=region_coefficient_dict[area])
                    session.add(region)
                    session.commit()
                    await get_all_universities_to_db(region, universities_dict)
        await request.close()
        session.commit()


async def get_all_universities_to_db(region, universities_dict):
    tasks = []
    for university, departments_dict in universities_dict.items():
        print(f"    {university}")
        university_object = University(
            name=university,
            region_id=region.id
        )
        session.add(university_object)
        session.commit()
        tasks.append(asyncio.ensure_future(get_all_knowledge_areas_to_db(university_object, departments_dict)))
    await asyncio.wait(tasks)


async def get_all_knowledge_areas_to_db(university, departments_dict):
    if departments_dict:
        tasks = []
        for knowledge_area, specialities_dict in departments_dict.items():
            if specialities_dict:
                print(f"        {knowledge_area}")
                knowledge_area_object = session.query(Knowledge_area).filter(
                    Knowledge_area.name == knowledge_area).first()
                if not knowledge_area_object:
                    knowledge_area_object = Knowledge_area(
                        name=knowledge_area,
                        university_id=university.id
                    )
                session.add(knowledge_area_object)
                session.commit()
                tasks.append(get_all_specialities_to_db(knowledge_area_object, specialities_dict))
        await asyncio.wait(tasks)


async def get_all_specialities_to_db(knowledge_area, specialities_dict):
    for speciality_id, speciality_dict in specialities_dict.items():
        if speciality_id:
            for speciality_name, speciality_values in speciality_dict.items():
                print(f"            {speciality_name}")
                speciality_index = speciality_name.split(" ")[0]
                speciality_coefficient = specialities_coefficient_dict.get(speciality_index)
                if not speciality_coefficient:
                    speciality_coefficient = 1
                speciality_object = Speciality(
                    name=speciality_name,
                    program=speciality_values["program"],
                    min_rate_budget=speciality_values["old_budget"],
                    average_rate_contract=speciality_values["old_contract"],
                    area_id=knowledge_area.id,
                    faculty=speciality_values["department"],
                    speciality_coefficient=speciality_coefficient
                )
                session.add(speciality_object)

                for subject, coefficient in speciality_values["zno"].items():
                    if "*" in subject:
                        zno = session.query(Zno).filter(Zno.name == subject[:-1]).first()
                        if not zno:
                            zno = Zno(
                                name=subject[:-1]
                            )
                    else:
                        zno = session.query(Zno).filter(Zno.name == subject).first()
                        if not zno:
                            zno = Zno(
                                name=subject
                            )

                    coefficient_object = Coefficient(
                        speciality_id=speciality_object.id,
                        zno_id=zno.id,
                        coefficient=float(coefficient),
                        required=True
                    )
                    if '*' in subject:
                        coefficient_object.required = False
                    session.add(zno)
                    session.add(coefficient_object)
    session.commit()


if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(get_all_areas_to_db())
    print(datetime.datetime.now() - start)