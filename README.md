# FritzCallMonitor

A simple python script for the FritzBox which sends mails to alert when a call with an untrusted phone number is established. 
The number is considered trustworthy if it is stored in the phone book or it matches the `trusted-number-regex` RegEx.

## Installation

- Download requirements
```
pip3 install -r requirements.txt 
```

- Enable CallMonitor Service on FritzBox by calling this number with a connected phone
```
activate: #96*5*
deactivate: #96*4*
```

- Create configuration file and add the path to the environment variable `FRITZ_MONITOR_CONFIG`
```yaml
fritz:
  address: 192.168.178.1
  password: <password>

trusted-number-regex: '^(\+49)' # the numbers are formatted in E164
phone-default-region: DE # is used to parse the phone numbers

mail:
  smtp-server: "smtp.gmail.com"
  smtp-port: 587
  sender-address: "<mailaddress@gmail.com>"
  password: "<password>"
  receiver-addresses:
    - "user1@mail.com"
    - "user2@mail.com"

alert:
  enable-startup-alert: true
  subject: Suspicious Call
``` 
- Start
```
python3 app.py
```
