import asyncio
import datetime
import os

import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from parser import get_areas_dict, parse_ode_department, get_university_department, get_area_universities
from db_models import Zno, Coefficient, Knowledge_area, Speciality, Region, University

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

async_engine = create_async_engine(os.environ.get('DATABASE_URL_ASYNC'), pool_size=10, pool_timeout=300)
async_session = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)
session = AsyncSession(async_engine)


async def get_area(area):
    async with async_session() as session:
        async with session.begin():
            region = await session.execute(select(Region).filter(Region.name == area))
            region = region.scalars().first()
            if not region:
                return None
            return region.id

async def create_area(area):
    async with async_session() as session:
        async with session.begin():
            region = Region(name=area,
                            region_coefficient=region_coefficient_dict[area])
            session.add(region)
            await session.commit()
            return region.id

async def get_all_areas_to_db():
    areas = await get_areas_dict()
    connector = aiohttp.TCPConnector(limit=200, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    tasks = []
    if areas:
        for area, area_url in areas.items():
            region_id = await get_area(area)
            if not region_id:
                region_id = await create_area(area)
            tasks.append(asyncio.ensure_future(add_all_universities(
                request,
                region_id,
                area_url)))
            # await add_all_universities(
            #     request,
            #     region_id,
            #     area_url)
        await asyncio.wait(tasks)
    await request.close()


async def add_all_universities(request, region_id, area_url):
    universities = await get_area_universities(request, area_url)
    tasks = []
    for university, university_url in universities.items():
        # await add_one_university(request=request, region_id=region_id, university=university, university_url=university_url)
        tasks.append(asyncio.ensure_future(add_one_university(request=request, region_id=region_id, university=university, university_url=university_url)))
    await asyncio.wait(tasks)


async def get_university(university, region_id):
    async with async_session() as session:
        async with session.begin():
            university_object = await session.execute(select(
                University
            ).filter(
                University.name == university,
                University.region_id == region_id
            ))
            university_object = university_object.scalars().first()
            if not university_object:
                return None
            return university_object.id


async def create_university(university, region_id):
    async with async_session() as session:
        async with session.begin():
            university_object = University(
                name=university,
                region_id=region_id
            )
            session.add_all(
                [
                    university_object
                ]
            )
            await session.commit()
            return university_object.id


async def add_one_university(request, region_id, university, university_url):
    university_id = await get_university(university, region_id)
    if not university_id:
        university_id = await create_university(university, region_id)
    print(university_id)
    await get_deps(request=request, university_id=university_id, university_url=university_url)


async def get_knowledge_area(university_id, value):
    async with async_session() as session:
        async with session.begin():
            knowledge_area = await session.execute(select(Knowledge_area).filter(Knowledge_area.university_id == university_id,
                                                                                 Knowledge_area.name == value[
                                                                                     "knowledge_area"]))
            knowledge_area = knowledge_area.scalars().first()
            if not knowledge_area:
                return None
            return knowledge_area.id


async def create_knowledge_area(university_id, value):
    async with async_session() as session:
        async with session.begin():
            knowledge_area = Knowledge_area(
                university_id=university_id,
                name=value["knowledge_area"]
            )
            session.add_all(
                [
                    knowledge_area
                ]
            )
            await session.commit()
            return knowledge_area.id


async def get_deps(request, university_id, university_url):
    deps_all = await get_university_department(request=request, university_url=university_url)
    tasks = []
    for dep in deps_all:
        if dep:
            departments_dict = await parse_ode_department(request=request, dep=dep)
            for key, value in departments_dict.items():
                knowledge_area_id = await get_knowledge_area(university_id, value)
                if not knowledge_area_id:
                    knowledge_area_id = await create_knowledge_area(university_id, value)
                print(knowledge_area_id)
                # await get_all_specialities_to_db(
                #     knowledge_area_id=knowledge_area_id,
                #     speciality_name=key,
                #     speciality_values=value)
                tasks.append(asyncio.ensure_future(get_all_specialities_to_db(
                                                                              knowledge_area_id=knowledge_area_id,
                                                                              speciality_name=key,
                                                                              speciality_values=value)))
            if tasks:
                await asyncio.wait(tasks)
                print(f"{university_id} is done")


async def get_speciality(speciality_values):
    async with async_session() as session:
        async with session.begin():
            speciality_object = await session.execute(select(Speciality).filter_by(
                speciality_url=speciality_values["speciality_url"]
            ))
            speciality_object = speciality_object.scalars().first()
            if not speciality_object:
                return None, speciality_object
            return speciality_object.id, speciality_object


async def create_speciality(speciality_values):
    async with async_session() as session:
        async with session.begin():
            speciality_object = Speciality(
                speciality_url=speciality_values["speciality_url"]
            )
            session.add_all(
                [
                    speciality_object
                ]
            )
            await session.commit()
            return speciality_object.id, speciality_object


async def edit_speciality(speciality_name, speciality_object, speciality_values, knowledge_area_id):
    async with async_session() as session:
        async with session.begin():
            speciality_index = speciality_name.split(" ")[0]
            speciality_coefficient = specialities_coefficient_dict.get(speciality_index)
            if not speciality_coefficient:
                speciality_coefficient = 1
            speciality_object.program = speciality_values["program"]
            if speciality_values["old_budget"]:
                speciality_object.min_rate_budget = float(speciality_values["old_budget"])
            if speciality_values["old_contract"]:
                speciality_object.average_rate_contract = float(speciality_values["old_contract"])
            speciality_object.name = speciality_name
            speciality_object.area_id = knowledge_area_id
            speciality_object.faculty = speciality_values["department"]
            speciality_object.speciality_coefficient = speciality_coefficient
            await session.commit()


async def get_zno(subject):
    async with async_session() as session:
        async with session.begin():
            zno = await session.execute(select(Zno).filter(Zno.name == subject))
            zno = zno.scalars().first()
            if not zno:
                return None
            return zno.id


async def create_zno(subject):
    async with async_session() as session:
        async with session.begin():
            zno = Zno(
                name=subject
            )
            session.add_all(
                [
                    zno
                ]
            )
            await session.commit()
            return zno.id


async def get_coefficient(speciality_id, zno_id):
    async with async_session() as session:
        async with session.begin():
            coefficient_object = await session.execute(select(
                Coefficient
            ).filter(
                Coefficient.speciality_id == speciality_id,
                Coefficient.zno_id == zno_id
            ))
            coefficient_object = coefficient_object.scalars().first()
            return coefficient_object


async def create_coefficient(speciality_id, zno_id):
    async with async_session() as session:
        async with session.begin():
            coefficient_object = Coefficient(
                speciality_id=speciality_id,
                zno_id=zno_id
            )
            session.add_all(
                [
                    coefficient_object
                ]
            )
            return coefficient_object

async def edit_coefficient(coefficient_object, coefficient, required):
    async with async_session() as session:
        async with session.begin():
            coefficient_object.coefficient = float(coefficient)
            coefficient_object.required = required
            await session.commit()


async def get_all_specialities_to_db(knowledge_area_id, speciality_name, speciality_values):
    speciality_id, speciality_object = await get_speciality(speciality_values)
    if not speciality_id:
        speciality_id, speciality_object = await create_speciality(speciality_values)
    print(speciality_id)
    await edit_speciality(speciality_name, speciality_object, speciality_values, knowledge_area_id)
    for subject, coefficient in speciality_values["zno"].items():
        if "*" in subject:
            zno_id = await get_zno(subject[:-1])
            if not zno_id:
                zno_id = await create_zno(subject[:-1])
        else:
            zno_id = await get_zno(subject)
            if not zno_id:
                zno_id = await create_zno(subject)
        coefficient_object = await get_coefficient(speciality_id, zno_id)
        if not coefficient_object:
            coefficient_object = await create_coefficient(speciality_id, zno_id)
        if "*" in subject:
            await edit_coefficient(coefficient_object, coefficient, False)
        else:
            await edit_coefficient(coefficient_object, coefficient, True)
    print(f"            {speciality_name} is done")

if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(get_all_areas_to_db())
    print(datetime.datetime.now() - start)
    #
    # connector = aiohttp.TCPConnector(limit=10, force_close=True)
    # request = aiohttp.ClientSession(connector=connector)
    # region = session.query(Region).filter(Region.name == "м. Київ").first()
    # print(asyncio.run(add_all_universities(request=request, region=region, area_url="https://vstup.osvita.ua/r10/")))

    # a = session.query(Speciality).filter(Speciality.average_rate_contract.is_not(None)).all()
    # print(a)

"""
{'134 Авіаційна та ракетно-космічна техніка':
 {'zno':
  {'Українська мова': '0.30',
   'Математика': '0.35',
    'Іноземна мова*': '0.25',
     'Історія України*': '0.25',
      'Біологія*': '0.25',
       'Географія*': '0.25',
        'Фізика*': '0.25',
         'Хімія*': '0.25',
          'Середній бал документа про освіту': '0.10'
    },
     'old_budget': '131.84',
     'old_contract': '130.36',
     'department': 'Аерокосмічний факультет',
     'program': 'Літаки і вертольоти; Обладнання повітряних суден',
     'speciality_url': 'https://vstup.osvita.ua/y2021/r27/183/854598/',
     'knowledge_area': 'Механічна інженерія'}}

"""