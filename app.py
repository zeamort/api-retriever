import connexion
from connexion import NoContent
import json
from datetime import datetime
import requests
import yaml
import logging
import logging.config
import uuid

MAX_EVENTS = 5
EVENT_FILE = "events.json"

# Load the app_conf.yml configuration 
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load the log_conf.yml configuration 
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Create a logger for this file
logger = logging.getLogger('basicLogger')

# Your functions here
def report_power_usage_reading(body):
    body['trace_id'] = str(uuid.uuid4())
    
    logger.info(f"Received event power-usage request with a trace id of {body['trace_id']}")

    response = requests.post(app_config['report_power_usage_reading']['url'], json=body, headers={"Content-Type": "application/json"})
    
    logger.info(f"Returned event power-usage response (Id: {body['trace_id']}) with status {response.status_code}")

    return NoContent, response.status_code


def report_location_reading(body):
    body['trace_id'] = str(uuid.uuid4())
    
    logger.info(f"Received event location request with a trace id of {body['trace_id']}")
    
    response = requests.post(app_config['report_location_reading']['url'], json=body, headers={"Content-Type": "application/json"})
    
    logger.info(f"Returned event location response (Id: {body['trace_id']}) with status {response.status_code}")
    
    return NoContent, response.status_code


def save_event(event_message, event_type):
    with open(EVENT_FILE, "r") as json_file:
        events = json.load(json_file)

    events[event_type]["count"] += 1

    # format the event message based on the event type
    if event_type == "power_usage":
        formatted_event_message = {
            "message_data": f"{event_message['device_type']} unit with device id {event_message['device_id']} outputted {event_message['power_data']['power_W']} watts of power and the battery is currently at {event_message['power_data']['state_of_charge_%']}%.",
            "received_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
    elif event_type == "location":
        formatted_event_message = {
            "message_data": f"{event_message['device_type']} unit with device id {event_message['device_id']} is currently located at {event_message['location_data']['gps_latitude']}, {event_message['location_data']['gps_longitude']}.",
            "received_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }

    # insert the formatted event message at the beginning of the list of recent messages
    events[event_type]["recent"].insert(0, formatted_event_message)

    # check if the number of messages is now exceeding MAX_EVENTS, in which case remove the oldest message
    if len(events[event_type]["recent"]) > MAX_EVENTS:
        events[event_type]["recent"].pop()
    
    # write the updated events to the file
    with open(EVENT_FILE, "w") as json_file:
        json.dump(events, json_file)


def main():
    app = connexion.FlaskApp(__name__, specification_dir='')
    app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)
    app.run(port=8080)


if __name__ == "__main__":
    main()
