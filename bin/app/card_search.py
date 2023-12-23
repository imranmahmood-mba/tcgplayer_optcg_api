from selenium import webdriver
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


def get_text_from_page(driver, search_page_url, **element_selectors:str):
    """Scrapes the text from a given element on a given page

    Args:
        driver (driver): This is the driver object needed to scrape a page
        search_page_url (str): URL of page to be scraped
        element_selectors(str): Element(s) to be scrape from page

    Raises:
        e: TimeoutException
        e: Catch-all

    Returns:
        _type_: _description_
    """
    attempts = 0
    wait_time = 12
    max_attempts = 3
    
    while attempts < max_attempts:
        try:
            driver.get(search_page_url)
            logging.info("Accessing website...")
            
            # wait for the page to load completely
            wait = WebDriverWait(driver, wait_time)
            logging.info(f"wait: {wait}")
            # find all the elements
            elements = {}
            for key, selector in element_selectors.items():
                found_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                elements[key] = found_elements 
            logging.info(f"Elements from {search_page_url} successfully loaded.") 
            logging.info(elements)          
            return elements
        except TimeoutException as e:
            attempts += 1
            logging.error(f"Attempt {attempts} error in the method download_elements_from_webpage(): {e} \n URL: {search_page_url}")
            if attempts >= max_attempts:
                raise e
            else:
                logging.info(f"Retrying in {wait_time} seconds.")
                wait_time += attempts
        except Exception as e:
            logging.error(f"Error in the method download_elements_from_webpage(): {e} \n URL: {search_page_url}")
            raise e

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