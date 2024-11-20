import time
import json
import pandas as pd
from selenium import webdriver
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from curl_cffi import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получение параметров от пользователя
try:
    minprice = float(input("Введите минимальную цену: "))
    maxprice = float(input("Введите максимальную цену: "))
    search_query = input("Введите запрос для поиска: ")
except ValueError:
    print("Ошибка: Пожалуйста, введите числовые значения для цен.")
    exit(1)

def init_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

def scrolldown(driver, deep, delay=0.5):
    for _ in range(deep):
        driver.execute_script('window.scrollBy(0, 500)')
        time.sleep(delay)

def get_product_info(product_url):
    session = requests.Session()
    try:
        raw_data = session.get("https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=" + product_url)
        json_data = json.loads(raw_data.content.decode())
        return json_data
    except Exception as e:
        logging.error(f"Ошибка при получении данных о продукте: {e}")
        return None

def extract_product_info(json_data):
    try:
        full_name = json_data["seo"]["title"]
        if json_data["layout"][0]["component"] == "userAdultModal":
            product_id = str(full_name.split()[-1])[1:-1]
            return (product_id, full_name, "Товар для лиц старше 18 лет", None, None, None, None)
        
        script_data = json.loads(json_data["seo"]["script"][0]["innerHTML"])
        description = script_data.get("description", "Нет описания")
        image_url = script_data.get("image", "Нет изображения")
        price = float(script_data['offers']['price'])
        price_currency = script_data['offers']['priceCurrency']
        rating = script_data.get("ratingValue", "Нет рейтинга")
        rating_counter = script_data.get("reviewCount", 0)
        product_id = script_data["sku"]
        return (product_id, full_name, description, f"{price} {price_currency}", rating, rating_counter, image_url)
    except (KeyError, IndexError) as e:
        logging.error(f"Ошибка при извлечении данных о товаре: {e}")
        return None

def get_searchpage_cards(driver, url):
    driver.get(url)
    # Выполняем несколько прокруток для загрузки всех товаров
    for _ in range(5):  # Количество прокруток, можно изменить в зависимости от нужд
        scrolldown(driver, 5)  # Прокручиваем вниз на 5 пикселей за раз
        time.sleep(0.5)  # Задержка, чтобы дать время для загрузки контента

    search_page_html = BeautifulSoup(driver.page_source, "html.parser")
    content = search_page_html.find("div", {"id": "layoutPage"})
    all_cards = []

    if content:
        content_with_cards = content.find("div", {"class": "widget-search-result-container"})
        if content_with_cards:
            content_with_cards = content_with_cards.find("div").findChildren(recursive=False)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for card in content_with_cards:
                    card_url = card.find("a", href=True)["href"]
                    futures.append(executor.submit(get_product_info, card_url))

                for future in futures:
                    json_data = future.result()
                    if json_data:
                        product_info = extract_product_info(json_data)
                        if product_info:
                            product_id, full_name, description, price, rating, rating_counter, image_url = product_info
                            if price:
                                price_value = float(price.split()[0])
                                if minprice <= price_value <= maxprice:  # Фильтрация по ценам
                                    card_info = {
                                        product_id: {
                                            "short_name": card.find("span", {"class": "tsBody500Medium"}).text,
                                            "full_name": full_name,
                                            "description": description,
                                            "url": "https://ozon.ru" + card_url,
                                            "rating": rating,
                                            "rating_counter": rating_counter,
                                            "price": price,
                                            "image_url": image_url
                                        }
                                    }
                                    all_cards.append(card_info)
                                    logging.info(f"{product_id} - DONE")

            # Проверка на наличие следующей страницы
            content_with_next = [div for div in content.find_all("a", href=True) if "Дальше" in str(div)]
            if content_with_next:
                next_page_url = "https://www.ozon.ru" + content_with_next[0]["href"]
                all_cards.extend(get_searchpage_cards(driver, next_page_url))
        else:
            logging.warning("Не удалось найти карточки на странице.")
    else:
        logging.warning("Не удалось найти контент на странице поиска.")
    
    return all_cards

def save_to_excel(data, filename):
    all_products = []
    for card in data:
        for product_id, product_info in card.items():
            all_products.append({
                "ID": product_id,
                "Short Name": product_info["short_name"],
                "Full Name": product_info["full_name"],
                "Description": product_info["description"],
                "URL": product_info["url"],
                "Rating": product_info["rating"],
                "Rating Counter": product_info["rating_counter"],
                "Price": product_info["price"],
                "Image URL": product_info["image_url"],
                "Date Parsed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    df = pd.DataFrame(all_products)
    df.to_excel(f"{filename}.xlsx", index=False)
    logging.info(f"Данные успешно сохранены в {filename}.xlsx")

def clear_old_data(filename):
    if os.path.exists(f"{filename}.xlsx"):
        os.remove(f"{filename}.xlsx")
        logging.info(f"Старые данные {filename}.xlsx удалены.")

if __name__ == "__main__":
    filename = "ozon_products"
    clear_old_data(filename)  # Очистка старых данных перед новым парсингом
    driver = init_webdriver()
    all_cards = []
    url_search = f"https://www.ozon.ru/search/?text={search_query}&from_global=true"
    try:
        search_cards = get_searchpage_cards(driver, url_search)
        all_cards.extend(search_cards)
        logging.info(f"Я успешно нашёл {len(search_cards)} по поиску {search_query}")
    except Exception as e:
        logging.error(f"Ошибка при парсинге по запросу {search_query}: {e}")
    
    save_to_excel(all_cards, filename)
    driver.quit()
