import logging
import os
import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify

from job import run_parse_and_send

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================
# APP
# ============================================================

app = Flask(__name__)

# Статус последнего запуска (thread-safe через lock)
_status_lock = threading.Lock()
_last_status = {"state": "idle", "started_at": None, "finished_at": None, "error": None}


def _run_job_tracked():
    """Обёртка над job — обновляет статус до/после."""
    with _status_lock:
        _last_status.update(state="running", started_at=datetime.utcnow().isoformat(), finished_at=None, error=None)
    try:
        run_parse_and_send()
        with _status_lock:
            _last_status.update(state="ok", finished_at=datetime.utcnow().isoformat())
    except Exception as exc:
        logger.exception("Ошибка при парсинге")
        with _status_lock:
            _last_status.update(state="error", finished_at=datetime.utcnow().isoformat(), error=str(exc))


# ============================================================
# SCHEDULER  (каждый день в 12:00 UTC)
# ============================================================

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(
    _run_job_tracked,
    trigger=CronTrigger(hour=12, minute=0),
    id="daily_parse",
    name="Daily lenta.ru parse",
    replace_existing=True,
)
scheduler.start()
if os.getenv("RUN_ON_START", "false").lower() == "true":
    thread = threading.Thread(target=_run_job_tracked, daemon=True)
    thread.start()
logger.info("Scheduler запущен. Следующий запуск: %s", scheduler.get_job("daily_parse").next_run_time)


# ============================================================
# ROUTES
# ============================================================

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/parse", methods=["POST"])
def parse_now():
    """Ручной запуск парсера (не блокирует запрос)."""
    with _status_lock:
        if _last_status["state"] == "running":
            return jsonify({"message": "Парсер уже запущен"}), 409

    thread = threading.Thread(target=_run_job_tracked, daemon=True)
    thread.start()
    return jsonify({"message": "Парсинг запущен"}), 202


@app.route("/status")
def status():
    with _status_lock:
        return jsonify(_last_status), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)