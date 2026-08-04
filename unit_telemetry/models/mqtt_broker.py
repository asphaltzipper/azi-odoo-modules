import logging
import time
import json
import math
import re
from odoo import models, api, fields, registry, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.mqtt_integration.utils import broker_client, get_first_or_zero

_logger = logging.getLogger(__name__)


class MqttBroker(models.Model):
    _inherit = 'mqtt.broker'

    def _run_listener_thread_safe(self, broker_id, dbname, stop_event):
        reg = registry(dbname)
        with reg.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            broker = env['mqtt.broker'].browse(broker_id)
            topic_names = self.get_subscribed_topics_for_broker(env, broker.id)

            broker_data = {
                'id': broker.id,
                'name': broker.name,
                'host': broker.host,
                'port': broker.port,
                'keepalive': broker.keepalive,
                'username': broker.username,
                'password': broker.password,
                'client_id': broker.client_id,
                'protocol': broker.protocol,
                'clean_session': broker.clean_session,
            }

        client = broker_client(
            client_id=broker_data['client_id'],
            clean_session=broker_data['clean_session'],
            protocol=broker_data['protocol'],
        )
        if broker_data['username']:
            client.username_pw_set(broker_data['username'], broker_data['password'] or None)

        def on_connect(client, userdata, flags, rc, properties=None):
            if getattr(client, '_subscribed', False):
                return
            _logger.info(f"[{dbname}] Connected to broker {broker_data['name']}.")

            if topic_names:
                for topic in topic_names:
                    client.subscribe(topic)
                    _logger.info(f"[{broker_data['name']}] Batch subscribed to topic: {topic}")

            client._subscribed = True

        def on_message(client, userdata, msg):
            _logger.info(f"Message received on {msg.topic}: {msg.payload}")
            with registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                topic_env = env['mqtt.topic']
                client_env = env['mqtt.client']
                metadata_model = env['mqtt.metadata']
                metadata_value_model = env['mqtt.metadata.value']
                history_env = env['mqtt.message.history']

                # ##################################################################
                # this stuff is different from the original _run_listener_thread_safe()
                topic = topic_env.search([], limit=None)
                topic = next((t for t in topic if t.client_regex and re.match(t.client_regex, msg.topic)), False)
                sub_exist = env['mqtt.subscription'].search([
                    ('topic_id', '=', topic.id if topic else False),
                    ('state', '=', 'subscribe'),
                ], limit=1)
                # ##################################################################

                if not sub_exist:
                    _logger.warning(f"Topic {msg.topic} is not subscribed.")
                    return

                try:
                    # Process message properties and metadata
                    metadata = None
                    metadata_value = []

                    if hasattr(msg.properties, 'UserProperty'):
                        user_props = msg.properties.UserProperty or {}
                        #_logger.info(f"UserProperty received on {msg.topic}: {msg.properties}")

                        # Properties MQTT
                        content_type = getattr(msg.properties, 'ContentType', None)
                        format_payload = getattr(msg.properties, 'PayloadFormatIndicator', None)
                        expiry = getattr(msg.properties, 'MessageExpiryInterval', None)
                        response_topic = getattr(msg.properties, 'ResponseTopic', None)
                        correlation_data = getattr(msg.properties, 'CorrelationData', None)
                        subscription_identifier = getattr(msg.properties, 'SubscriptionIdentifier', None)
                        metadata_data = {
                            'name': 'Metadata for ' + msg.topic + str(fields.Datetime.now()),
                            'topic_id': topic.id if topic else False,
                            'history_id': False,
                            'subscription_id': sub_exist.id if sub_exist else False,
                            'direction': 'incoming',
                            'content_type': content_type,
                            'format_payload': '1' if format_payload == 1 else '0',
                            'expiry': expiry,
                            'response_topic': response_topic,
                            'correlation_data': correlation_data,
                            'subscription_identifier': get_first_or_zero(subscription_identifier),
                            'metadata_value_ids': metadata_value,
                        }
                        metadata = metadata_model.create(metadata_data)
                        #_logger.info(f"Metadata received on {msg.topic} created: {metadata.name or ''}.")

                        for key, value in user_props:
                            metadata_value_data = {
                                'key': key,
                                'value': value,
                                'timestamp': fields.Datetime.now(),
                                'metadata_id': metadata.id if metadata else False,
                                'topic_id': topic.id if topic else False,
                            }
                            metadata_value.append(metadata_value_model.create(metadata_value_data))

                    message_data = {
                        'broker_id': broker_id,
                        'metadata_id': metadata.id if metadata else False,
                        'subscription_id': sub_exist.id if sub_exist else False,
                        'topic_name': topic.name,
                        'topic': msg.topic,
                        'payload': msg.payload.decode(errors='ignore'),
                        'direction': 'incoming',
                        'qos': msg.qos,
                        'retain': msg.retain,
                        'timestamp': fields.Datetime.now(),
                    }

                    # ##################################################################
                    # this stuff is different from the original _run_listener_thread_safe()
                    if topic and topic.client_regex:
                        code_match = re.match(topic.client_regex, msg.topic)
                        iccid = code_match and code_match.group(1)
                        if iccid:
                            client_device = client_env.search([('name', '=', iccid)])
                            if client_device:
                                message_data['client_id'] = client_device.id
                    # ##################################################################

                    history = history_env.create(message_data)
                    #_logger.info(f"Message history created for topic {msg.topic}: {history.name or ''}.")

                    # Update metadata with history and values
                    if metadata:
                        metadata.update({
                            'history_id': history.id if history else False,
                            'metadata_value_ids': [(6, 0, [mv.id for mv in metadata_value])] if metadata_value else False
                        })
                    #_logger.info(f"Metadata updated with history and values for topic {msg.topic}.")

                except Exception as e:
                    _logger.error(f"Error processing message for topic {msg.topic}: {e}")

                # Save to bus for real-time updates
                env['bus.bus']._sendone(
                    dbname,
                    ['mqtt_realtime'],
                    {
                        'topic': msg.topic,
                        'payload': msg.payload.decode(errors='ignore'),
                        'broker': broker_data['name'],
                        'timestamp': str(fields.Datetime.now())
                    }
                )

                #_logger.info(f"Saved MQTT messages to database: {topic.broker_id.name if topic else 'Unknow'} - {msg.topic}.")
                cr.commit()

        def on_disconnect(client, userdata, rc, properties=None, reason_codes=None):
            reason_str = getattr(rc, 'name', str(rc))
            _logger.warning(f"[{dbname}] Disconnected from {broker_data['name']} - Reason: {reason_str}.")

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        try:
            client.connect(broker_data['host'], int(broker_data['port']), broker_data['keepalive'])
            client.loop_start()
            _logger.info(f"[{dbname}] Initial connection for {broker_data['name']} successfully.")

        except Exception as e:
            _logger.error(f"[{dbname}] Initial connection failed for {broker_data['name']}: {e}")
            raise UserError(f"[{dbname}] Initial connection failed for {broker_data['name']}.")

        # === Main listener loop ===
        reconnect_fail_count = 0
        last_reconnect_time = 0
        min_delay = 3
        max_delay = 60

        while not stop_event.is_set():
            try:
                time.sleep(min_delay)
                # Poll database for other worker to stop signal
                with registry(dbname).cursor() as cr:
                    cr.execute("SELECT listener_status FROM mqtt_broker WHERE id = %s", (broker_id,))
                    row = cr.fetchone()
                    if row and row[0] != 'run':
                        _logger.info(f"mqtt_broker.listener_status = {row and row[0] or 'NULL'}")
                        stop_event.set()
                        break
                if not client.is_connected():
                    reconnect_fail_count += 1
                    # Exponential backoff
                    delay = min(max_delay, min_delay * int(math.pow(2, reconnect_fail_count)))
                    now = time.time()
                    if now - last_reconnect_time < delay:
                        continue
                    last_reconnect_time = now
                    _logger.warning(f"[{dbname}] Attempting reconnect to {broker_data['name']}...")

                    try:
                        client.reconnect()
                        client._subscribed = False
                        _logger.info(
                            f"[{dbname}] Reconnected to {broker_data['name']} (after {reconnect_fail_count} fails).")
                        reconnect_fail_count = 0  # Reset counter after success

                    except Exception as e:
                        _logger.error(f"[{dbname}] Reconnect failed: {e}")
                        # Notify after 5 consecutive fails
                        if reconnect_fail_count == 5:
                            with registry(dbname).cursor() as cr:
                                env = api.Environment(cr, SUPERUSER_ID, {})
                                # Notify via bus (or send email if desired)
                                env['bus.bus']._sendone(
                                    dbname, ['mqtt_realtime'],
                                    {"error": f"Reconnect fail 5 times for broker {broker_data['name']}"}
                                )

            except Exception as e:
                _logger.error(f"[{dbname}] Error in MQTT loop for {broker_data['name']}: {e}")
                time.sleep(1)

        # Cleanup: Unsubscribe before disconnecting
        try:
            with registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                topic_names = self.get_subscribed_topics_for_broker(env, broker_id)

            if topic_names and broker_data.get('clean_session', True):
                client.unsubscribe(topic_names)
                _logger.info(f"Batch unsubscribed from {len(topic_names)} topics: {', '.join(topic_names)}")

                time.sleep(1)

        except Exception as e:
            _logger.error(f"[{dbname}] Error during unsubscribe in thread cleanup: {e}")

        client.loop_stop()
        client.disconnect()
        _logger.info(f"[{dbname}] Listener thread for broker {broker_data['name']} fully stopped and disconnected.")
