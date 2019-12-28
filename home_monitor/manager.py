import datetime
from home_monitor import config
from home_monitor.model.sensor import Sensor, Reading
from pytils import validator, slack, http, logger

class SensorManager:
    
    sensor_checker = validator.Checker().all()
    sensor_checker.add_rule(lambda x: x.temperature > 15, 'Temperature is to low.')
    sensor_checker.add_rule(lambda x: x.temperature < 30, 'Temperature is to high.')
    sensor_checker.add_rule(lambda x: x.humidity > 30, 'Humidity is to low.')
    sensor_checker.add_rule(lambda x: x.humidity < 70, 'Humidity is to high.')

    def __init__(self, lifetime=24):
        self._sensors = {}

    def update(self, reading):
        if reading.name in self._sensors:
            self._sensors[reading.name].reading = reading
        else:
            self._sensors[reading.name] = Sensor(reading)

        sensor = self._sensors[reading.name]
        status_code = http.post_json(config.save_sensor_url, reading.to_json())
        self.check(sensor)

    def check(self, sensor):
        if not self.sensor_checker.validate(sensor.reading):
            if not sensor.alarm_state:
                alarm = self.sensor_checker.evaluate(sensor.reading)
                self.notify(alarm, sensor.reading)
                logger.warning(alarm)
            sensor.alarm_state = True
        elif sensor.alarm_state:
                sensor.alarm_state = False
                # Notify back to normal?

    def notify(self, alarm, sensor):
        message = 'Warning {}! {} Temperature {} C, Humidity {} %'.format(sensor.name, alarm, sensor.temperature, sensor.humidity)
        slack.post(config.slack_webhook_url, message)