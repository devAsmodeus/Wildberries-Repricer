import time
import traceback
import pyautogui

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver

import selenium.common.exceptions


def get_coefficient() -> float:
    driver, coefficient = create_chrome(), 1.0
    driver.implicitly_wait(60)
    try:
        driver.get('https://www.wildberries.ru')
        time.sleep(10)
        for card in driver.find_elements(By.CSS_SELECTOR, 'a[class*="product-card__link"]'):
            script = "return document.querySelector('.product-card__wrapper').innerText;"
            card_description: str = driver.execute_script(script, card)
            if 'с WB Кошельком' in card_description.lower():
                price_count = card_description.count('₽') - 1
            else:
                price_count = card_description.count('₽')
            card.click()
            coefficient = update_card(driver, price_count)
            break
        else:
            coefficient = 1.0
    except Exception as exception:
        print(repr(exception))
        raise ValueError('Не получен коэффициент кошелька')
    finally:
        driver.close()
        return coefficient


def update_card(driver: webdriver.Chrome, price_count: int) -> float:
    tries = 3
    while tries:
        time.sleep(5)
        wait = WebDriverWait(driver, 30)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class*=priceBlockContent]')))
        script = "return document.querySelector('div[class*=priceBlockContent]').innerText;"
        prices: str = driver.execute_script(script)
        if prices.count('₽') in (price_count, price_count + 1, price_count + 2):
            prices: list[str] = ''.join(prices.split()).split('₽')
            wallet_price, default_price, *_ = prices
            return round(int(wallet_price) / int(default_price), 2)
        else:
            tries -= 1
            pyautogui.press('f5')
    else:
        return 1.0


def create_chrome() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    for location in ('Program Files', 'Program Files (x86)'):
        try:
            options.binary_location = fr'C:\{location}\Google\Chrome\Application\chrome.exe'
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option("prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            })
            # options.add_argument("--incognito")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(r"--user-data-dir=C:\Users\Administrator\AppData\Local\Google\ChromeSelenium")
            options.add_argument("--profile-directory=Profile 1")
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(10)
            return driver
        except selenium.common.exceptions.WebDriverException as selenium_exception:
            print(traceback.format_exc())
            continue
    else:
        raise ValueError('WebDriver не найден')
