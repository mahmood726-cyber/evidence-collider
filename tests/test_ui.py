import subprocess
import sys
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

REPO_ROOT = Path(__file__).resolve().parents[1]
PORT = 8094
URL = f"http://127.0.0.1:{PORT}/index.html"


def _build_driver():
    browser_attempts = [
        ("chrome", webdriver.Chrome, ChromeOptions, ["--headless=new"]),
        ("edge", webdriver.Edge, EdgeOptions, ["--headless=new"]),
        ("firefox", webdriver.Firefox, FirefoxOptions, ["--headless"]),
    ]
    errors: list[str] = []
    for name, constructor, options_cls, args in browser_attempts:
        try:
            options = options_cls()
            for arg in args:
                options.add_argument(arg)
            return constructor(options=options)
        except Exception as exc:  # pragma: no cover - only reached on browser setup failure
            errors.append(f"{name}: {exc}")
    pytest.skip("No local Selenium browser could be launched: " + " | ".join(errors))


@pytest.fixture
def static_server():
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=str(REPO_ROOT),
    )
    time.sleep(2)
    try:
        yield
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=10)


def test_collider_ui_integrity(static_server):
    driver = _build_driver()
    try:
        driver.get(URL)
        time.sleep(3)

        cards = driver.find_elements(By.CLASS_NAME, "desert-card")
        assert len(cards) > 0, "No evidence desert cards rendered"

        deserts = driver.find_elements(By.CLASS_NAME, "DESERT")
        assert len(deserts) > 0, "No 'DESERT' status cards found"

        sdi_text = driver.find_element(By.CLASS_NAME, "stat-line").text
        assert "IHME SDI" in sdi_text, "SDI value missing from card"
    finally:
        driver.quit()
