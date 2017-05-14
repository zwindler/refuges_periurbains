#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import getopt
import ConfigParser

import dryscrape

from datetime import datetime
import re

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

do_send_mail=False

def check_refuge_availability(session):
  available_dates = []
  #Get all dates that aren't marked as "unselectable"
  for date_available in session.xpath("//td[not(contains(@class, 'datepick-unselectable'))]"):
    candidate_classes = date_available['class']
    candidate_cal4date = re.search('cal4date-\d*-\d*-\d*', candidate_classes)
    candidate_clean_date = datetime.strptime(candidate_cal4date.group(), 'cal4date-%m-%d-%Y')
    available_dates.append(candidate_clean_date.strftime('%d-%m-%Y'))
  return(available_dates)

def scrap_single_url(refuge):
  global do_send_mail
  available_dates = []
  if refuge["interested"]:
    refuge['name'] = "<b><u>"+refuge['name']+"</u></b>"
  availability = "    <h3>"+refuge['name']+"</h3>\n    <ul>\n"
  session = dryscrape.Session()
  session.visit(refuge['url'])

  #Get current month availability
  available_dates.extend(check_refuge_availability(session))

  #Check next month  
  datepicknext = session.at_xpath('//*[@class="datepick-next"]/a')
  datepicknext.click()

  #Get next month availability
  available_dates.extend(check_refuge_availability(session))

  #Do we need to send mail ?
  if available_dates.extend != [] and refuge["interested"]:
    do_send_mail=True
  if available_dates == []:
    available_dates.extend(["Plus de dates disponibles"])
  #Write available dates in HTML
  for available_date in available_dates:
    availability+="      <li>"+available_date+"</li>\n"
  return(availability+"    </ul>")

def send_mail(message_body, gmail_config):
  [gmail_from_addr, gmail_to_addr, gmail_password] = gmail_config
  email = MIMEMultipart('alternative')
  email['Subject'] = "Des refuges périurbains sont disponibles!"
  email['From'] = gmail_from_addr
  email['To'] = gmail_to_addr

  #part1 = MIMEText(message_body, 'plain')
  part2 = MIMEText(message_body, 'html')
  #email.attach(part1)
  email.attach(part2)

  smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
  smtp_conn.starttls()
  smtp_conn.login(gmail_from_addr, gmail_password)
  smtp_conn.sendmail(gmail_from_addr, gmail_to_addr, email.as_string())
  smtp_conn.quit()

def main():
  website =  [{ "name" : "Le Tronc Creux", "url" : "http://lesrefuges.bordeaux-metropole.fr/le-tronc-creux/", "interested" : True },
              { "name" : "Le Hamac", "url" : "http://lesrefuges.bordeaux-metropole.fr/le-hamac/", "interested" : True },
              { "name" : "Les Guetteurs", "url" : "http://lesrefuges.bordeaux-metropole.fr/les-guetteurs/", "interested" : True },
              { "name" : "La Belle Etoile", "url" : "http://lesrefuges.bordeaux-metropole.fr/la-belle-etoile/", "interested" : False },
              { "name" : "Le Nuage",  "url" : "http://lesrefuges.bordeaux-metropole.fr/le-nuage/", "interested" : False },
              { "name" : "La Nuit Americaine", "url" : "http://lesrefuges.bordeaux-metropole.fr/la-nuit-americaine/", "interested" : False },
              { "name" : "Le Prisme", "url" : "http://lesrefuges.bordeaux-metropole.fr/le-prisme/", "interested" : True }, 
              { "name" : "Le Vouivre", "url" : "http://lesrefuges.bordeaux-metropole.fr/la-vouivre/", "interested" : False }]
  
  config_file_path = 'scraper.cfg'

  try:
    opts, args = getopt.getopt(sys.argv[1:], 'c:h', ['config=', 'help'])
  except getopt.GetoptError:
    usage()
    sys.exit(2)

  for o, a in opts:
    if o in ('-c', '--config'):
      config_file_path = a
    if o in ('-h', '--help'):
      usage()
      sys.exit()

  config = ConfigParser.RawConfigParser()
  config.read(config_file_path)
  gmail = [config.get('Gmail', 'gmail_from_addr'), config.get('Gmail', 'gmail_to_addr'), config.get('Gmail', 'gmail_password')]

  message = "<html>\n  <head></head>\n  <body>\n    <h2>Disponibilité des refuges périurbains</h2>\n"
  #check if smtp_conn X is available; use xvfb instead
  if 'linux' in sys.platform:
    dryscrape.start_xvfb()
  for refuge in website:
    message += scrap_single_url(refuge)+"\n"
  message += "  </body>\n</html>"
  if do_send_mail:
    print "interested, mail had been sent\n"
    send_mail(message, gmail)
    print "#####\n"
  print message

if __name__ == '__main__':
  main()