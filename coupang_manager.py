import os
import shutil
import json
import sys
import time

import requests as requests
from selenium import webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from fake_useragent import UserAgent


class CoupangManager():
    def __init__(self):
        self.driver = None

    def open_chrome(self):
        try:
            shutil.rmtree(r'C:\chrometemp')
        except Exception as e:
            pass

        # subprocess.Popen(
        #     r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"')
        #
        user_ag = UserAgent().random
        #
        options = webdriver.ChromeOptions()

        with open("config.json", "r", encoding='utf-8') as st_json:
            json_data = json.load(st_json)

        background = json_data['background']

        if 'y' in background.lower():
            options.add_argument('headless')

        options.add_argument('window-size=1910x1080')
        options.add_argument('lang=ko_KR')
        options.add_argument('user-agent=%s' % user_ag)
        # options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        if not self.driver:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)

        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) """})

        self.driver.implicitly_wait(3)

    def log_in(self, coupang_id, coupang_pwd):
        print('Logging in...')

        self.open_chrome()

        try:
            self.driver.get(url='https://login.coupang.com/login/login.pang')

            time.sleep(1)

            if 'Access Denied' in self.driver.title:
                print('쿠팡 엑세스 거부로 인해 IP 바꾸고 재시도합니다...')
                self.close()
                return -1

            self.wait_until_clickable(10, "//input[@id='login-email-input']")
            time.sleep(1)

            self.send_key("//input[@id='login-email-input']", coupang_id)
            self.send_key("//input[@id='login-password-input']", coupang_pwd + Keys.ENTER)

            self.wait_until_clickable(10, "//button[@class='pincode-content__button pincode-select__button']")
            self.click("//button[@class='pincode-content__button pincode-select__button']")

            with open("config.json", "r", encoding='utf-8') as st_json:
                json_data = json.load(st_json)

            sms_api_url = json_data['sms_api_url']
            sms_api_key = json_data['sms_api_key']

            while True:
                time.sleep(5)

                try:
                    response = requests.get(url=sms_api_url, params={'key': sms_api_key})
                    auth_code = response.json()
                    self.send_key("//input[@class='pincode-input__pincode-input-box__pincode']",
                                  auth_code['auth'] + Keys.ENTER)

                    self.wait_until_clickable(10, "//li[@id='logout']")
                    return 0

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(e, fname, exc_tb.tb_lineno)

        except Exception as e:
            try:
                self.wait_until_clickable(10, "//li[@id='logout']")
                return 0
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)
                self.driver.refresh()
                return self.log_in(coupang_id, coupang_pwd)

    def test_product(self, url, mobile_info, quant, pg):
        try:
            self.wait_until_clickable(10, "//li[@id='logout']")

            self.driver.get(url=url)

            self.wait_until_clickable(10, "//button[@class='travel-button travel-button__blue full-width']")
            self.click("//button[@class='travel-button travel-button__blue full-width']")

            self.wait_until_clickable(10, "//span[@class='select-button-text']")
            self.click("//span[@class='select-button-text']")

            self.wait_until_clickable(10, "//span[@class='option-item-text has-price']")
            self.click("//span[@class='option-item-text has-price']")

            self.wait_until_clickable(10, "//button[@class='spinner-plus']")

            for _ in range(1, quant):
                self.click("//button[@class='spinner-plus']")
                self.wait_until_clickable(10, "//button[@class='spinner-plus']")

            self.wait_until_clickable(10, "//button[@class='travel-button travel-button__blue md reservation-button']")
            self.click("//button[@class='travel-button travel-button__blue md reservation-button']")

            self.get_pg_window(mobile_info, pg)

            element = self.driver.find_element(By.XPATH, "//div[@class='infoBox']").find_elements(By.TAG_NAME, "td")
            product_name = element[0].text
            price = element[1].text[:-1]

            self.fill_payment_form(mobile_info, pg)

            time.sleep(3)

            result_text = ''
            if '모빌' in pg:
                while not result_text:
                    try:
                        alert = self.driver.switch_to.alert
                        result_text = alert.text
                        alert.accept()
                    except:
                        if self.driver.find_element(By.XPATH, "//tr[@id='inputApprNo']").is_displayed():
                            result_text = '정상'

            elif '다날' in pg:
                while not result_text:
                    if self.driver.find_element(By.XPATH,
                                                "//td[@id='alerttext']").text and not self.driver.find_element(
                            By.XPATH, "//tr[@id='inputOTP']").is_displayed():
                        result_text = self.driver.find_element(By.XPATH, "//td[@id='alerttext']").text
                    elif not self.driver.find_element(By.XPATH,
                                                      "//td[@id='alerttext']").text and self.driver.find_element(
                            By.XPATH, "//tr[@id='inputOTP']").is_displayed():
                        result_text = '정상'

            elif '빌게이트' in pg:
                while not result_text:
                    if self.driver.find_element(By.XPATH,
                                                "//td[@id='alerttext']").text and not self.driver.find_element(
                            By.XPATH, "//tr[@id='inputOTP']").is_displayed():
                        result_text = self.driver.find_element(By.XPATH, "//td[@id='alerttext']").text
                    elif not self.driver.find_element(By.XPATH,
                                                      "//td[@id='alerttext']").text and self.driver.find_element(
                            By.XPATH, "//tr[@id='inputOTP']").is_displayed():
                        result_text = '정상'

            self.driver.switch_to.default_content()
            self.driver.get(url='https://www.coupang.com/')

            return product_name, price, result_text

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)
            self.driver.get(url='https://www.coupang.com/')
            return self.test_product(url, mobile_info, quant, pg)

    def fill_payment_form(self, mobile_info, pg):
        _, phone_number, id_num1, id_num2 = mobile_info

        _, phone_number2, phone_number3 = phone_number.split('-')

        # 다날, 빌게이트
        if '다날' in pg or '빌게이트' in pg:
            element = self.driver.find_element(By.XPATH, "//input[@id='mobileNum2']")
            element.clear()
            element.click()
            element.send_keys(phone_number2)

            element = self.driver.find_element(By.XPATH, "//input[@id='mobileNum3']")
            element.clear()
            element.click()
            element.send_keys(phone_number3 + id_num1 + id_num2)

            confirm_button = self.driver.find_element(By.XPATH, "//img[@alt='승인번호 요청']")
        # 모빌리언스
        else:
            element = self.driver.find_element(By.XPATH, "//input[@id='phoneNo2']")
            element.clear()
            element.click()
            element.send_keys(phone_number2)

            element = self.driver.find_element(By.XPATH, "//input[@id='phoneNo3']")
            element.clear()
            element.click()
            element.send_keys(phone_number3 + id_num1 + id_num2)

            confirm_button = self.driver.find_element(By.XPATH, "//img[@alt='인증번호 요청']")

        time.sleep(5)
        confirm_button.click()

    def get_pg_window(self, mobile_info, pg):
        target_content = ''
        iframe_content = ''

        # 다날
        if '다날' in pg:
            target_content = '다날'

        # 빌게이트
        elif '빌게이트' in pg:
            target_content = 'billgate'

        # 모빌
        else:
            target_content = 'mobilians'

        while target_content not in iframe_content:
            self.driver.switch_to.default_content()
            self.driver.refresh()
            self.fill_up_order_page(mobile_info)

            self.click("//button[@id='paymentBtn']")

            while True:
                try:
                    self.driver.switch_to.frame("callLGPayment")
                    self.wait_until_clickable(1, "//label[@for='korNum']")

                    iframe_content = self.driver.find_element(By.TAG_NAME, "html").get_attribute('innerHTML')
                    break
                except Exception as e:
                    if 'Message: callLGPayment' in str(e):
                        try:
                            self.click("//button[@id='paymentBtn']")
                        except Exception as e:
                            pass
                    pass

    def fill_up_order_page(self, mobile_info):
        self.wait_until_clickable(10, "//input[@value='PHONE']")
        self.click("//input[@value='PHONE']")

        target_carrier = mobile_info[0].lower()

        if 's' in target_carrier:
            self.click("//select[@name='cellphoneTelecom']/option[text()='SKT']")
        else:
            self.click("//select[@name='cellphoneTelecom']/option[text()='KT']")

    def wait_until_clickable(self, wait_time, xpath):
        WebDriverWait(self.driver, wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))

    def send_key(self, xpath, keys):
        self.driver.find_element(By.XPATH, xpath).send_keys(keys)

    def click(self, xpath):
        self.driver.find_element(By.XPATH, xpath).click()

    def close(self):
        self.driver.close()
        self.driver = None
