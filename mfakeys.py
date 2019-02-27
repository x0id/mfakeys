from __future__ import print_function

import os
import sys
import argparse
import getpass
import ConfigParser
import rncryptor
import base64
import subprocess
import re

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

def base_dir():
   try:
      # under PyInstaler
      return sys._MEIPASS
   except:
      return os.getcwd()

def eprint(*args, **kwargs):
   """ Print to standard error """
   print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":

   parser = argparse.ArgumentParser(description="AWS MFA Keys Fetcher")
   parser.add_argument("-i", "--stdin",
                       help="read secret from stdin",
                       action="store_true")
   parser.add_argument("-t", "--token",
                       help="get mfa token",
                       action="store_true")
   parser.add_argument("-e", "--encrypt",
                       help="encrypt user password or pin",
                       action="store_true")
   parser.add_argument("-p", "--profile",
                       help="configuration profile",
                       default="")
   parser.add_argument("-a", "--account",
                       help="account id, list accounts if not provided",
                       default="")

   args = parser.parse_args()
   argsd = vars(args)

   config = ConfigParser.ConfigParser()
   config.read(CONFIG_FILE_NAME)

   base_dir = base_dir()

   section = argsd["profile"]
   if section == "":
      section = config.get("default", "profile")

   if args.stdin:
      secret = sys.stdin.readline().rstrip()
   else:
      secret = getpass.getpass("secret: ")

   if args.encrypt:
      text = getpass.getpass("text to encrypt: ")
      text = rncryptor.encrypt(text, secret)
      text = base64.b64encode(text)
      print(text)
      sys.exit(0)

   pin = config.get(section, "pin")
   pin = base64.b64decode(pin)
   pin = rncryptor.decrypt(pin, secret)

   token, _ = subprocess.Popen(['stoken', '--stdin'],
      stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate(pin)
   token = token.rstrip()

   if args.token:
      print(token)
      sys.exit(0)

   username = config.get(section, "username")
   password = config.get(section, "password")
   url = config.get(section, "url")

   account = argsd["account"]

   password = base64.b64decode(password)
   password = rncryptor.decrypt(password, secret)

   # if ID is not given the just accounts
   list_accounts = False
   if account == None or account == "":
      list_accounts = True

   chrome_options = webdriver.ChromeOptions()
   chrome_options.add_argument("--headless")
   chrome_options.add_argument("--disable-gpu")
   chrome_options.add_argument('--no-sandbox')
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
      driver.find_element_by_id("wdc_login_button").click()
      # proceed to the next form
      WebDriverWait(driver, 5).until(
         EC.visibility_of_element_located((By.ID, "wdc_mfacode"))
      )
      driver.find_element_by_id("wdc_mfacode").send_keys(token)
      driver.find_element_by_id("wdc_login_button").click()
      # auth and wait
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
            text = driver.find_element_by_id("env-var-linux").text
            print(re.sub(r"\nClick.*\n*", "", text, re.M).replace('"', ''))

   except TimeoutException:
      eprint("Error: Timeout")
   except Exception as e:
      eprint("Error: " + str(e))
   finally:
      driver.quit()
