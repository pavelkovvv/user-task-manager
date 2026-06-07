"""Асинхронная доставка записей журнала: основной поток кладёт сообщения в очередь, на диск пишет отдельный поток"""

import atexit
import logging
from logging.handlers import QueueHandler, RotatingFileHandler
from pathlib import Path
from queue import Queue
from threading import Thread

from settings import config_loader


def _as_bool(value: object, default: bool) -> bool:
    """Приведение строки конфига к bool с запасными значением по умолчанию при None"""
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes", "on"}


class AsyncLogWriter:
    """Один writer-поток пишет в RotatingFileHandler; производители блокируются только если очередь полна (~10к)"""

    _STOP = object()

    def __init__(self) -> None:
        self.queue = Queue(maxsize=10_000)
        self.log_file = self._resolve_log_file()
        self.handler = RotatingFileHandler(
            self.log_file,
            maxBytes=50_000_000,
            backupCount=10,
            encoding="utf-8",
        )
        self.thread = Thread(target=self._write_loop, daemon=True)
        self.thread.start()
        atexit.register(self.shutdown)

    @staticmethod
    def _resolve_log_file() -> str:
        """Путь файла журнала: из конфига или `./logs/app.log`; при недоступности конфиг-пути — fallback"""
        configured = config_loader("LOG_FILE")
        default_path = Path("logs") / "app.log"
        target = Path(configured) if configured else default_path

        try:
            # Предпочтительный путь из конфига; создаем родительскую директорию при необходимости
            target.parent.mkdir(parents=True, exist_ok=True)
            return str(target)
        except OSError:
            # Резервный путь внутри проекта, чтобы приложение не падало на старте,
            # если путь из конфига недоступен для записи (например, /var/log)
            fallback = default_path
            fallback.parent.mkdir(parents=True, exist_ok=True)
            return str(fallback)

    def _write_loop(self) -> None:
        while True:
            record = self.queue.get()
            try:
                # Маркер _STOP ставится в shutdown: без него join к потоку мог бы повиснуть на get()
                if record is self._STOP:
                    break
                self.handler.emit(record)
            except Exception:
                # Поток логирования не должен завершаться молча при ошибке записи
                logging.getLogger(__name__).exception("Не удалось записать запись в журнал")
            finally:
                self.queue.task_done()

    def shutdown(self) -> None:
        """Корректное завершение: дожаться очередь, поток успевает записать последние сообщения перед exit"""
        if not self.thread.is_alive():
            return
        # Перед завершением дожидаемся записи всех оставшихся логов из очереди
        self.queue.put(self._STOP)
        self.queue.join()
        self.thread.join(timeout=2)
        self.handler.close()


log_writer = AsyncLogWriter()

logger = logging.getLogger("user-task-manager")
logger.handlers.clear()
logger.addHandler(QueueHandler(log_writer.queue))
logger.setLevel(logging.DEBUG)
logger.propagate = False
