from fritzconnection.core.fritzmonitor import FritzMonitor
from fritzconnection.lib.fritzphonebook import FritzPhonebook
import queue
import datetime
import yaml
import re
from enum import Enum
import phonenumber
import mail


class CallAction(str, Enum):
    RING = "RING"
    CALL = "CALL"
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"


def parse_call_event(event, call_history):
    fields = event.split(";")
    time_str = fields[0]
    action_str = fields[1]
    id = int(fields[2])

    timestamp = datetime.datetime.strptime(time_str, "%d.%m.%y %H:%M:%S")
    if action_str == CallAction.RING:
        call_history[id] = {"id": id, "type": "incoming", "from": fields[3], "to": fields[4], "device": fields[5],
                            "initiated": timestamp, "accepted": None, "closed": None}
    elif action_str == CallAction.CALL:
        call_history[id] = {"id": id, "type": "outgoing", "from": fields[4], "to": fields[5], "device": fields[6],
                            "initiated": timestamp, "accepted": None, "closed": None}
    elif action_str == CallAction.CONNECT and id in call_history:
        call_history[id]["accepted"] = timestamp
    elif action_str == CallAction.DISCONNECT and id in call_history:
        call_history[id]["closed"] = timestamp
    return call_history[id], action_str


def process_events(config, monitor, event_queue, healthcheck_interval=10):
    call_history = {}
    while True:
        try:
            event = event_queue.get(timeout=healthcheck_interval)
            print(event)
            call, action = parse_call_event(event, call_history)
            if action in (CallAction.RING, CallAction.CALL):
                # send mail when call starts
                if not is_trusted_call(config, call):
                    print("untrusted call", call)
                    generate_mail(config, call)
            elif action == CallAction.DISCONNECT and call["id"] in call_history:
                # send mail when call was accepted and ends
                if call["accepted"] is not None and not is_trusted_call(config, call):
                    generate_mail(config, call)
                # clear memory
                del call_history[call["id"]]
            print(call)
        except queue.Empty:
            # check health:
            if not monitor.is_alive:
                raise OSError("Error: fritzmonitor connection failed")
        else:
            # do event processing here:
            print(event)


def generate_mail(config, call):
    content = ""

    for key, value in call.items():
        converted_value = str(value)
        if type(value) is datetime.datetime:
            converted_value = value.strftime("%d.%m.%y %H:%M:%S")
        content += f"{key}: {str(converted_value)}\n"

    mail.send_mail(config, config["alert"]["subject"], content)


def is_trusted_call(config, call):
    trusted_numbers = get_known_phonebook_numbers(config)

    if call["type"] == "incoming":
        number_to_check = call["from"]
    else:
        number_to_check = call["to"]

    number_to_check = phonenumber.normalize(number_to_check, config["phone-default-region"])

    if number_to_check in trusted_numbers:
        print(f"phonebook contains number {number_to_check}")
        return True

    if "trusted-number-regex" in config and re.search(config["trusted-number-regex"], number_to_check) is not None:
        print(f"number matches the trusted-number-regex {number_to_check}")
        return True

    return False


def read_config():
    import os
    config_path = os.getenv("FRITZ_MONITOR_CONFIG", "config.yml")
    with open(config_path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        print(config)
    return config


def start_monitoring(config):
    try:
        # as a context manager FritzMonitor will shut down the monitor thread
        with FritzMonitor(address=config["fritz"]["address"]) as monitor:
            event_queue = monitor.start()
            process_events(config, monitor, event_queue)
    except (OSError, KeyboardInterrupt) as err:
        print(err)


def get_known_phonebook_numbers(config):
    fp = FritzPhonebook(address=config["fritz"]["address"], password=config["fritz"]["password"])

    number_set = set()
    for phonebook_id in fp.phonebook_ids:
        contacts = fp.get_all_names(phonebook_id)
        print(contacts)
        for name, numbers in contacts.items():
            for number in numbers:
                number_set.add(phonenumber.normalize(number, config["phone-default-region"]))
    return number_set


def main():
    config = read_config()
    get_known_phonebook_numbers(config)

    if config["alert"]["enable-startup-alert"]:
        mail.send_mail(config, "Startup", "FritzCallMonitor just started")
    start_monitoring(config)


if __name__ == '__main__':
    main()



