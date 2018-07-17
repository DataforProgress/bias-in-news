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
        dates.append((datetime.strftime(start_date + timedelta(i * interval), '%m/%d/%y'),
                      datetime.strftime(start_date + timedelta(i * interval + interval - 1), '%m/%d/%y')))
    return dates

def get_nexis_source_between(driver, start_date, end_date, days_per_search, source_id, source_name):
    dates = get_dates_intervals(start_date, end_date, days_per_search)
    driver.get("https://login.stanford.idm.oclc.org/login?url=http://www.lexisnexis.com/hottopics/lnacademic/")
    stanford_auth(driver)
    sleep(5)
    for date in dates:
        driver.refresh()
        try_until_success('''driver.switch_to_default_content()''', None)
        try_until_success('''driver.switch_to.frame("mainFrame")''', None)
        try_until_success('''driver.find_element_by_id("lblAdvancDwn").click()''', None)
        sleep(1)
        driver.execute_script("SelectOptionAdv('%s','%s','')" % (source_id, source_name))
        driver.execute_script('''GetSourcesSelected()''')
        driver.execute_script('''hideASMAdv();''')
        txtFrmDate = driver.find_element_by_id("txtFrmDate")
        txtFrmDate.send_keys(date[0])
        txtToDate = driver.find_element_by_id("txtToDate")
        txtToDate.send_keys(date[1])
        try_until_success('''driver.find_element_by_id("OkButt").click()''', None)
        try:
            try_until_success('''driver.find_element_by_id("srchButt").click()''', None)
        except:
            try_until_success('''driver.find_element_by_id("OkButt").click()''', None)
            try_until_success('''driver.find_element_by_id("srchButt").click()''', None)
        found = True
        while found:
            try_until_success('''driver.switch_to_default_content()''', None)
            try_until_success('''driver.switch_to.frame("mainFrame")''', None)
            ids = driver.find_elements_by_xpath('//*[@id]')
            temp = "~"
            for ii in ids:
                if '~' in ii.get_attribute('id'):
                    temp += ii.get_attribute('id').split('~')[-1]
            try:
                driver.switch_to.frame("fr_resultsNav" + temp)
                found = False
            except:
                found = True
        try_until_success('''driver.find_element_by_class_name("paginationalign")''', None)
        pagination = driver.find_element_by_class_name("paginationalign")
        results = int(pagination.get_attribute('innerHTML').split("<strong>")[-1].replace("</strong>",""))
        driver.switch_to_default_content()
        driver.switch_to.frame("mainFrame")
        for i in range(int(ceil(results / 500.0))):
            try_until_success('''driver.execute_script("openDeliveryWindow(this, 'delivery_DnldRender');")''', None)
            driver.switch_to.window(driver.window_handles[1])
            try_until_success('''driver.find_element_by_id("delFmt")''', None)
            try_until_success('''driver.find_element_by_id("delView")''', None)
            delFmt = Select(driver.find_element_by_id("delFmt"))
            delFmt.select_by_visible_text('Text')
            delView = Select(driver.find_element_by_id("delView"))
            delView.select_by_visible_text('Full w/ Indexing')
            sleep(1)
            rangetextbox = driver.find_element_by_id("rangetextbox")
            driver.execute_script('''subCheckRangeOptionsStatus('sel', 'delivery_DnldForm', 'false');''')
            rng_start = i * 500 + 1
            rng_end = i * 500 + 500 if i * 500 + 500 < results else results
            rangetextbox.send_keys("%d-%d" % (rng_start, rng_end))
            driver.execute_script('''subCheckRangeOptionsStatus('sel', 'delivery_DnldForm', 'false');''')
            rangetextbox.click()
            try_until_success('''driver.find_element_by_id("img_orig_top").click()''', None)
            try:
                try_until_success('''driver.find_element_by_class_name("suspendbox")''', 200)
            except:
                rangetextbox.click()
                try_until_success('''driver.find_element_by_id("img_orig_top").click()''', None)
                try_until_success('''driver.find_element_by_class_name("suspendbox")''', None, sleep_time=1)
            try_until_success('''driver.page_source''', None)
            HTML = driver.page_source
            while 'Ready to Download' not in HTML:
                try:
                    driver.switch_to_default_content()
                    HTML = driver.page_source
                except:
                    pass
            driver.find_element_by_class_name("suspendbox").click()
            sleep(1)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        driver.back()


fp = get_download_profile()
driver = webdriver.Firefox(firefox_profile=fp)
d1 = date(2017, 11, 23)  # start date
d2 = date(2018, 7, 11)  # end date
# number of days per NEXIS search. Ideally this is as large as possible without the possiblility of exceeding 3000
# results as after 3000 NEXIS refuses to display more than 1000 results, this is irritating but unavoidable
n = 7
source_id = '265544'
source_name = 'Washingtonpost.com'
get_nexis_source_between(driver, d1, d2, n, source_id, source_name)
