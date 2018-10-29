import os
import sys
import argparse
import ConfigParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

# don't print exception stack trace
sys.tracebacklimit = 0

class EC_OR:
   def __init__(self, *args):
      self.ecs = args

   def __call__(self, driver):
      for ec in self.ecs:
         try:
            if ec(driver): return True
         except:
            pass

CONFIG_FILE_NAME=os.getenv("HOME") + "/" + ".mfakeysrc"

def read_config(section, key):
   config = ConfigParser.ConfigParser()
   config.read(CONFIG_FILE_NAME)
   return config.get(section, key)

def get_arg(argsd, name, required):
   arg = argsd[name]
   if arg != "":
      return arg
   try:
      return read_config("default", name)
   except:
      if required:
         raise Exception("argument '" + name + "' is required")
      else:
         return ""

def base_dir():
   try:
      # under PyInstaler
      return sys._MEIPASS
   except:
      return os.getcwd()

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="AWS MFA Keys Fetcher")
   parser.add_argument("-u", "--username",
                       help="User name. Read from '" + CONFIG_FILE_NAME + "' if not provided",
                       default="")
   parser.add_argument("-p", "--password",
                       help="Password. Read from '" + CONFIG_FILE_NAME + "' if not provided",
                       default="")
   parser.add_argument("-c", "--code",
                       help="MFA Code", required=True)
   parser.add_argument("-a", "--account",
                       help="Account ID. List accounts if not provided",
                       default="")
   parser.add_argument("--url",
                       help="Auth URL. Read from '" + CONFIG_FILE_NAME + "' if not provided",
                       default="")
   parser.add_argument("--debug",
                       help="Show browser for debugging",
                       action="store_true")
   args = parser.parse_args()
   argsd = vars(args)

   base_dir = base_dir()
   debug = args.debug
   code = args.code

   username = get_arg(argsd, "username", True)
   password = get_arg(argsd, "password", True)
   account = get_arg(argsd, "account", False)
   url = get_arg(argsd, "url", True)

   if debug:
      print("Username: " + username)
      print("Password: " + password)
      print("Code: " + code)
      print("Account: " + account)
      print("Url: " + url)
      print("Dir: " + base_dir)

   # if ID is not given the just accounts
   list_accounts = False
   if account == None or account == "":
      list_accounts = True

   chrome_options = webdriver.ChromeOptions()
   if not debug:
      chrome_options.add_argument("--headless")
   chrome_options.add_argument("--disable-gpu")
   driver = webdriver.Chrome(
      executable_path=os.path.join(base_dir, "bin/chromedriver"),
      chrome_options=chrome_options
   )
   try:
      driver.get(url)
      WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "wdc_login_button"))
      )
      driver.find_element_by_id("wdc_username").send_keys(username)
      driver.find_element_by_id("wdc_password").send_keys(password)
      driver.find_element_by_id("wdc_mfa").send_keys(code)
      # auth and wait
      driver.find_element_by_id("wdc_login_button").click()
      WebDriverWait(driver, 60).until(EC_OR(
         EC.visibility_of_element_located((By.XPATH, "//*[@id='alertFrame']/div")),
         EC.element_to_be_clickable((By.XPATH, "//portal-application"))
      ))
      try:
         driver.find_element_by_xpath("//*[@id='alertFrame']/div")
         raise Exception("Authentication Failed")
      except NoSuchElementException:
         # if alertFrame is not found then auth is successful, go to the next page
         pass

      if list_accounts:
         print(driver.find_element_by_xpath("//portal-application").text + ":")

      driver.find_element_by_xpath("//portal-application").click()
      accounts_raw = driver.find_element_by_xpath("//portal-instance-list").text

      if not list_accounts and accounts_raw.find(account) == -1:
         raise Exception("Account ID not found")

      accounts = accounts_raw.split("\n")
      for i in xrange(len(accounts)):
         if list_accounts:
            print(accounts[i])

         if not list_accounts and accounts[i].find(account) != -1:
            instance = driver.find_elements_by_tag_name("portal-instance")[i]
            instance.click()
            driver.implicitly_wait(1)
            instance.find_element_by_id("temp-credentials-button").click()
            WebDriverWait(driver, 30).until(
               EC.element_to_be_clickable((By.ID, "env-var-linux"))
            )
            print(driver.find_element_by_id("env-var-linux").text)

   except TimeoutException:
      print("Timeout")
   except Exception as e:
      print("Exception: " + str(e))
   finally:
      if not debug:
         driver.quit()
