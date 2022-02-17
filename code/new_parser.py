import asyncio
import datetime
import errno
import os
import socket
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

import aiohttp
from bs4 import BeautifulSoup
from db_models import (Coefficient, Knowledge_area, Region, Speciality,
                       University, Zno)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

region_coefficient_dict = {
    "м. Київ": 1.00,
    "Донецька область": 1.04,
    "Луганська область": 1.04,
    "Кіровоградська область": 1.04,
    "Миколаївська область": 1.04,
    "Рівненська область": 1.04,
    "Сумська область": 1.04,
    "Херсонська область": 1.04,
    "Житомирська область": 1.04,
    "Черкаська область": 1.04,
    "Чернігівська область": 1.04,
    "Івано-Франківська область": 1.02,
    "Вінницька область": 1.02,
    "Волинська область": 1.02,
    "Дніпропетровська область": 1.02,
    "Закарпатська область": 1.02,
    "Запорізька область": 1.02,
    "Київська область": 1.00,
    "Львівська область": 1.02,
    "Одеська область": 1.02,
    "Полтавська область": 1.02,
    "Тернопільська область": 1.02,
    "Харківська область": 1.02,
    "Хмельницька область": 1.02,
    "Чернівецька область": 1.02,
}

result = {'011 Освітні, педагогічні науки': 'Освіта/Педагогіка',
 '012 Дошкільна освіта': 'Освіта/Педагогіка',
 '013 Початкова освіта': 'Освіта/Педагогіка',
 '014 Середня освіта': 'Освіта/Педагогіка',
 '015 Професійна освіта': 'Освіта/Педагогіка',
 '016 Спеціальна освіта': 'Освіта/Педагогіка',
 '017 Фізична культура і спорт': 'Освіта/Педагогіка',
 '021 Аудіовізуальне мистецтво та виробництво': 'Культура і мистецтво',
 '022 Дизайн': 'Культура і мистецтво',
 '023 Образотворче мистецтво, декоративне мистецтво, реставрація': 'Культура і '
                                                                   'мистецтво',
 '024 Хореографія': 'Культура і мистецтво',
 '025 Музичне мистецтво': 'Культура і мистецтво',
 '026 Сценічне мистецтво': 'Культура і мистецтво',
 '027 Музеєзнавство, пам’яткознавство': 'Культура і мистецтво',
 '028 Менеджмент соціокультурної діяльності': 'Культура і мистецтво',
 '029 Інформаційна, бібліотечна та архівна справа': 'Культура і мистецтво',
 '031 Релігієзнавство': 'Гуманітарні науки',
 '032 Історія та археологія': 'Гуманітарні науки',
 '033 Філософія': 'Гуманітарні науки',
 '034 Культурологія': 'Гуманітарні науки',
 '035 Філологія': 'Гуманітарні науки',
 '041 Богослов’я': 'Богослов’я',
 '051 Економіка': 'Соціальні та поведінкові науки',
 '052 Політологія': 'Соціальні та поведінкові науки',
 '053 Психологія': 'Соціальні та поведінкові науки',
 '054 Соціологія': 'Соціальні та поведінкові науки',
 '061 Журналістика': 'Журналістика',
 '071 Облік і оподаткування': 'Управління та адміністрування',
 '072 Фінанси, банківська справа та страхування': 'Управління та '
                                                  'адміністрування',
 '073 Менеджмент': 'Управління та адміністрування',
 '075 Маркетинг': 'Управління та адміністрування',
 '076 Підприємництво, торгівля та біржова діяльність': 'Управління та '
                                                       'адміністрування',
 '081 Право': 'Право',
 '091 Біологія': 'Біологія',
 '101 Екологія': 'Природничі науки',
 '102 Хімія': 'Природничі науки',
 '103 Науки про Землю': 'Природничі науки',
 '104 Фізика та астрономія': 'Природничі науки',
 '105 Прикладна фізика та наноматеріали': 'Природничі науки',
 '106 Географія': 'Природничі науки',
 '111 Математика': 'Математика та статистика',
 '112 Статистика': 'Математика та статистика',
 '113 Прикладна математика': 'Математика та статистика',
 '121 Інженерія програмного забезпечення': 'Інформаційні технології',
 "122 Комп'ютерні науки": 'Інформаційні технології',
 '123 Комп’ютерна інженерія': 'Інформаційні технології',
 '124 Системний аналіз': 'Інформаційні технології',
 '125 Кібербезпека': 'Інформаційні технології',
 '126 Інформаційні системи та технології': 'Інформаційні технології',
 '131 Прикладна механіка': 'Механічна інженерія',
 '132 Матеріалознавство': 'Механічна інженерія',
 '133 Галузеве машинобудування': 'Механічна інженерія',
 '134 Авіаційна та ракетно-космічна техніка': 'Механічна інженерія',
 '135 Суднобудування': 'Механічна інженерія',
 '136 Металургія': 'Механічна інженерія',
 '141 Електроенергетика, електротехніка та електромеханіка': 'Електрична '
                                                             'інженерія',
 '142 Енергетичне машинобудування': 'Електрична інженерія',
 '143 Атомна енергетика': 'Електрична інженерія',
 '144 Теплоенергетика': 'Електрична інженерія',
 '145 Гідроенергетика': 'Електрична інженерія',
 '151 Автоматизація та комп’ютерно-інтегровані технології': 'Автоматизація та '
                                                            'приладобудування',
 '152 Метрологія та інформаційно-вимірювальна техніка': 'Автоматизація та '
                                                        'приладобудування',
 '153 Мікро- та наносистемна техніка': 'Автоматизація та приладобудування',
 '161 Хімічні технології та інженерія': 'Хімічна та біоінженерія',
 '162 Біотехнології та біоінженерія': 'Хімічна та біоінженерія',
 '163 Біомедична інженерія': 'Хімічна та біоінженерія',
 '171 Електроніка': 'Електроніка та телекомунікації',
 '172 Телекомунікації та радіотехніка': 'Електроніка та телекомунікації',
 '173 Авіоніка': 'Електроніка та телекомунікації',
 '181 Харчові технології': 'Виробництво та технології',
 '182 Технології легкої промисловості': 'Виробництво та технології',
 '183 Технології захисту навколишнього середовища': 'Виробництво та технології',
 '184 Гірництво': 'Виробництво та технології',
 '185 Нафтогазова інженерія та технології': 'Виробництво та технології',
 '186 Видавництво та поліграфія': 'Виробництво та технології',
 '187 Деревообробні та меблеві технології': 'Виробництво та технології',
 '191 Архітектура та містобудування': 'Архітектура та будівництво',
 '192 Будівництво та цивільна інженерія': 'Архітектура та будівництво',
 '193 Геодезія та землеустрій': 'Архітектура та будівництво',
 '194 Гідротехнічне будівництво, водна інженерія та водні технології': 'Архітектура '
                                                                       'та '
                                                                       'будівництво',
 '201 Агрономія': 'Аграрні науки та продовольство',
 '202 Захист і карантин рослин': 'Аграрні науки та продовольство',
 '203 Садівництво та виноградарство': 'Аграрні науки та продовольство',
 '204 Технологія виробництва і переробки продукції тваринництва': 'Аграрні '
                                                                  'науки та '
                                                                  'продовольство',
 '205 Лісове господарство': 'Аграрні науки та продовольство',
 '206 Садово-паркове господарство': 'Аграрні науки та продовольство',
 '207 Водні біоресурси та аквакультура': 'Аграрні науки та продовольство',
 '208 Агроінженерія': 'Аграрні науки та продовольство',
 '223 Медсестринство': 'Охорона здоров’я',
 '224 Технології медичної діагностики та лікування': 'Охорона здоров’я',
 '226 Фармація, промислова фармація': 'Охорона здоров’я',
 '227 Фізична терапія, ерготерапія': 'Охорона здоров’я',
 '229 Громадське здоров`я': 'Охорона здоров’я',
 '231 Соціальна робота': 'Соціальна робота',
 '232 Соціальне забезпечення': 'Соціальна робота',
 '241 Готельно-ресторанна справа': 'Сфера обслуговування',
 '242 Туризм': 'Сфера обслуговування',
 '251 Державна безпека': 'Воєнні науки, національна безпека, безпека '
                         'державного кордону',
 '256 Національна безпека': 'Воєнні науки, національна безпека, безпека '
                            'державного кордону',
 '261 Пожежна безпека': 'Цивільна безпека',
 '262 Правоохоронна діяльність': 'Цивільна безпека',
 '263 Цивільна безпека': 'Цивільна безпека',
 '271 Річковий та морський транспорт': 'Транспорт',
 '272 Авіаційний транспорт': 'Транспорт',
 '273 Залізничний транспорт': 'Транспорт',
 '274 Автомобільний транспорт': 'Транспорт',
 '275 Транспортні технології': 'Транспорт',
 '281 Публічне управління та адміністрування': 'Публічне управління та '
                                               'адміністрування',
 '291 Міжнародні відносини, суспільні комунікації та регіональні студії': 'Міжнародні '
                                                                          'відносини',
 '292 Міжнародні економічні відносини': 'Міжнародні відносини',
 '293 Міжнародне право': 'Міжнародні відносини'}

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
    "275": 1.02,
}

