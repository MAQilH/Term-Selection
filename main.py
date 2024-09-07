import pip


def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])


import_or_install('Unidecode')
import_or_install('selenium')

import os

from unidecode import unidecode

from selenium import webdriver
from selenium.webdriver.common.by import By

import constant as const


class TermSelect(webdriver.Chrome):
    def __init__(self, teardown=False):
        self.teardown = teardown
        os.environ['PATH'] += const.DRIVER_PATH
        super(TermSelect, self).__init__()
        self.implicitly_wait(60)
        self.maximize_window()
        self.get(const.BASE_URL)

    def start(self):
        if self.check_is_login_page():
            self.login()
        self.select_lessons()

    def check_is_login_page(self):
        return str(self.current_url) == const.BASE_URL

    def login(self):
        username = self.find_element(By.NAME, 'username')
        password = self.find_element(By.NAME, 'password')
        security_code = self.find_element(By.NAME, 'securityCode')

        username.send_keys(const.STUDENT_ID)
        password.send_keys(const.PASSWORD)
        security_code.send_keys(self.get_security_code())

        submit_button = self.find_element(By.CSS_SELECTOR, 'button[class="ui large fluid primary button"]')
        submit_button.click()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()

    def get_sorted_path(self):
        svg = self.find_element(By.CSS_SELECTOR, 'svg[viewBox="0,0,150,50"]')
        paths = svg.find_elements(By.TAG_NAME, 'path')
        sorted_path = list()
        for path in paths:
            d = path.get_attribute('d')
            if len(d) < 100:
                continue
            split_d = d.split()
            sorted_path.append((float(split_d[0][1:]), d))
        sorted_path.sort()
        return sorted_path

    def get_security_code(self):
        sorted_path = self.get_sorted_path()
        security_code = ''
        for pos, path in enumerate(sorted_path):
            near_digit = (100000000000, -1)
            for digit in range(10):
                with open(f'CAPTCHA-STORE/pos-{pos}/{digit}.txt', 'r') as file:
                    dist = 0
                    cnt = 0
                    while True:
                        digit_d_content = file.readline().strip()
                        if not digit_d_content:
                            break
                        cnt += 1
                        dist += (len(digit_d_content) - len(path[1].strip())) ** 2
                    dist /= cnt
                    if dist < near_digit[0]:
                        near_digit = (dist, digit)
            security_code += str(near_digit[1])
        return security_code

    def train(self):
        while True:
            correct_code = input().strip()
            if correct_code == 'exit':
                break
            self.train_correct_code(correct_code)
            refresh_button = self.find_element(By.CSS_SELECTOR, 'a[role="button"]')
            refresh_button.click()

    def train_correct_code(self, correct_code):
        sorted_path = self.get_sorted_path()
        for pos, digit in enumerate(correct_code):
            with open(f'CAPTCHA-STORE/pos-{pos}/{digit}.txt', 'a') as file:
                file.write(sorted_path[pos][1])
                file.write('\n')

    def select_lessons(self):
        self.goto_stared_page()

        table = self.find_element(By.CSS_SELECTOR, 'table[class="ui small selectable very basic compact table"]')
        table_body = table.find_element(By.TAG_NAME, 'tbody')
        lessons = table_body.find_elements(By.TAG_NAME, 'tr')
        remaining_capacities = self.get_remaining_capacities(lessons)

        for _, lesson_pos in remaining_capacities:
            lesson_row = lessons[lesson_pos]

            add_button = lesson_row.find_element(By.CSS_SELECTOR, 'button[class="ui mini basic circular icon button"]')
            add_button.click()

            action_box = self.find_element(By.CSS_SELECTOR, 'div[class="actions"]')
            close_button = action_box.find_elements(By.TAG_NAME, 'button')[0]
            register_button = action_box.find_elements(By.TAG_NAME, 'button')[1]

            register_button.click()

            try:
                close_button.click()
            except Exception as e:
                print(e)

            # wait = WebDriverWait(self, timeout=10, poll_frequency=0.5)
            # print(len(self.find_elements(By.CSS_SELECTOR, 'div[class="ui tiny modal transition visible active"]')))
            # wait.until(lambda d : len(self.find_elements(By.CSS_SELECTOR, 'div[class="ui tiny modal transition visible active"]')) == 0)
            # print('end')

    def get_remaining_capacities(self, lessons):
        remaining_capacity = list()
        for pos, lesson in enumerate(lessons):
            capacity_container = lesson.find_element(By.CSS_SELECTOR,
                                                     'td[class="center aligned middle aligned one wide"]')
            capacity_text = capacity_container.find_element(By.TAG_NAME, 'span').text
            filled_number = int(unidecode(capacity_text.split()[0]))
            capacity = int(unidecode(capacity_text.split()[2]))
            remaining_capacity.append((capacity - filled_number, pos))
        remaining_capacity.sort()
        return remaining_capacity

    def goto_stared_page(self):
        stared_button = self.find_element(By.CSS_SELECTOR, 'a[href="/courses/marked"]')
        stared_button.click()


with TermSelect() as term:
    term.start()
    # term.train()