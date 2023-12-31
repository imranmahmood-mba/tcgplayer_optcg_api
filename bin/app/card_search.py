from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import logging
import logging.config
import time
from selenium.common.exceptions import TimeoutException
import os 
import requests

# Get the absolute directory of the current script
abs_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the logging configuration file

logging_config_path = '/Users/imranmahmood/Projects/tcg_api/util/logging_to_file.conf'
#= os.path.join(abs_dir, '..', 'util', 'logging_to_file.conf')

logging.config.fileConfig(fname=logging_config_path)

# Get the custom Logger from Configuration File
logger = logging.getLogger(__name__)

def create_driver():
    """
    Creates and returns a Chrome driver with specified options.
    Returns:
        driver (WebDriver): The created Chrome driver.
    Raises:
        Exception: If there is an error while creating the driver.
    """
    try:
        # Setup Chrome options
        logging.info("Creating driver")
        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.set_capability("browserVersion", "98")

        driver = webdriver.Chrome()

    except Exception as e:
        logger.error(f"Failed to start the Chrome driver. Exception: {e}")
        raise e
    else:
        logger.info("Driver successfully created.")
    return driver

def card_search(card_name, url, page_num=1):
    """Returns url to scrape if response is 200

    Args:
        card_name (str): user submitted query param
        url (str): the url that is going to generate search results to scrape
        page_num (int, optional): page number to scrape, used to increment through search results pages. Defaults to 1.

    Returns:
        str: url to scrape
    """
    url = f"https://www.tcgplayer.com/search/one-piece-card-game/product?productLineName=one-piece-card-game&q={card_name}&view=grid&page={page_num}"
    response = requests.get(url)
    if response.status_code == 200:
        print("Success")
        return url
    else:
        print('error')

def retry_scrape(wait_time=12, max_attempts=3):
    """Decorator function for retrying scrape attempts

    Args:
        attempts (int, optional): _description_. Defaults to 0.
        wait_time (int, optional): _description_. Defaults to 12.
        max_attempts (int, optional): _description_. Defaults to 3.
    Raises:
        e: TimeoutException
        e: Catch-all

    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            current_wait_time = wait_time
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except TimeoutException as e:
                    attempts += 1
                    logging.error(f"Attempt {attempts} error in {func.__name__}: {e}")
                    if attempts >= max_attempts:
                        raise e
                    else:
                        logging.info(f"Retrying in {wait_time} seconds.")
                        time.sleep(wait_time)
                        current_wait_time += attempts
                except Exception as e:
                    logging.error(f"Error in {func.__name__}: {e}")
                    raise e
        return wrapper
    return decorator

@retry_scrape()
def get_text_from_page(driver, search_page_url, **element_selectors:str):
    """Scrapes the text from a given element on a given page

    Args:
        driver (driver): This is the driver object needed to scrape a page
        search_page_url (str): URL of page to be scraped
        element_selectors(str): Element(s) to be scrape from page
    Returns:
        dict: Dictionary of scraped css elements
    """
    
    # wait for the page to load completely
    wait = WebDriverWait(driver, 12)
    # find all the elements
    elements = {}
    for key, selector in element_selectors.items():
        found_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
        elements[key] = found_elements 
    logging.info(f"Elements from {search_page_url} successfully loaded.") 
    return elements

def format_api_data(json_data):
    """Helper function used to take the output from app.search_card and return formatted repsonse

    Args:
        json_data (dict): Dictionary of lists containing results from each scraped page. 

    Returns:
        list: Formatted list of dictionaries, each dictionary contains all scraped elements for each individual card.
    """
    formatted_data = []

    for item_group in json_data['results']:
        # Extract keys and ensure they are present in the item_group
        keys = item_group.keys()

        # Prepare lists to be zipped
        lists_to_zip = [item_group[key] for key in keys if isinstance(item_group[key], list)]

        # Zip the lists and process each entry
        for zipped_entry in zip(*lists_to_zip):
            entry = {key: value for key, value in zip(keys, zipped_entry)}
            formatted_data.append(entry)

    return formatted_data

def process_element(element: WebElement, key: str, *args: str) -> str:
    """
    Returns the 'href' attribute of the element if the key is specified in the arguments, 
    otherwise returns the text of the element.

    Args:
    element (WebElement): The Selenium WebElement to process.
    key (str): The key corresponding to the element.
    *args (str): Additional arguments specifying when to extract 'href'.

    Returns:
    str: 'href' attribute or text of the element.
    """
    try:
        href = element.get_attribute('href')
        return href if key in args else element.text
    except Exception as e:
        print(f"Error processing element: {e}")
        return ""
    
@retry_scrape()
def get_all_products():        
    try:
        all_results = {}
        all_results_expanded = {}
        url = f'https://www.tcgplayer.com/search/one-piece-card-game/product?productLineName=one-piece-card-game&page=1&view=grid'
        driver = create_driver()
        driver.get(url)
        while True:            
            # scrapes each element from search results page
            data = get_text_from_page(driver, url, 
                                      names='.search-result__title', 
                                      set_name='.search-result__subtitle', 
                                link="a[data-testid^='search-result__image']")
            print(len(data['link']))
            for i in range(len(data['link'])):
                key = data['names'][i].text + ' ' + data['set_name'][i].text 

                print(key)
                all_results[key] = data['link'][i].get_attribute('href')


            all_results.append(all_results_expanded)

            next_button = driver.find_elements(By.CSS_SELECTOR, '.tcg-standard-button__content')[-1]
            next_button.click()

            WebDriverWait(driver, 10).until(
                EC.url_changes(url)
            )           
            url = driver.current_url
    except Exception as e:
        logging.info(f'Exception: {e} in {get_all_products.func_name}')
    finally:
        if driver:
            driver.quit()
        return all_results


