import asyncio
import logging
from datetime import datetime

from util.proxy_manager import ProxyManager
from util import DBHelperOld
from avito_parser import AvitoParser
import httpx

# Логгирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def url_collector_task(queue: asyncio.Queue, base_url: str, client: httpx.AsyncClient):
    logger.info("[Collector] Запуск парсера ссылок")

    parser = AvitoParser(db_config={}, )
    await parser.start_browser()
    try:
        await parser.page.goto(base_url)
        urls = await parser.get_ads_urls()

        for url in urls:
            await queue.put({
                "url": url,
                "retries": 0
            })
            logger.debug(f"[Collector] Добавлена ссылка: {url}")

        logger.info(f"[Collector] Добавлено {len(urls)} ссылок")
    finally:
        await parser.close_browser()

    logger.info("[Collector] Завершение. Посылаем сигналы воркерам.")
    for _ in range(8):
        await queue.put(None)


async def page_parser_worker(queue: asyncio.Queue, db_config: dict, worker_id: int, proxy_manager: ProxyManager):
    logger.info(f"[Worker {worker_id}] Запуск")

    parser = AvitoParser(db_config)
    await parser.start_browser()

    processed = 0
    max_retries = 3

    while True:
        task = await queue.get()
        if task is None:
            logger.info(f"[Worker {worker_id}] Завершение по сигналу")
            break

        url = task["url"]
        retries = task.get("retries", 0)

        try:
            logger.info(f"[Worker {worker_id}] Обработка: {url} (попытка {retries + 1})")
            await parser.parse_ad(url)
            processed += 1
        except Exception as e:
            logger.warning(f"[Worker {worker_id}] Ошибка: {e}")
            if retries < max_retries:
                await queue.put({"url": url, "retries": retries + 1})
            else:
                logger.error(f"[Worker {worker_id}] Превышено число попыток для {url}")

    await parser.close_browser()
    logger.info(f"[Worker {worker_id}] Завершил работу. Всего: {processed}")


async def main():
    base_url = "https://www.avito.ru/all/kvartiry/prodam-ASgBAgICAUSSA8YQ?..."

    db_config = {
        "host": "localhost",
        "user": "user",
        "password": "password",
        "dbname": "your_db"
    }

    num_workers = 8
    queue = asyncio.Queue(maxsize=1000)

    logger.info("Инициализация прокси-менеджера")
    proxy_manager = ProxyManager()
    proxy_manager.init()

    logger.info(f"Старт сбора ссылок с {base_url}")
    start_time = datetime.now()

    async with httpx.AsyncClient(timeout=15.0) as client:
        producer = asyncio.create_task(url_collector_task(queue, base_url, client))
        consumers = [
            asyncio.create_task(page_parser_worker(queue, db_config, i, proxy_manager))
            for i in range(num_workers)
        ]
        await producer
        await asyncio.gather(*consumers)

    logger.info(f"Завершено за {datetime.now() - start_time}")


if __name__ == "__main__":
    asyncio.run(main())
