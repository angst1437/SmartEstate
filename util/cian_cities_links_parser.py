from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3

driver = webdriver.Chrome()

cities_conn = sqlite3.connect('cities.db')
links_conn = sqlite3.connect('../parsers/cian/links.db')
cities_cursor = cities_conn.cursor()
links_cursor = links_conn.cursor()

cities_cursor.execute('SELECT * FROM cities')
cities_from_db = cities_cursor.fetchall()

cities = [city[0] for city in cities_from_db]




for city_name in cities:
    city = city_name if city_name != "Уфа" else "Башкортостан"
    driver.get("https://www.cian.ru/")
    time.sleep(2)

    geo_switcher = driver.find_element(By.XPATH, "//div[@data-name='GeoSwitcher']//button")
    geo_switcher.click()

    city_input = driver.find_element(By.XPATH, "//input[@placeholder='Выберите регион или город']")
    city_input.send_keys(Keys.CONTROL, "a")
    city_input.send_keys(Keys.DELETE)
    city_input.send_keys(city)

    driver.execute_script("arguments[0].blur();", city_input)

    city_input.click()
    time.sleep(2)

    suggestions = driver.find_elements(By.XPATH, f'//div[@data-name="GeoSuggest"]//span[contains(text(), "{city}")]')

    try:
        for suggestion in suggestions:
            if suggestion.text == city:
                suggestion.click()
                break
    except:
        continue

    time.sleep(2)

    home_url = driver.current_url

    wait = WebDriverWait(driver, 10)
    # rooms_button = driver.find_element(By.XPATH, '//div[@data-mark="FilterRoomsCount"]//button')
    rooms_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="1, 2 комн."]')))
    rooms_button.click()

    deselect_1_room = driver.find_element(By.XPATH, '//button[text()="1"]')
    deselect_2_room = driver.find_element(By.XPATH, '//button[text()="2"]')

    deselect_1_room.click()
    deselect_2_room.click()

    find_button = driver.find_element(By.XPATH, '//a[@data-mark="FiltersSearchButton"]')

    find_button.click()

    time.sleep(1)

    buy_link = driver.current_url

    driver.get(home_url)
    time.sleep(2)

    rent_button = driver.find_element(By.XPATH, '//a[text()="Снять"]')

    rent_button.click()

    # rooms_button = driver.find_element(By.XPATH, '//div[@data-mark="FilterRoomsCount"]//button')
    rooms_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="1, 2 комн."]')))
    rooms_button.click()

    deselect_1_room = driver.find_element(By.XPATH, '//button[text()="1"]')
    deselect_2_room = driver.find_element(By.XPATH, '//button[text()="2"]')

    deselect_1_room.click()
    deselect_2_room.click()

    find_button = driver.find_element(By.XPATH, '//a[@data-mark="FiltersSearchButton"]')

    find_button.click()

    time.sleep(1)

    rent_link = driver.current_url

    print(f"{city}: {buy_link}, {rent_link}")

    links_cursor.execute("INSERT INTO links VALUES (?, ?, ?)", (city_name, buy_link, rent_link))
    links_conn.commit()
driver.quit()
