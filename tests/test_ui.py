import os
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# sys.path anchor
import sys; from pathlib import Path; ROOT = Path(__file__).resolve().parent.parent.parent; sys.path.append(str(ROOT))
from browser_rotator import get_driver

PORT = 8094
server_proc = subprocess.Popen(['python', '-m', 'http.server', str(PORT)], cwd='evidence-collider')
time.sleep(2)

URL = f'http://localhost:{PORT}/index.html'

def test_collider_ui_integrity():
    driver = get_driver()
    try:
        driver.get(URL)
        time.sleep(3)
        
        # 1. Verify Card Presence
        cards = driver.find_elements(By.CLASS_NAME, 'desert-card')
        assert len(cards) > 0, "No evidence desert cards rendered"
        
        # 2. Verify Desert Classification
        deserts = driver.find_elements(By.CLASS_NAME, 'DESERT')
        assert len(deserts) > 0, "No 'DESERT' status cards found"
        
        # 3. Verify SDI rendering
        sdi_text = driver.find_element(By.CLASS_NAME, 'stat-line').text
        assert 'IHME SDI' in sdi_text, "SDI value missing from card"
        
        print("  PASS: Evidence Collider E2E Rigor Audit")
        
    finally:
        driver.quit()
        server_proc.terminate()

if __name__ == '__main__':
    test_collider_ui_integrity()