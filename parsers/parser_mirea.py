from bs4 import BeautifulSoup
import requests
from datetime import datetime
import logging
from db_func import connect_get_cursor, create_news_table, get_last_link, insert_news, print_all_rows, \
    create_categories_table, create_university_tables, get_category_id, get_university_id

logging.basicConfig(
    filename='monitor.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    encoding='utf-8'
)


def log_message(message, level=logging.INFO):
    """Выводим сообщение и в консоль, и в общий файл логов."""
    print(message)
    logging.log(level, message)


def normalise_category(input_cat):
    if not input_cat:
        return "Без категории"

    key = input_cat.strip().lower()

    mapping = {
        # --- Наука и инновации ---
        "пиш": "Наука и инновации",  # передовые инженерные школы
        "иии": "Наука и инновации",  # институт ИИ
        "идеи будущего": "Наука и инновации",
        "химбиотех": "Наука и инновации",

        # --- Образование ---
        "математический праздник": "Образование",
        "яндекс лицей": "Образование",
        "мпош": "Образование",  # московская предпроф. олимпиада школьников
        "мош": "Образование",  # московская олимпиада школьников
        "омо": "Образование",  # организационно-методический отдел
        "оммо": "Образование",  # объединённая межвузовская мат. олимпиада
        "охо": "Образование",
        "всош": "Образование",  # всерос олимпиада школьников
        "вош": "Образование",  # всерос олимпиада
        "математическая вертикаль": "Образование",
        "предпрофессиональная": "Образование",
        "профориентация": "Образование",
        "многопрофильная инженерная олимпиада «звезда»": "Образование",
        "многопрофильная олимпиада рту мирэа": "Образование",
        "олимпиады": "Образование",
        "конкурсы": "Образование",
        "прикладной конкурс «золотая дюжина»": "Образование",
        "технокалейдоскоп": "Образование",
        "шаг в будущее": "Образование",
        "лига инженеров": "Образование",
        "нто": "Образование",  # нац. технологическая олимпиада

        # --- Студенческая жизнь ---
        "вектор успеха": "Студенческая жизнь",
        "математические бои": "Студенческая жизнь",
        "химические бои": "Студенческая жизнь",
        "химический праздник": "Студенческая жизнь",
        "ученик года": "Студенческая жизнь",
        "интеллектуальные игры": "Студенческая жизнь",
        "киберспорт": "Студенческая жизнь",
        "кибербиатлон": "Студенческая жизнь",
        "ит-вертикаль": "Студенческая жизнь",
        "достижения": "Студенческая жизнь",

        # --- Объявления и события ---
        "дод": "Объявления и события",  # день открытых дверей
        "дни открытых дверей": "Объявления и события",

        # --- Абитуриентам ---
        "приемная комиссия": "Абитуриентам",
        "приёмная кампания": "Абитуриентам",
        "абитуриентам": "Абитуриентам",
        "навигатор поступления": "Абитуриентам",
        "детский технопарк": "Абитуриентам",
        "фрязино": "Абитуриентам",

        # --- Сотрудничество и партнёрство ---
        "партнеры": "Сотрудничество и партнёрство",
        "сотрудничество со школами": "Сотрудничество и партнёрство",
    }

    return mapping.get(key, "Без категории")


def update_db(conn, cur, page, meta, last_link):
    try:
        response = requests.get(page, headers=meta, timeout=15)
    except requests.RequestException as error:
        log_message(f'Ошибка запроса страницы {page}: {error}', logging.ERROR)
        return False
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')

        cards = soup.select('.article-body')
        if not cards:
            log_message('Структура сайта изменилась. Карточка .article-body не найдена', logging.ERROR)
            return False

        for card in cards:
            category_block = card.select_one('ul')
            if category_block:
                categories = [cat.text.strip() for cat in category_block.select('a')]
                cat = normalise_category(categories[0]) if categories else 'Без категории'
            else:
                cat = 'Без категории'

            href_tag = card.find('a')
            href = "https://priem.mirea.ru/" + href_tag.get('href')
            if last_link != href:
                title = card.select_one('.article-header').text.strip()
                time_tag = card.select_one('time')
                if time_tag:
                    dt_iso = time_tag.get('datetime')
                    dt_with_tz = datetime.fromisoformat(dt_iso)
                    dt_naive = dt_with_tz.replace(tzinfo=None)
                else:
                    log_message('Структура сайта изменилась. Временная метка time не найдена', logging.ERROR)
                    return False

                descript = card.select_one('.article-introtext').text.strip()
                cat_id = get_category_id(cur, cat)
                uni_id = get_university_id(cur, 'МИРЭА')
                if href and title:
                    insert_news(cur, conn, title, href, dt_naive, cat_id, uni_id, descript)
                    log_message("Новость успешно добавлена")
                else:
                    log_message('Структура сайта изменилась. Ссылка или заголовок .article-header не найдены', logging.ERROR)
            else:
                log_message('Не добавленных в базу новостей нет')
                return 'Completed'

    else:
        log_message(f'Ошибка на странице: {page}, код {response.status_code}', logging.ERROR)
        return False


def parse(db):
    connection, cursor = connect_get_cursor(db)
    create_news_table(cursor, connection)
    create_categories_table(cursor, connection)
    create_university_tables(cursor, connection)
    last = get_last_link(cursor)
    log_message(f'Последняя новость в базе: {last}')


    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }

    try:
        first_resp = requests.get("https://priem.mirea.ru/news?start=0", timeout=15)
    except requests.RequestException as error:
        log_message(f'Ошибка запроса главной страницы МИРЭА: {error}', logging.ERROR)
        connection.close()
        return False
    if first_resp:
        try:
            soup = BeautifulSoup(first_resp.text, 'html.parser')
            counter = soup.select_one('.com-content-category-blog__counter.counter.float-md-end.pt-3.pe-2')
            if counter is None:
                raise ValueError('Не найден счётчик страниц новостей')
            counter_str = counter.text
            num_of_pages = int(counter_str.split()[-1])
        except (AttributeError, ValueError, IndexError) as error:
            log_message(f'Ошибка разбора главной страницы МИРЭА: {error}', logging.ERROR)
            connection.close()
            return False

        for i in range(0, num_of_pages - 1):
            url = f"https://priem.mirea.ru/news?start={i * 9}"
            status = update_db(connection, cursor, url, headers, last)
            if status == 'Completed':
                break
    else:
        log_message(f'Ошибка на главной странице: код {first_resp.status_code}, URL: https://priem.mirea.ru/news?start=0', logging.ERROR)
        return False

    connection.close()

if __name__ == '__main__':
    parse('../news.db')