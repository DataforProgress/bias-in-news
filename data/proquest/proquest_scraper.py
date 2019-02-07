from selenium import webdriver
from selenium.webdriver.support.select import Select
from time import sleep
from math import ceil
import json
import sys
import re
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

def get_dates_intervals(start_date, end_date, interval):
    """
    Get a list of tuples of dates from start to end, first index is start of date interval, second is end of date
    interval
    :param start_date: date obj start, e.g. date(2017, 8, 22)
    :param end_date: date obj end e.g. date(2017, 8, 22)
    :param interval: number of days in each interval
    :return: list of tuples of dates from start to end, first index is start of date interval, second is end of
             date interval
    """
    delta = end_date - start_date  # timedelta
    dates = []
    for i in range(int(delta.days / interval)):
        dates.append((datetime.strftime(start_date + timedelta(i * interval), '%Y%m%d'),
                      datetime.strftime(start_date + timedelta(i * interval + interval - 1), '%Y%m%d')))
    return dates


total, curr = 1, 0
d1 = date(2015, 1, 1)  # start date
d2 = date(2018, 5, 1)  # end date
dates = get_dates_intervals(d1, d2, 45)
print(dates)

fp = get_download_profile()
driver = webdriver.Firefox(firefox_profile=fp)


driver.get("https://login.stanford.idm.oclc.org/login?url=https://search-proquest-com.stanford.idm.oclc.org/")
stanford_auth(driver)

driver.refresh()

try_until_success('''driver.find_element_by_id("searchTerm")''', None)


def search_source(start_date, end_date):
    try_until_success('''driver.find_element_by_id("searchTerm")''', None)
    search_bar = driver.find_element_by_id("searchTerm")
    search_bar.clear()
    search_bar.send_keys("PUBID(105983) AND PD(>{0}) AND PD(<{1})".format(start_date, end_date))
    driver.find_element_by_id("expandedSearch").click()


def set_items_per_page():
    try_until_success('''driver.find_element_by_id("itemsPerPage")''', None)
    itemsPerPage = Select(driver.find_element_by_id("itemsPerPage"))
    itemsPerPage.select_by_visible_text('100')

for date in dates:
    try_until_success('''driver.find_element_by_class_name("pq-logo").click()''', None)
    start_page = 0
    page = 0
    print(date)
    search_source(date[0], date[1])
    set_items_per_page()
    try_until_success('''driver.find_element_by_id("mlcbAll").click()''', None)
    while curr < total:
        for _ in range(8):
            try_until_success('''driver.find_element_by_id("eventlink")''', None)
            total = int(driver.find_element_by_id("eventlink").text.split(" ")[0].replace(',', ''))
            curr = int(driver.find_element_by_class_name("selectItems").text.split("-")[-1].replace(',', ''))
            print(curr, total)
            if curr >= total:
                break
            print(start_page)
            try_until_success('''driver.find_element_by_link_text("Next page").click()''', None)
            sleep(2)
            try_until_success('''driver.find_element_by_id("mlcbAll").click()''', None)
            sleep(2)
            page += 1
        try_until_success('''driver.find_element_by_id("tsMore").click()''', None)
        driver.find_element_by_id("saveExportLink_5").click()
        try_until_success('''driver.find_element_by_name("deselectCheckBox").click()''', None)
        driver.find_elements_by_class_name("pull-right")[6].click()
        driver.switch_to.window(driver.window_handles[1])
        HTML = driver.page_source
        skip = False
        while 'Request complete' not in HTML and "Session Ended" not in HTML:
            try:
                HTML = driver.page_source
            except:
                pass
        sleep(2)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        if "Session Ended" in HTML:
            try_until_success('''driver.find_element_by_class_name("pq-logo").click()''', None)
            search_source(date[0], date[1])
            set_items_per_page()
            url = driver.current_url
            url = url.replace('/1?', '/{0}?'.format(start_page))
            driver.get(url)
            page = start_page
            continue
        start_page = page
        sleep(1)

