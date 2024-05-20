#!/usr/bin/python3
#
# Scan base directory to find certificates with extension likes pem, cer, crt
# Extract a certificate information and put in a dictionary
# Calculate how many days are remaining
# Print out the details based on the days remaining
# 

import os
import re
import sys
import subprocess
import time
from datetime import datetime

def get_subject(my_cert):
  proc = subprocess.Popen([openssl,  'x509', '-in', my_cert, '-noout', '-subject'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  output,error = proc.communicate()

  if output != '':
    subject = output
  elif error != '':
    print("Error:\n%s"  % error)


  subject = subject.decode('utf-8')
  subject = subject.split('ubject=')[-1]
  subject = subject.strip()

  return (subject)

def get_end_date(my_cert):
  proc = subprocess.Popen([openssl,  'x509', '-in', my_cert, '-noout', '-enddate'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  output,error = proc.communicate()

  if output != '':
    end_date = output
  elif error != '':
    print("Error:\n%s"  % error)

  end_date = end_date.decode('utf-8')
  end_date = end_date.split('notAfter=')[-1]
  end_date = end_date.strip()

  return (end_date)

def get_finger_256(my_cert):
  proc = subprocess.Popen([openssl,  'x509', '-in', my_cert, '-noout', '-sha256', '-fingerprint'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  output,error = proc.communicate()

  if output != '':
    sha256_thumb = output
  elif error != '':
    print("Error:\n%s"  % error)

  sha256_thumb =  sha256_thumb.decode('utf-8')
  sha256_thumb =  sha256_thumb.split('=')[-1]
  sha256_thumb =  sha256_thumb.strip()
  return (sha256_thumb)

def get_serial(my_cert):
  proc = subprocess.Popen([openssl,  'x509', '-in', my_cert, '-noout', '-serial' ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  output,error = proc.communicate()

  if output != '':
    serial = output
  elif error != '':
    print("Error:\n%s"  % error)

  serial = serial.decode('utf-8')
  serial = serial.split('=')[-1]
  serial = serial.strip()

  return (serial)

def get_key_usage(my_cert):
  proc = subprocess.Popen([openssl,  'x509', '-in', my_cert, '-noout', '-ext' ,'extendedKeyUsage' ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  output,error = proc.communicate()

  if output != '':
    KeyUsage = output
  elif error != '':
    print("Error:\n%s"  % error)

  KeyUsage = KeyUsage.decode('utf-8')
  KeyUsage = KeyUsage.split('X509v3 Extended Key Usage: \n    ')[-1]
  KeyUsage = KeyUsage.strip()

  return (KeyUsage)

def get_sans(my_cert):
  output = subprocess.run([openssl,  'x509', '-in', my_cert, '-noout', '-text'], check=True, capture_output=True, text=True).stdout
  #print(output)

  sans = re.findall('DNS:(.+)', output)
  return (sans)


def get_cert_details(my_cert):
  ## Get the certificate popperties by calling the approriate methods
  subject      = get_subject(my_cert)
  enddate      = get_end_date(my_cert)
  sha256_thumb = get_finger_256(my_cert)
  serial       = get_serial(my_cert)
  key_usage    = get_key_usage(my_cert)
  sans         = get_sans(my_cert)

  days_remaining = calculate_days_remaining(enddate)

  if days_remaining >= 90:
    status = 'ok'
  elif (days_remaining >= 30) and (days_remaining <= 90):
    status = 'warning'
  elif (days_remaining <= 30) and  (days_remaining > 0):
    status = 'critical'
  elif (days_remaining < 0) and (days_remaining <= -200):
    status = 'catastropic'

  my_cert_dict = {}
  my_cert_dict['filename']       = my_cert
  my_cert_dict['subject']        = subject
  my_cert_dict['thumbprint']     = sha256_thumb
  my_cert_dict['serial']         = serial
  my_cert_dict['sans']           = sans
  my_cert_dict['key_usage']      = key_usage
  my_cert_dict['end_date']       = enddate
  my_cert_dict['days_remaining'] = days_remaining
  my_cert_dict['status']         = status

  return(my_cert_dict)

def calculate_days_remaining(date_string):

  ## Jul 29 14:53:08 2024 GMT
  try:
      date_obj = datetime.strptime(date_string, "%b %d %H:%M:%S %Y %Z")
  except ValueError:
    pass

  time_tup = date_obj.timetuple()
  epoch_timestamp = time.mktime(time_tup)

  epoch_time_now = time.time()
  days_remaining = int(epoch_timestamp) - int(epoch_time_now)

  days_remaining = days_remaining / 86400

  return (days_remaining)

def build_webpage(my_dict):
  ## build the website to display the results
  count = 1
  ## build the website
  f = open("cert_status.html", 'w')

  f.write("<!DOCTYPE html>\n")
  f.write("<html>\n")
  f.write("  <head>\n")
  #f.write('<link rel="stylesheet" href="certs_styles.css">'
  f.write("  <style>\n")
  f.write("    table, th, td {\n")
  f.write("      border: 1px solid;\n")
  f.write("    }\n")
  f.write("    table {\n")
  f.write("      width: 90%;\n")
  f.write("      border-collapse: collapse;\n")
  f.write("    }\n")
  f.write("    tr:hover {\n")
  f.write("      background-color: lightblue;\n")
  f.write("    }\n")
  f.write("    .ok {\n")
  f.write("      background-color: #00cc66;\n")
  f.write("    }\n")
  f.write("    .critical {\n")
  f.write("      background-color: #FD2D00;\n")
  f.write("    }\n")
  f.write("    .warning {\n")
  f.write("      background-color: #FFBB00;\n")
  f.write("    }\n")
  f.write("    .catastropic {\n")
  f.write("      background-color: #9300FF;\n")
  f.write("    }\n")
  f.write("  </style>\n")
  f.write("</head>\n")
  f.write("<body>\n")
  f.write("  <h1>Certificate HTML - Produced: %s</h1>\n" % datetime.now())
  f.write("  <p>Use the website to determine which certificates are due to expire</p><br>\n")
  f.write("  <table>\n")
  f.write("    <colgroup>\n")
  f.write("      <col span=\"1\" style=\"width: 2%;\">   <!-- ID -->\n")
  f.write("      <col span=\"1\" style=\"width: 15%;\">  <!--Filename -->\n")
  f.write("	     <col span=\"1\" style=\"width: 25%;\">  <!--Subject -->\n")
  f.write("   	 <col span=\"1\" style=\"width: 2%;\">   <!-- Days Remaining -->\n")
  f.write("	     <col span=\"1\" style=\"width: 5%;\">   <!-- end date -->\n")
  f.write("	     <col span=\"1\" style=\"width: 14%;\">  <!--Thumbprint -->\n")
  f.write("	     <col span=\"1\" style=\"width: 17%;\">  <!-- Sans -->\n")
  f.write("     </colgroup>\n")
  f.write("   <tbody>\n")
  f.write("   <tr>\n")
  f.write("     <!-- Headers for the Table --> \n")
  f.write("     <th>ID</th>\n")
  f.write("     <th>Filename</th>\n")
  f.write("     <th>Subject</th>\n")
  f.write("     <th>Days Remaining</th>\n")
  f.write("     <th>End Date</th>\n")
  f.write("     <th>Thumbprint SHA256</th>\n")
  f.write("     <th>SANS</th>\n")
  f.write("   </tr>\n")

  for key, values in cert_dict.items():
    status = values['status']
    f.write("   <tr>\n")
    f.write("     <td class=\"%s\">%s</td>\n" % (status, count))
    f.write("     <td class=\"%s\">%s</td>\n" % (status, values['filename']))
    f.write("     <td class=\"%s\">%s</td>\n" % (status, values['subject']))
    f.write("     <td class=\"%s\">%s</td>\n" % (status, int(values['days_remaining'])))
    f.write("     <td class=\"%s\">%s</td>\n" % (status, values['end_date']))
    f.write("     <td class=\"%s\">%s</td>\n" % (status, values['thumbprint']))
    try:
      sans = values['sans'][0]
      sans = sans.split(',')
      f.write("     <td class=\"%s\">\n" % status)
      f.write("       <ol>\n")
      for san in sans:
        f.write("         <li>%s</li>\n" % san.replace('DNS:', ''))
      f.write("       </ol>\n")
      f.write("     </td>\n")
      f.write("   </tr>\n")
    except IndexError:
      f.write("     <td class=\"%s\"></td>\n" % status)
      f.write("   </tr>\n")
    count+= 1
  f.write("    </tbody>\n")
  f.write("  </table>\n")
  f.write("</body>\n")
  f.write("</html>\n")
  f.close()

  return  
# ------ Main ------ #

openssl = '/usr/bin/openssl'
base_dir = '/home/nigel/certs'

file_types = [ '.pem','.crt', '.cer']

cert_dict = {}

## Get a list of the dirctories to search
for (root,dirs,files) in os.walk(base_dir, topdown=True):
  for my_file in files:
    name, extension = os.path.splitext(my_file)
    ## Check the file names agains the file anem extnsions
    if extension.lower() in file_types:
      file_path ="%s/%s" % (root,my_file)
      ## loop through and get the certificate details
      tmp_dict = {}
      tmp_dict = get_cert_details(file_path)
      days_remaining = tmp_dict['days_remaining']
      if cert_dict.get(days_remaining):
        old_data = cert_dict[days_remaining]
      else:
        cert_dict[days_remaining] = tmp_dict
      del tmp_dict

#for k,v in  cert_dict.items():
#  if isinstance(v, dict):
#    for vv in v.items():
#      print("%s   %s" % (k, vv))

for key, values in cert_dict.items():
  print("----------------------------------------------------------------------------------------------")
  print("subject:     %s" % values['subject'])
  print("----------------------------------------------------------------------------------------------")
  print("filename:    %s" % values['filename'])
  print("fingerprint: %s" % values['thumbprint'])
  print("serial:      %s" % values['serial'])
  print("status:      %s" % values['status'])
  print("end date:    %s" % values['end_date'])
  print("days left    %s" % int(values['days_remaining']))
  print("sans:          ")
  try:
    sans = values['sans'][0]
    sans = sans.split(',')
    for san in sans:
        print("            %s" % san.replace('DNS:', ''))
  except IndexError:
    continue 
  print("\n")


build_webpage(cert_dict)

sys.exit(0)
