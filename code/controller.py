import asyncio
import datetime

import aiohttp
from sqlalchemy.orm import Session

from parser import get_areas_dict, parse_ode_department, get_university_department, get_area_universities
from db_models import Zno, Coefficient, Knowledge_area, Speciality, Region, University, engine

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


session = Session(engine)


async def get_all_areas_to_db():
    areas = await get_areas_dict()
    connector = aiohttp.TCPConnector(limit=200, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    tasks = []
    if areas:
        for area, area_url in areas.items():
            region = session.query(Region).where(Region.name == area).first()
            if not region:
                region = Region(name=area,
                                region_coefficient=region_coefficient_dict[area])
                session.add(region)
                session.commit()

            # tasks.append(asyncio.ensure_future(add_all_universities(
            #     request,
            #     region,
            #     area_url)))
            await add_all_universities(
                request,
                region,
                area_url)
        # await asyncio.wait(tasks)
    await request.close()


async def add_all_universities(request, region, area_url):
    universities = await get_area_universities(request, area_url)
    # tasks = []
    for university, university_url in universities.items():
        await add_one_university(request=request, region=region, university=university, university_url=university_url)
    #     tasks.append(asyncio.ensure_future(add_one_university(request=request, region=region, university=university, university_url=university_url)))
    # await asyncio.wait(tasks)




async def add_one_university(request, region, university, university_url):
    university_object = session.query(
        University
    ).filter(
        University.name == university,
        University.region_id == region.id
    ).first()
    if not university_object:
        university_object = University(
            name=university,
            region_id=region.id
        )
        session.add(university_object)
        session.commit()
    await get_deps(request=request, university=university_object, university_url=university_url)





async def get_deps(request, university, university_url):
    deps_all = await get_university_department(request=request, university_url=university_url)
    tasks = []
    for dep in deps_all:
        if dep:
            departments_dict = await parse_ode_department(request=request, dep=dep)
            for key, value in departments_dict.items():
                knowledge_area = session.query(Knowledge_area).filter(Knowledge_area.university_id == university.id,
                                                                       Knowledge_area.name == value["knowledge_area"]).first()
                if not knowledge_area:
                    knowledge_area = Knowledge_area(
                        university_id=university.id,
                        name=value["knowledge_area"]
                    )
                    session.add(knowledge_area)
                    session.commit()
                # await get_all_specialities_to_db(knowledge_area=knowledge_area,
                #                                                               speciality_name=key,
                #                                                               speciality_values=value)
                tasks.append(asyncio.ensure_future(get_all_specialities_to_db(knowledge_area=knowledge_area,
                                                                              speciality_name=key,
                                                                              speciality_values=value)))
    if tasks:
        await asyncio.wait(tasks)
        print(f"{university.name} is done")


async def get_all_specialities_to_db(knowledge_area, speciality_name, speciality_values):
    speciality_index = speciality_name.split(" ")[0]
    speciality_coefficient = specialities_coefficient_dict.get(speciality_index)

    speciality_object = session.query(Speciality).filter_by(
        speciality_url=speciality_values["speciality_url"]
    ).first()
    if not speciality_coefficient:
        speciality_coefficient = 1
    if not speciality_object:
        speciality_object = Speciality(
            speciality_url=speciality_values["speciality_url"]
        )
        session.add(speciality_object)
        session.commit()
    speciality_object.program = speciality_values["program"]
    if speciality_values["old_budget"]:
        speciality_object.min_rate_budget = float(speciality_values["old_budget"])
    if speciality_values["old_contract"]:
        speciality_object.average_rate_contract = float(speciality_values["old_contract"])
    speciality_object.name = speciality_name
    speciality_object.area_id = knowledge_area.id
    speciality_object.faculty = speciality_values["department"]
    speciality_object.speciality_coefficient = speciality_coefficient
    for subject, coefficient in speciality_values["zno"].items():
        if "*" in subject:
            zno = session.query(Zno).filter(Zno.name == subject[:-1]).first()
            if not zno:
                zno = Zno(
                    name=subject[:-1]
                )
                session.add(zno)
                session.commit()
        else:
            zno = session.query(Zno).filter(Zno.name == subject).first()
            if not zno:
                zno = Zno(
                    name=subject
                )
                session.add(zno)
                session.commit()
        coefficient_object = session.query(
            Coefficient
        ).filter(
            Coefficient.speciality_id == speciality_object.id,
            Coefficient.zno_id == zno.id
        ).first()
        if not coefficient_object:
            coefficient_object = Coefficient(
                speciality_id=speciality_object.id,
                zno_id=zno.id
            )
            session.add(coefficient_object)
        coefficient_object.coefficient = float(coefficient)
        if '*' in subject:
            coefficient_object.required = False
        else:
            coefficient_object.required = True
    session.commit()
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


# async def get_all_knowledge_areas_to_db(university, departments_dict):
#     if departments_dict:
#         tasks = []
#         for knowledge_area, specialities_dict in departments_dict.items():
#             if specialities_dict:
#                 print(f"        {knowledge_area}")
#                 knowledge_area_object = session.query(Knowledge_area).filter(
#                     Knowledge_area.name == knowledge_area,
#                     Knowledge_area.university_id == university.id
#                 ).first()
#                 if not knowledge_area_object:
#                     knowledge_area_object = Knowledge_area(
#                         name=knowledge_area,
#                         university_id=university.id
#                     )
#                     session.add(knowledge_area_object)
#                     session.commit()
#                 tasks.append(get_all_specialities_to_db(knowledge_area_object, specialities_dict))
#         await asyncio.wait(tasks)


# async def get_university_department(request, university, university_url: str):
#     """
#     Method that parse every department for one university
#     """
#     url = university_url
#     while True:
#         try:
#             async with request.get(url, headers=headers) as response:
#                 if response:
#                     soup = BeautifulSoup(await response.text(), "lxml")
#                     year_urls = soup.find_all("span", class_="year")
#                     url_2021 = 0
#                     for i in year_urls:
#                         if "2021" in i.text:
#                             url_2021 = i
#                     async with request.get("https://vstup.osvita.ua" + url_2021.find("a").get("href"), headers=headers) as response:
#                         soup = BeautifulSoup(await response.text(), "lxml")
#                     deps_all = soup.find("div", class_="panel den")
#                     if deps_all:
#                         deps_all = deps_all.select('div[class*="row no-gutters table-of-specs-item-row qual1 base40"]')
#                     if deps_all:
#                         departments_dict = {}
#                         counter = 0
#                         for dep in deps_all:
#                             try:
#                                 department = dep.text.split("Факультет:")[1]
#                                 department = department.split('Освітня')[0].strip()
#                             except IndexError:
#                                 department = "-"
#                             knowledge_area = dep.text.split("Галузь:")[1].split('Спеціальність')[0].strip()
#                             print(knowledge_area)
#                             speciality = dep.find("a").text
#                             program = dep.text.split("Освітня програма:")[1].split("\n")[0].strip()
#                             speciality_url = "https://vstup.osvita.ua" + dep.find("a", class_="green-button").get("href")
#                             grades_names = dep.select('div[class*="sub"]')
#                             counter += 1
#                             grades_dict = {}
#                             for grade in range(0, len(grades_names), 2):
#                                 name = grades_names[grade].text.split("(")[0].strip()
#                                 coefficient = grades_names[grade].text.replace(" \n", "").replace(")", "").replace(", ",
#                                                                                                                    "").replace(
#                                     "балmin=", "k=").strip().split("k=")[1:3]
#                                 if len(coefficient) > 1:
#                                     grades_dict[name] = coefficient[1]
#                                 else:
#                                     grades_dict[name] = coefficient[0]
#                             if knowledge_area not in departments_dict.keys():
#                                 departments_dict[knowledge_area] = {}
#                             if speciality not in departments_dict[knowledge_area]:
#                                 departments_dict[knowledge_area].setdefault(f"speciality{counter}", {})
#                                 departments_dict[knowledge_area][f"speciality{counter}"][speciality] = {"zno": grades_dict}
#                             min_budget, avg_contract = await parse_one_speciality(request, speciality_url)
#                             departments_dict[knowledge_area][f"speciality{counter}"][speciality]["old_budget"] = min_budget
#                             departments_dict[knowledge_area][f"speciality{counter}"][speciality]["old_contract"] = avg_contract
#                             departments_dict[knowledge_area][f"speciality{counter}"][speciality][
#                                 "department"] = department
#                             departments_dict[knowledge_area][f"speciality{counter}"][speciality]["program"] = program
#                             departments_dict[knowledge_area][f"speciality{counter}"][speciality]["speciality_url"] = speciality_url
#                         return (university, departments_dict)
#                 break
#         except SocketError as e:
#             if e.errno != errno.ECONNRESET:
#                 raise e
#             pass
#     return None, None
