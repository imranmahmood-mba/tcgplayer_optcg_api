from selenium import webdriver

driver = webdriver.Chrome()

driver.set_page_load_timeout(30)
driver.get("https://www.facebook.com/")
driver.maximize_window()
driver.quit()