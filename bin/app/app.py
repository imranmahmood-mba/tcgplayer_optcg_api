from flask import Flask, request, jsonify
from card_search import create_driver, get_text_from_page, card_search, format_api_data
import logging
import logging.config
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask.views import MethodView
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

# Get the absolute directory of the current script
abs_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the logging configuration file

logging_config_path = '/Users/imranmahmood/Projects/tcg_api/util/logging_to_file.conf'

logging.config.fileConfig(fname=logging_config_path)

# Get the custom Logger from Configuration File
logger = logging.getLogger(__name__)

app = Flask(__name__)

# endpoint that returns TCGPlayer card search results
class TCGApi(MethodView):
    def __init__(self) -> None:
        self.driver = create_driver()            
    def get(self):
        card_name = request.args.get('card_name')
        card_url = request.args.get('card_url')
        
        if card_name:
            return self.search_card(card_name)
        elif card_url:
            return self.card_sales(card_url)
        else:
            return jsonify({'error': 'Invalid request'}), 400
    # @app.route('/api/search', methods=['GET'])
    def search_card(self, card_name): 
        card_name = request.args.get('card_name')
        if not card_name:
            return jsonify({'error': 'Card name is required'}), 400
        try:
            page_num = 1
            all_results = []
            while True:
                url = f"https://www.tcgplayer.com/search/one-piece-card-game/product?productLineName=one-piece-card-game&q={card_name}&view=grid&page={page_num}" 
                
                # scrapes each element from search results page
                self.driver.get(url)
                data = get_text_from_page(self.driver, url, prices='.inventory__price-with-shipping', names='.search-result__title', 
                                            set_name='.search-result__subtitle', market_price='.search-result__market-price--value',
                                            rarity='.search-result__rarity span:nth-child(1)', 
                                            number_of_listings='.notification--message , .inventory__listing-count-block span')
                all_results.append({key: [element.text for element in elements_list] 
                            for key, elements_list in data.items()} )

                next_button = self.driver.find_elements(By.CSS_SELECTOR, '.tcg-standard-button__content')[-1]
                        
                next_button.click()
                WebDriverWait(self.driver, 10).until(
                    EC.url_changes(url)
                )           
                url = self.driver.current_url
                page_num += 1 

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if self.driver:
                self.driver.quit()
            return jsonify(format_api_data({'results':all_results}))

    # @app.route('/api/card_sales', methods=['GET'])
    def card_sales(self, card_url):
        all_results = []
        card_url = request.args.get('card_url')
        if not card_url:
            return jsonify({'error': 'Card url is required'}), 400
        
        self.driver.get(card_url)
        wait = WebDriverWait(self.driver, 10)
        sales_history_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.modal__activator')))
        sales_history_button.click()
        while True:
            try:
                # Locate the button
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "sales-history-snapshot__load-more"))
                )
                # Click the button
                button.click()
            # Button no longer exists, break the loop    
            except ElementClickInterceptedException:
                break
            except TimeoutException:
                break
        prices = get_text_from_page(driver=self.driver, search_page_url=card_url, price='ul.is-modal li span.price', 
                                    date='ul.is-modal li span.date', condition='ul.is-modal li span.condition', 
                                    quantity='ul.is-modal li span.quantity')
        all_results.append({key: [element.text for element in elements_list] 
                            for key, elements_list in prices.items()} )        
        if self.driver:
                self.driver.quit()
        return jsonify(format_api_data({'results':all_results}))

        
# Register routes
app.add_url_rule('/api/search', view_func=TCGApi.as_view('search_card'))
app.add_url_rule('/api/card_sales', view_func=TCGApi.as_view('card_sales'))

if __name__ == '__main__':
    app.run(debug=True)

