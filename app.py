from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import re

app = Flask(__name__)

def start_webdriver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"  # Ścieżka do Chrome w Render
    driver = webdriver.Chrome(options=options)
    return driver

def search_product(driver, product_code):
    search_url = f"https://epstryk.pl/pl/szukaj/?search_lang=pl&search=product&string={product_code}"
    driver.get(search_url)
    time.sleep(3)

    try:
        product_link = driver.find_element(By.CSS_SELECTOR, "a.productTileIconV1__img").get_attribute("href")
        driver.get(product_link)
        time.sleep(3)
    except Exception:
        print(f"Błąd: Nie znaleziono wyników dla kodu produktu: {product_code}")
        return None

    return extract_product_data(driver, product_link)

def extract_product_data(driver, product_link):
    try:
        product_name = driver.find_element(By.CSS_SELECTOR, ".productCardMain__name.header.-h1.grow").text
        product_code = driver.find_element(By.XPATH, "//span[contains(text(), 'Kod produktu:')]/following-sibling::span").text
        catalog_price = driver.find_element(By.XPATH, "//span[contains(text(), 'Cena katalogowa netto:')]/following-sibling::span").text
        your_price = driver.find_element(By.CSS_SELECTOR, ".productParam__value.-bold.productParam__value--big").text
        image_url = driver.find_element(By.CSS_SELECTOR, ".productFoto__zoom img").get_attribute("src")
        
        # Pobieranie identyfikatora produktu z kodu strony
        page_source = driver.page_source
        match = re.search(r"fbq\('track', 'ViewContent', {content_type:'product', content_ids:\['(\d+)'\]", page_source)
        if match:
            product_id = match.group(1)
            print(f"Identyfikator produktu znaleziony w JavaScript: {product_id}")
        else:
            print("Nie udało się znaleźć identyfikatora produktu.")
            return None

        return {
            "name": product_name,
            "code": product_code,
            "catalog_price": catalog_price,
            "your_price": your_price,
            "image_url": image_url,
            "id": product_id,
            "link": product_link
        }
    except Exception as e:
        print(f"Błąd podczas pobierania danych produktu: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_codes = [request.form.get(f"product_code{i+1}") for i in range(10)]
        driver = start_webdriver()

        try:
            product_data_list = []
            for code in product_codes:
                if code:
                    data = search_product(driver, code)
                    if data:
                        product_data_list.append(data)
        finally:
            driver.quit()

        # Generowanie kodu HTML dla wszystkich produktów
        html_code = ""
        for product_data in product_data_list:
            product_html = f"""
            <div class="product-card">
                <a href="{product_data['link']}" target="_blank">
                    <img src="{product_data['image_url']}" alt="{product_data['name']}" width="200" height="200">
                </a>
                <h2><a href="{product_data['link']}" target="_blank">{product_data['name']}</a></h2>
                <p class="catalog-price"><s>{product_data['catalog_price']}</s></p>
                <p class="your-price" style="color: red; font-weight: bold;">{product_data['your_price']}</p>
                <a href="https://epstryk.pl/pl/order/basket.html?add_product[{product_data['id']}]=1">
                    <button>Kup teraz</button>
                </a>
            </div>
            """
            html_code += product_html

        return render_template("index.html", product_data=product_data_list, html_code=html_code)

    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
