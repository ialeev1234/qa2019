from datetime import datetime

import psycopg2
import pytz as pytz
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from sshtunnel import SSHTunnelForwarder

SSH_HOST = '146.185.143.168'
SSH_PORT = 22
SSH_USER = 'root'
SSH_PASSWORD = 'testQA2019'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_USER = 'mantisbt'
DB_NAME = 'mantisbt'
DB_PASSWORD = 'mantisbt2019'
URL = 'http://146.185.143.168'
USER = 'administrator'
PASSWORD = 'mantisbt2019'
PATH = '/manage_user_page.php'


class TestMantis:
    data = None

    def setup(self):
        print('\n\n\n      Preparing before test:')
        with SSHTunnelForwarder(
                (SSH_HOST, SSH_PORT),
                ssh_username=SSH_USER,
                ssh_password=SSH_PASSWORD,
                remote_bind_address=(DB_HOST, DB_PORT),
                allow_agent=False
        ) as tunnel:
            tunnel.start()
            print('SSH tunnel started!')
            with psycopg2.connect(
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=tunnel.local_bind_port,
                    database=DB_NAME
            ) as connection:
                print('DB connected!')
                cursor = connection.cursor()
                mantis_user_query = "select * from mantis_user_table"
                cursor.execute(mantis_user_query)
                self.data = cursor.fetchall()
                print(f'Fetched {len(self.data)} user(s) from "mantis_user_table"!')

    def test_mantis_user_table(self):
        with Display(visible=0):
            cap = DesiredCapabilities().FIREFOX
            cap["marionette"] = True

            profile = webdriver.FirefoxProfile()
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", "proxy.server.address")
            profile.set_preference("network.proxy.http_port", "port_number")
            profile.update_preferences()

            with webdriver.Firefox(
                capabilities=cap,
                firefox_profile=profile
            ) as driver:
                print('\n      Start test:')
                driver.get(URL)
                username = driver.find_element_by_id('username')
                username.send_keys(USER)
                driver.find_element_by_css_selector('input[type=submit]').click()
                print('Username entered!')
                password = driver.find_element_by_id('password')
                password.send_keys(PASSWORD)
                driver.find_element_by_css_selector('input[type=submit]').click()
                print('Password entered!')
                driver.get(f'{URL}{PATH}')
                users_elements = driver.find_elements_by_css_selector('div.table-responsive tbody tr')
                print('Users received!')
                users_by_username = {}
                for user_tr in users_elements:
                    user_tds = [x.text for x in user_tr.find_elements_by_tag_name('td')]
                    """
                    ', '.join([x.text for x in driver.find_elements_by_css_selector('div.table-responsive thead a')])
                    
                    'Username, Real Name, E-mail, Access Level, Enabled, Protected, Date Created, Last Visit'
                    """
                    users_by_username[user_tds[0]] = user_tds[1:]
                for item in self.data:
                    """
                    select column_name from information_schema.columns where table_name = 'mantis_user_table';
                    
                             column_name         
                    -----------------------------
                     id
                     username
                     realname
                     email
                     password
                     enabled
                     protected
                     access_level
                     login_count
                     lost_password_request_count
                     failed_login_count
                     cookie_string
                     last_visit
                     date_created

                    """
                    if not item[5]:
                        # let's skip disabled users
                        print(f'"{item[1]}" disabled and skipped!')
                        continue
                    print(f'"{item[1]}" is comparing...')
                    username = item[1]
                    assert username in users_by_username
                    user = users_by_username[username]
                    # realname
                    assert item[2] == user[0]
                    # email
                    assert item[3] == user[1]
                    # created date
                    timestamp = item[-1]
                    time_string_utc = datetime \
                        .fromtimestamp(timestamp) \
                        .astimezone(tz=pytz.timezone('utc')) \
                        .strftime('%Y-%m-%d %H:%M')
                    assert time_string_utc == user[-2]
                print('All enabled users matched successfully!')
