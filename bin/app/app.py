from flask import Flask, request, jsonify
from card_search import create_driver, get_text_from_page, card_search, format_api_data
import logging
import logging.config
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Get the absolute directory of the current script
abs_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the logging configuration file

logging_config_path = '/Users/imranmahmood/Projects/tcg_api/util/logging_to_file.conf'

logging.config.fileConfig(fname=logging_config_path)

# Get the custom Logger from Configuration File
logger = logging.getLogger(__name__)

app = Flask(__name__)

# endpoint that returns TCGPlayer card search results
@app.route('/api/search', methods=['GET'])
def search_card(): 
    card_name = request.args.get('card_name')
    driver = create_driver()            
    if not card_name:
        return jsonify({'error': 'Card name is required'}), 400
    try:
        page_num = 1
        all_results = []
        while True:
            url = f"https://www.tcgplayer.com/search/one-piece-card-game/product?productLineName=one-piece-card-game&q={card_name}&view=grid&page={page_num}" 
            
            # scrapes each element from search results page
            data = get_text_from_page(driver, url, prices='.inventory__price-with-shipping', names='.search-result__title', 
                                        set_name='.search-result__subtitle', market_price='.search-result__market-price--value',
                                          rarity='.search-result__rarity span:nth-child(1)', 
                                          number_of_listings='.notification--message , .inventory__listing-count-block span')
            all_results.append({key: [element.text for element in elements_list] 
                        for key, elements_list in data.items()} )

            next_button = driver.find_elements(By.CSS_SELECTOR, '.tcg-standard-button__content')[-1]
                      
            next_button.click()
            WebDriverWait(driver, 10).until(
                EC.url_changes(url)
            )           
            url = driver.current_url
            page_num += 1 

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if driver:
            driver.quit()
        return jsonify(format_api_data({'results':all_results}))

if __name__ == '__main__':
    app.run(debug=True)

