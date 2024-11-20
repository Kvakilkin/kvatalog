import requests
import pandas as pd
from retry import retry

def get_data_from_search(query: str, low_price: int, top_price: int, discount: int, page: int) -> dict:
    """Сбор данных по поисковому запросу"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0)"}
    url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}&page={page}' \
          f'&priceU={low_price * 100};{top_price * 100}&discount={discount}'
    r = requests.get(url, headers=headers)
    print(f'Статус: {r.status_code} Страница {page} Идет сбор...')
    if r.status_code != 200:
        print(f'Ошибка при запросе страницы {page}: {r.status_code}')
    return r.json()

def get_data_from_json(json_file: dict) -> list:
    """Извлекаем из json данные"""
    data_list = []
    if 'data' in json_file and 'products' in json_file['data']:
        for data in json_file['data']['products']:
            sku = data.get('id')
            name = data.get('name')
            price = int(data.get("priceU") / 100)
            salePriceU = int(data.get('salePriceU') / 100) if data.get('salePriceU') else None
            cashback = data.get('feedbackPoints')
            sale = data.get('sale')
            brand = data.get('brand')
            rating = data.get('rating')
            supplier = data.get('supplier')
            supplierRating = data.get('supplierRating')
            feedbacks = data.get('feedbacks')
            reviewRating = data.get('reviewRating')
            promoTextCard = data.get('promoTextCard')
            promoTextCat = data.get('promoTextCat')
            data_list.append({
                'id': sku,
                'name': name,
                'price': price,
                'salePriceU': salePriceU,
                'cashback': cashback,
                'sale': sale,
                'brand': brand,
                'rating': rating,
                'supplier': supplier,
                'supplierRating': supplierRating,
                'feedbacks': feedbacks,
                'reviewRating': reviewRating,
                'promoTextCard': promoTextCard,
                'promoTextCat': promoTextCat,
                'link': f'https://www.wildberries.ru/catalog/{data.get("id")}/detail.aspx?targetUrl=BP'
            })
    return data_list

@retry(Exception, tries=-1, delay=0)
def scrap_page(query: str, low_price: int, top_price: int, discount: int, page: int) -> dict:
    """Сбор данных со страниц"""
    return get_data_from_search(query, low_price, top_price, discount, page)

def save_excel(data: list, filename: str):
    """Сохранение результата в excel файл"""
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'{filename}.xlsx')
    df.to_excel(writer, sheet_name='data', index=False)
    writer.close()
    print(f'Все сохранено в {filename}.xlsx\n')

def parser(query: str, low_price: int = 1, top_price: int = 1000000, discount: int = 0):
    """Основная функция"""
    data_list = []
    page = 1
    while True:
        data = scrap_page(query, low_price, top_price, discount, page)
        products = get_data_from_json(data)
        print(f'Добавлено позиций: {len(products)} на странице {page}')
        
        if not products:  # Если нет товаров, выходим из цикла
            break
        
        data_list.extend(products)
        page += 1  # Переходим к следующей странице

    print(f'Сбор данных завершен. Собрано: {len(data_list)} товаров.')
    save_excel(data_list, f'{query}_from_{low_price}_to_{top_price}')

if __name__ == '__main__':
    while True:
        try:
            poisk = input('Введите поисковый запрос(q, для выхода): \n')
            if poisk == 'q':
                break
            low_price = int(input('Введите минимальную сумму товара: '))
            top_price = int(input('Введите максимальную сумму товара: '))
            discount = int(input('Введите минимальную скидку(введите 0 если без скидки): '))
            parser(query=poisk, low_price=low_price, top_price=top_price, discount=discount)
        except Exception as e:
            print(f'Произошла ошибка: {e}. Перезапуск...')