db_link = "postgresql+asyncpg:" + os.environ.get("DATABASE_URL")
async_engine = create_async_engine(db_link, pool_size=30, pool_timeout=300)
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/97.0.4692.71 Safari/537.36"
}


async def get_region(region_name: str):
    """
    function used to get region id from db or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            region = await session.execute(
                select(Region.id).filter(Region.name == region_name)
            )
            if not region:
                return None
            region = region.scalars().first()
            return region


async def create_region(region_name: str):
    """
    function used to create region object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            region = Region(
                name=region_name,
                region_coefficient=region_coefficient_dict[region_name],
            )
            session.add(region)
            await session.commit()
            print(region.id)
            return region.id


async def start_parsing():
    """
    function for parsing all regions and region urls from vstup.osvita.ua
    and add region if it does not exist
    """
    url = "https://abit-poisk.org.ua/rate2021"
    connector = aiohttp.TCPConnector(limit=50, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    async with request.get(url, headers=headers) as response:
        soup = BeautifulSoup(await response.text(), "lxml")

        select_list_regions = soup.find(
            "table",
            class_="table table-bordered"
        )
        if select_list_regions:
            select_list_regions = select_list_regions.find_all(
                "a"
            )
        if select_list_regions:
            # tasks = []
            for option in select_list_regions:
                option_text = option.text
                print(option_text)
                option_value = option.get("href")
                if option_value:
                    region_id = await get_region(option_text)
                    if not region_id:
                        region_id = await create_region(option_text)
                    region_url = url.replace('/rate2021', '') + option_value
                    print(region_url)
                    # tasks.append(
                    #     asyncio.ensure_future(
                    #         get_region_universities(
                    #             request=request,
                    #             region_url=region_url,
                    #             region_id=region_id
                    #         )
                    #     )
                    # )
                    await get_region_universities(
                        request=request,
                        region_url=region_url,
                        region_id=region_id
                    )
            # await asyncio.wait(tasks)
    await request.close()


async def get_university(university: str, region_id: int):
    """
    function used to get university id from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            university_id = await session.execute(
                select(University.id).filter(
                    University.name == university,
                    University.region_id == region_id
                )
            )
            university_id = university_id.scalars().first()
            return university_id


async def create_university(university: str, region_id: int):
    """
    function used to create university object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            university_object = University(
                name=university,
                region_id=region_id
            )
            session.add_all([university_object])
            await session.commit()
            return university_object.id


async def get_region_universities(
    request: aiohttp.ClientSession, region_url: str, region_id: int
):
    """
    Method that get all universities and university urls for one region
    and add them to db if they are not in there already
    """
    if region_url:
        while True:
            soup = await get_soup(request, url=region_url, headers=headers)
            all_uni = soup.find(
                "table",
                class_="table table-bordered"
            )
            if all_uni:
                all_uni = all_uni.find_all("a")
                # tasks = []
                if all_uni:
                    for uni in all_uni:
                        uni_text = uni.text
                        print(uni_text)
                        university_id = await get_university(
                            uni_text, region_id=region_id
                        )
                        if not university_id:
                            university_id = await create_university(
                                university=uni_text, region_id=region_id
                            )
                        await get_university_department(
                            request=request,
                            university_name=uni_text,
                            university_id=university_id,
                        )
                    #     tasks.append(
                    #         asyncio.ensure_future(
                    #             get_university_department(
                    #                 request=request,
                    #                 university_url=university_url,
                    #                 university_id=university_id
                    #             )
                    #         )
                    #     )
                    # await asyncio.wait(tasks)
                    break


async def get_soup(request: aiohttp.ClientSession, url: str, headers: dict):
    while True:
        try:
            async with request.get(url, headers=headers) as response:
                return BeautifulSoup(await response.text(), "lxml")
        except socket.error as e:
            if e.errno != errno.ECONNRESET:
                raise e


async def get_knowledge_area(university_id: int, knowledge_area: str):
    """
    function used to get knowledge area id from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            knowledge_area = await session.execute(
                select(Knowledge_area.id).filter(
                    Knowledge_area.university_id == university_id,
                    Knowledge_area.name == knowledge_area,
                )
            )
            knowledge_area = knowledge_area.scalars().first()
            return knowledge_area


async def create_knowledge_area(university_id, knowledge_area):
    """
    function used to create knowledge area object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            knowledge_area = Knowledge_area(
                university_id=university_id, name=knowledge_area
            )
            session.add_all([knowledge_area])
            await session.commit()
            return knowledge_area.id


async def get_university_department(
    request: aiohttp.ClientSession, university_name: str, university_id: int
):
    """
    Method that parse every speciality for one university
    and add knowledge areas if they are not exists
    """
    print(university_name)
    url = f"https://vstup2021.edbo.gov.ua/offers/"
    options = Options()
    options.add_argument("--headless")
    driver = GeckoDriverManager().install()
    browser = webdriver.Firefox(service=Service(driver), options=options)
    browser.get(url)
    find_field = browser.find_element_by_id("offers-search-ft-q")
    find_field.send_keys("бакалавр " + university_name + " денна")
    await asyncio.sleep(2)
    find_field.send_keys(Keys.ENTER)
    await asyncio.sleep(2)
    universities = browser.find_elements_by_class_name("university-title")
    for uni in universities:
        await asyncio.sleep(2)
        uni.click()
    soup = BeautifulSoup(browser.page_source, "lxml")
    browser.close()
    soup = soup.find("div", {"id": "universities"})
    deps_all = soup.select('div[class*="university-offers-qbe"]')
    departments = []
    for dep in deps_all:
        if "Бакалавр" in dep.text:
            if "(основа вступу - Повна загальна середня освіта)" in dep.text:
                departments.append(dep)
    if departments:
        tasks = []
        for dep in departments:
            specialities = dep.find_all("div", class_="offer")
            for spec in specialities:
                # await parse_ode_speciality(
                #     request,
                #     spec,
                #     university_id
                # )
                tasks.append(
                    asyncio.ensure_future(
                        parse_ode_speciality(
                            request,
                            spec,
                            university_id
                        )
                    )
                )
        await asyncio.wait(tasks)


async def get_speciality(speciality_name: str, knowledge_area_id):
    """
    function used to get speciality object from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            speciality_object = await session.execute(
                select(Speciality).filter_by(
                    name=speciality_name,
                    area_id=knowledge_area_id
                )
            )
            speciality_object = speciality_object.scalars().first()
            if speciality_object:
                session.expunge(speciality_object)
            return speciality_object


async def create_speciality(speciality_name: str, knowledge_area_id: int):
    """
    function used to create speciality object,
    add it to db and get it
    """
    async with async_session() as session:
        async with session.begin():
            speciality_object = Speciality(name=speciality_name,
                                           area_id=knowledge_area_id)
            session.add_all([speciality_object])
            await session.commit()
            session.expunge(speciality_object)
            return speciality_object


async def edit_speciality(
    speciality_name: str,
    speciality_object: Speciality,
    min_budget: str,
    avg_contract: str,
    department: str,
    program: str,
    knowledge_area_id: int,
):
    """
    function used to edit speciality object,
    add commit changes
    """
    async with async_session() as session:
        async with session.begin():
            print(speciality_name)
            session.add(speciality_object)
            speciality_index = speciality_name.split(" ")[0]
            speciality_coefficient = specialities_coefficient_dict.get(
                speciality_index
            )
            if not speciality_coefficient:
                speciality_coefficient = 1
            speciality_object.program = program
            if min_budget:
                speciality_object.min_rate_budget = float(min_budget)
            if avg_contract:
                speciality_object.average_rate_contract = float(avg_contract)
            speciality_object.name = speciality_name
            speciality_object.area_id = knowledge_area_id
            speciality_object.faculty = department
            speciality_object.speciality_coefficient = speciality_coefficient
            await session.commit()


async def get_zno(subject: str):
    """
    function used to get zno id from db,
    or None if there are no such object
    """
    async with async_session() as session:
        async with session.begin():
            zno = await session.execute(
                select(
                    Zno.id
                ).filter(
                    Zno.name == subject
                )
            )
            zno = zno.scalars().first()
            return zno


async def create_zno(subject: str):
    """
    function used to create zno object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            zno = Zno(name=subject)
            session.add_all([zno])
            await session.commit()
            return zno.id


async def get_coefficient(speciality_id: int, zno_id: int):
    """
    function used to get coefficient object from db,
    or None if there are no such object
    """
    async with async_session() as session:
        async with session.begin():
            coefficient_object = await session.execute(
                select(Coefficient).filter(
                    Coefficient.speciality_id == speciality_id,
                    Coefficient.zno_id == zno_id,
                )
            )
            coefficient_object = coefficient_object.scalars().first()
            if coefficient_object:
                session.expunge(coefficient_object)
            return coefficient_object


async def create_coefficient(speciality_id: int, zno_id: str):
    """
    function used to create coefficient object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            coefficient_object = Coefficient(
                speciality_id=speciality_id,
                zno_id=zno_id
            )
            session.add_all([coefficient_object])

            session.expunge(coefficient_object)
            return coefficient_object


async def edit_coefficient(
    coefficient_object: Coefficient, coefficient: str, required: bool
):
    """
    function used to edit coefficient object,
    add commit changes to db
    """
    async with async_session() as session:
        async with session.begin():
            session.add(coefficient_object)
            coefficient_object.coefficient = float(coefficient)
            coefficient_object.required = required
            await session.commit()


async def parse_ode_speciality(
    request: aiohttp.ClientSession, dep: BeautifulSoup, university_id: int
):
    """
    function used to parse information about one speciality and add/modify it
    """
    speciality = dep.find("dl", class_="row offer-university-specialities-name")
    speciality_name = f'{speciality.find("span", class_="badge badge-primary").text} {speciality.find("span", class_="text-uppercase text-primary").text}'
    department = dep.find("dl", class_="row offer-university-facultet-name")
    department = f"{department.find('dd').text}"
    program = dep.find("dl", class_="row offer-study-programs")
    program = f"{program.find('dd').text}"
    knowledge_area = result[speciality_name]
    knowledge_area_id = await get_knowledge_area(university_id=university_id, knowledge_area=knowledge_area)
    if not knowledge_area_id:
        knowledge_area_id = await create_knowledge_area(university_id, knowledge_area)
    grades_names = dep.find('div', class_="offer-subjects")
    grades_names = grades_names.find_all("div", class_="offer-subject-wrapper")
    try:
        min_budget = dep.find("div", class_="col-md-4 col-sm-12 stats-field stats-field-obm").find("div", class_="value").text
    except:
        min_budget = None
    try:
        avg_contract = dep.find("div", class_="col-md-4 col-sm-12 stats-field stats-field-ocm").find("div", class_="value").text
    except:
        avg_contract = None
    speciality_object = await get_speciality(speciality_name, knowledge_area_id)
    if not speciality_object:
        speciality_object = await create_speciality(speciality_name, knowledge_area_id)
    await edit_speciality(
        speciality_name=speciality_name,
        speciality_object=speciality_object,
        min_budget=min_budget,
        avg_contract=avg_contract,
        department=department,
        program=program,
        knowledge_area_id=knowledge_area_id,
    )
    for grade in grades_names:
        subjects = grade.find_all("div", class_="subject-wrapper")
        for subject in subjects:
            coefficient = subject.find("div", class_="coefficient").text
            name = subject.select('div[class*="subject-name"]')
            name = name[0].text
            try:
                zno_id = await create_zno(name)
            except IntegrityError:
                zno_id = await get_zno(name)
            coefficient_object = await get_coefficient(
                speciality_object.id,
                zno_id
            )
            if not coefficient_object:
                coefficient_object = await create_coefficient(
                    speciality_object.id, zno_id
                )
            required = True
            if "3" == grade.find("div", class_="subject-number").text:
                required = False
            await edit_coefficient(
                coefficient_object,
                coefficient,
                required
            )


if __name__ == "__main__":
    start = datetime.datetime.now()
    asyncio.run(start_parsing())
    print(datetime.datetime.now() - start)
