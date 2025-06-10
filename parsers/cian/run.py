import asyncio
import sqlite3
from datetime import datetime

from cian_parser import EstatePageParser, UrlCollector
from util import DBHelper
from util.proxy_manager import ProxyManager
import httpx
import logging

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

batch_size = 50

async def url_collector_task(queue: asyncio.Queue, start_url: str, client: httpx.AsyncClient):
    logger.info(f"Старт сбора ссылок с: {start_url}")
    collector = UrlCollector(client)
    current_url = start_url

    for i in range(10):  # 10 страниц
        logger.info(f"[Collector] Обрабатываем страницу {i+1}: {current_url}")
        result = await collector.get_urls_from_page(current_url)
        if result is None or not result["urls"]:
            logger.warning(f"[Collector] Нет ссылок на странице {current_url}. Остановка.")
            break

        for link in result["urls"]:
            await queue.put({"url": link, "page": result["page"], "retries": 0})
            logger.debug(f"[Collector] Добавлена ссылка: {link} (стр. {result['page']})")

        current_url = collector.get_next_page(current_url)
        await asyncio.sleep(1)

    logger.info("[Collector] Завершение. Посылаем сигналы завершения воркерам.")
    for _ in range(8):
        await queue.put(None)


async def page_parser_worker(queue: asyncio.Queue, dbhelper_config: dict, worker_id: int, proxy_manager: ProxyManager):
    db = DBHelper.DBHelper(**dbhelper_config)
    processed = 0
    max_retries = 3

    logger.info(f"[Worker {worker_id}] Запущен")

    while True:
        task = await queue.get()
        if task is None:
            logger.info(f"[Worker {worker_id}] Получен сигнал завершения")
            break

        url = task["url"]
        page = task["page"]
        retries = task.get("retries", 0)

        client, proxy = proxy_manager.get_httpx_client()

        try:
            logger.info(f"[Worker {worker_id}] Начинаем парсинг: {url} (попытка {retries + 1}, прокси: {proxy})")
            parser = EstatePageParser(url=url, client=client)
            data = await parser.parse_page()
            data["page"] = page
            db.insert_ad(data)
            print(f"[Worker {worker_id}] Успешно: {url}")
            processed += 1
        except Exception as e:
            logger.warning(f"[Worker {worker_id}] Ошибка: {url} через {proxy}: {e}")
            proxy_manager.report_error(proxy)

            # Повторная попытка
            if retries < max_retries:
                logger.info(f"[Worker {worker_id}] Повторная попытка {retries + 1} для {url}")
                await queue.put({"url": url, "page": page, "retries": retries + 1})
            else:
                logger.error(f"[Worker {worker_id}] Превышено число попыток для {url}")
        finally:
            await client.aclose()

    logger.info(f"[Worker {worker_id}] Завершил работу. Всего обработано: {processed}")


async def main():
    db_config = {
        "dbname": "cian",
        "dbpassword": "1437"
    }

    logger.info("Чтение стартового URL из SQLite...")
    conn = sqlite3.connect("links.db")
    cur = conn.cursor()
    cur.execute("SELECT buy_link FROM links LIMIT 3;")
    row = cur.fetchall()
    if not row:
        logger.error("Не удалось получить стартовый URL из базы links.db")
        return
    start_url = row[2][0]
    cur.close()
    conn.close()
    logger.info(f"Стартовый URL: {start_url}")

    queue = asyncio.Queue(maxsize=1000)
    num_workers = 8
    logger.info(f"Используем {num_workers} воркеров")

    start_time = datetime.now()

    # Инициализация прокси
    logger.info("Инициализация менеджера прокси...")
    proxy_manager = ProxyManager()
    proxy_manager.init()
    logger.info("Прокси инициализированы")

    logger.info("Создание HTTP-клиента для сбора ссылок")
    async with httpx.AsyncClient(timeout=15.0) as general_client:
        logger.info("Запуск задач")
        producer = asyncio.create_task(url_collector_task(queue, start_url, general_client))
        consumers = [
            asyncio.create_task(page_parser_worker(queue, db_config, i, proxy_manager))
            for i in range(num_workers)
        ]

        await producer
        await asyncio.gather(*consumers)

    end_time = datetime.now()
    logger.info(f"Завершено за {end_time - start_time}")


if __name__ == "__main__":
    asyncio.run(main())
