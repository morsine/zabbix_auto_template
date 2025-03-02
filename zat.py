import requests
import json
import subprocess
import datetime
requests.packages.urllib3.disable_warnings() 

# ==== VARIABLES ====
IP="192.168.1.40" #Zabbix server IP
authkey="REPLACE_ME" #API access key
DBIP="192.168.1.11" #Database server IP address
DBUSER="zabbix" #Database username
DBPASS="zabbix" #Database password
DBNAME="zabbixdb" #Database name
TMPFILE="/tmp/hosts.csv"
DEBUG="no"
# You may need to replace the template IDs and SNMP details
# ==== VARIABLES ====

# ==== FUNCTIONS ====
def clearvars():
    global hostid
    global passed
    global iosver
    global templateid
    hostid=""
    passed=""
    iosver=""
    templateid=""

def gethostid():
    global hostid
    global hostname
    global passed
    try:
        r = requests.post(f'http://{IP}/api_jsonrpc.php', verify=False, json={
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [
                    f"{hostname}"
                ]
            }
        },
        "auth": f"{authkey}",
        "id": 1
        })
        json_data = json.loads(json.dumps(r.json(), indent=4, sort_keys=True))
        dent2 = json.loads(json.dumps(json_data['result'][0], indent=4, sort_keys=True))
        hostid=(dent2['hostid'])
        passed="yes"
        if DEBUG == "yes":
            print("GET HOST ID DEBUG:")
            print(r.json())
            print(f"host ID {hostid}")
    except:
        passed="no"
        if DEBUG == "yes":
            print(f"DEBUG: {r}")
            print(r.json())
        print("An error occurred while trying to find hostid")

def getiosver():
    global hostname
    global iosver
    global passed
    try:
        command = f"snmpwalk -v3 -l authpriv -u BSI-NMS-BSI -a MD5 -A 'REPLACE_ME' -x DES -X 'REPLACE_ME' {hostname} 1.3.6.1.2.1.1.1.0 | grep Version | sed 's/.*Version //g' | sed 's/[.].*//'"
        iosver = subprocess.check_output(command, shell=True, text=True)
        iosver = int(iosver)
        if DEBUG == "yes":
            print(f"DEBUG: IOS Version detected {iosver}")
        if iosver in range(8,30):
            passed = "yes"
        if iosver == "":
            passed = "no"
    except:
        print("An error occurred while trying to find the IOS version of the device")
        passed = "no"

def dumphosts():
    global passed
    command = f"bash /root/syntrix/morsine/autotemplate/dumphosts.sh {DBIP} {DBUSER} {DBPASS} {DBNAME} > {TMPFILE}"
    try:
        subprocess.check_output(command, shell=True, text=True)
        passed = "yes"
    except:
        print("An error occurred while retrieving host list from the database")
        passed = "no"

def settemplates():
    global hostid
    global hostname
    global passed
    if 13 <= iosver:
        templateid = "26319"
    elif iosver <= 12:
        templateid = "22138"
    try:
        r = requests.post(f'https://{IP}/api_jsonrpc.php', verify=False, json={
        "jsonrpc": "2.0",
            "method": "host.update",
            "params": {
                "hostid": f"{hostid}",
                "templates": [
                    {
                        "templateid": "10186"
                    },
                    {
                        "templateid": "14879"
                    },
                    {
                        "templateid": f"{templateid}"
                    }
                ]
            },
            "auth": f"{authkey}",
            "id": 1
        })
        if DEBUG == "yes":
            print(r.json())
        # to do (add conditions for failing and verifying if the script had worked)
        passed="yes"
    except:
        passed="no"
        print(f"An error occurred while configurig templates for host {hostname} with hostid {hostid}")
# ==== FUNCTIONS ====


# ==== LOGIC ====
print("=================================================")
print("=   Software written by Morsine    syntrix.ir   =")
print("=================================================")
now = datetime.datetime.now()
print(f"Task started at {now}")
print("Requesting host list...")
dumphosts()
if passed == "no":
    print("Cannot continue due to a critical error")
    exit()
total_command = f"bash /root/syntrix/morsine/autotemplate/total.sh {TMPFILE}"
total = subprocess.check_output(total_command, shell=True, text=True)
total = int(total)
print(f"A total of {total} hosts were found")
now = datetime.datetime.now()
print(f"Starting the process at {now}")
num = 1
print("=================================================")
with open(TMPFILE) as file:
  for item in file:
    clearvars()
    print(f"Processing {num}/{total}")
    num = num + 1
    item = item.replace('\n', '').replace('\r', '')
    hostname = item
    if DEBUG == "yes":
        print(f"DEBUG: Hostname {hostname}")
    gethostid()
    if passed == "yes":
        getiosver()
        if passed == "yes":
            settemplates()
            if passed == "yes":
                print(F"Host {hostname} ID {hostid} With IOS version {iosver} was linked to the relative template.")
            else:
                print("Skipping item due to an error")
        else:
            print("Skipping item due to an error")
    else:
        print("Skipping item due to an error")
now = datetime.datetime.now()
print("=================================================")
print(f"Task completed at {now}")
# ==== LOGIC ====
