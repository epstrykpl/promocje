from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def search_product(product_code):
    search_url = f"https://epstryk.pl/pl/szukaj/?search_lang=pl&search=product&string={product_code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Błąd: Nie udało się pobrać strony dla kodu produktu {product_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        product_link = soup.select_one("a.productTileIconV1__img")["href"]
        full_product_link = f"https://epstryk.pl{product_link}"

        product_response = requests.get(full_product_link, headers=headers)
        if product_response.status_code != 200:
            print(f"Błąd: Nie udało się pobrać strony produktu {product_code}")
            return None

        product_soup = BeautifulSoup(product_response.text, 'html.parser')
        product_name = product_soup.select_one(".productCardMain__name.header.-h1.grow").text.strip()
        product_code = product_soup.select_one("span:contains('Kod produktu:') + span").text.strip()
        catalog_price = product_soup.select_one("span:contains('Cena katalogowa netto:') + span").text.strip()
        your_price = product_soup.select_one(".productParam__value.-bold.productParam__value--big").text.strip()
        image_url = product_soup.select_one(".productFoto__zoom img")["src"]

        return {
            "name": product_name,
            "code": product_code,
            "catalog_price": catalog_price,
            "your_price": your_price,
            "image_url": image_url,
            "link": full_product_link
        }
    except Exception as e:
        print(f"Błąd podczas analizy HTML dla produktu {product_code}: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_codes = [request.form.get(f"product_code{i+1}") for i in range(10)]
        product_data_list = []

        for code in product_codes:
            if code:
                data = search_product(code)
                if data:
                    product_data_list.append(data)

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
                <a href="https://epstryk.pl/pl/order/basket.html?add_product[{product_data['code']}]=1">
                    <button>Kup teraz</button>
                </a>
            </div>
            """
            html_code += product_html

        return render_template("index.html", product_data=product_data_list, html_code=html_code)

    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
