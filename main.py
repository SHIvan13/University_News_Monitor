import json
import time
import sqlite3
import logging

from parsers import parser_mirea, parser_rea, parser_kfu
import db_func

# Читаем настройки из config.json
try:
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)
except FileNotFoundError:
    print("Файл конфигурации не найден")


NEWS_DB = config["news_db"]
USERS_DB = config["users_db"]
OUTPUT_FILE = config["output_file"]
INTERVAL = config["interval_minutes"]


def prepare_databases():
    """Создаём таблицы, если их ещё нет."""
    conn, cursor = db_func.connect_get_cursor(NEWS_DB)
    if conn:
        db_func.create_news_table(cursor, conn)
        db_func.create_categories_table(cursor, conn)
        db_func.create_university_tables(cursor, conn)
        conn.close()

    conn, cursor = db_func.connect_get_cursor(USERS_DB)
    if conn:
        db_func.create_users_table(cursor, conn)
        db_func.create_user_cat_table(cursor, conn)
        conn.close()


def run_parsers():
    """Запускаем готовые парсеры."""
    parsers = [
        ("МИРЭА", parser_mirea.parse),
        ("КФУ", parser_kfu.parse),
        ("РЭУ", parser_rea.rea_parse),
    ]

    for name, function in parsers:
        try:
            print(f"Обработка сайта {name}")
            logging.info(f"Обработка сайта {name}")
            function(NEWS_DB)
        except Exception as error:
            print(f"Ошибка парсера {name}: {error}")
            logging.exception("Ошибка парсера %s", name)


def make_send_list(old_max_id):
    """Подбираем новые новости по интересам пользователей."""
    with sqlite3.connect(NEWS_DB) as conn:
        news = conn.execute(
            "SELECT id, category_id FROM news WHERE id > ? ORDER BY id",
            (old_max_id,)
        ).fetchall()

    with sqlite3.connect(USERS_DB) as conn:
        users = conn.execute("SELECT id FROM users ORDER BY id").fetchall()
        interests = conn.execute(
            "SELECT user_id, category_id FROM user_categories"
        ).fetchall()

    user_categories = {}
    for user_id, category_id in interests:
        user_categories.setdefault(user_id, set()).add(category_id)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        for (user_id,) in users:
            news_ids = [
                str(news_id)
                for news_id, category_id in news
                if category_id in user_categories.get(user_id, set())
            ]
            if news_ids:
                file.write(f"{user_id}: {', '.join(news_ids)}\n")

    print(f"Список рассылки сохранён в {OUTPUT_FILE}")
    print(f"Новых новостей: {len(news)}")
    logging.info(f"Список рассылки сохранён в {OUTPUT_FILE}")
    logging.info(f"Новых новостей: {len(news)}")


def main():
    logging.basicConfig(
        filename="monitor.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

    prepare_databases()

    while True:
        try:
            # Запоминаем ID новостей до запуска парсеров.
            with sqlite3.connect(NEWS_DB) as conn:
                old_max_id = conn.execute(
                    "SELECT COALESCE(MAX(id), 0) FROM news"
                ).fetchone()[0]

            run_parsers()
            make_send_list(old_max_id)
            logging.info("Цикл мониторинга завершён")

            time.sleep(INTERVAL * 60)

        except KeyboardInterrupt:
            print("\nПрограмма остановлена.")
            break
        except (sqlite3.Error, OSError, KeyError, ValueError) as error:
            print(f"Ошибка программы: {error}")
            logging.exception("Ошибка программы")
            time.sleep(INTERVAL * 60)


if __name__ == "__main__":
    main()