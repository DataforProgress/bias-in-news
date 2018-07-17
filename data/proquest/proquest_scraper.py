from selenium import webdriver
from selenium.webdriver.support.select import Select
from time import sleep
from math import ceil
import json
import sys
from datetime import date, timedelta, datetime

sys.setrecursionlimit(1500)

def try_until_success(to_exec, fail_after, sleep_time=0.5):
    """
    This method essentially allows selenium to continue trying to find an element until it appears, limited only by
    Python's recursion limit. This is very hacky, but it works.
    :param to_exec: python line to execute
    :param fail_after: fail after this many attempts, if None just continue attempting to recurse
    :param sleep_time: how long to sleep btwn tries
    :return:
    """
    if fail_after is not None:
        if fail_after == 0:
            exec(to_exec)
    fail_after = fail_after - 1 if fail_after is not None else None
    try:
        exec(to_exec)
    except:
        sleep(sleep_time)
        try_until_success(to_exec, fail_after)

def get_download_profile(download_dir='~/Downloads'):
    """
    Get a firefox profile that automatically downloads NEXIS text files
    :param download_dir: the download dir, defaults to Downloads
    :return:
    """
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList", 2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)
    fp.set_preference("browser.download.dir", download_dir)
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/plain;charset=ISO-8859-1")
    return fp

def stanford_auth(driver):
    """
    Login to stanford web portal
    :param driver: the Selenium driver to auth
    :return:
    """
    try_until_success('''driver.find_element_by_id("username")''', None)
    username = driver.find_element_by_id("username")
    password = driver.find_element_by_id("password")
    with open('creds.json') as f:
        creds = json.load(f)
    username.send_keys(creds['username'])
    password.send_keys(creds['password'])
    driver.find_element_by_name("_eventId_proceed").click()
    try_until_success('''driver.switch_to.frame(driver.find_element_by_id("duo_iframe"))''', 10)
    try_until_success('''driver.find_element_by_id("passcode").click()''', None)
    try_until_success('''driver.find_element_by_id("message").click()''', None)
    two_fa = input()
    passcode = driver.find_element_by_name("passcode")
    passcode.send_keys(two_fa)
    driver.find_element_by_id("passcode").click()


fp = get_download_profile()
driver = webdriver.Firefox(firefox_profile=fp)

driver.get("https://login.stanford.idm.oclc.org/login?url=https://search-proquest-com.stanford.idm.oclc.org/")
stanford_auth(driver)

driver.refresh()

try_until_success('''driver.find_element_by_id("searchTerm")''', None)

search_bar = driver.find_element_by_id("searchTerm")

search_bar.send_keys("PUBID(105983)")

driver.find_element_by_id("expandedSearch").click()

# set num items per page
itemsPerPage = Select(driver.find_element_by_id("itemsPerPage"))
itemsPerPage.select_by_visible_text('100')
driver.find_element_by_id("gaSelectPerPageSubmit").click()

sleep(5)

driver.find_element_by_id("mlcbAll").click()

driver.find_element_by_id("tsMore").click()

driver.find_element_by_id("saveExportLink_5").click()

driver.find_elements_by_class_name("pull-right")[6].click()
driver.switch_to.window(driver.window_handles[1])
HTML = driver.page_source
while 'Request Complete' not in HTML:
    try:
        HTML = driver.page_source
    except:
        pass


sleep(1)
driver.close()

driver.switch_to.window(driver.window_handles[0])




























