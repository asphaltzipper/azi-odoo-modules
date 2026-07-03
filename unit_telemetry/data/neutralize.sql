-- disable mqtt brokers
UPDATE mqtt_broker
   SET state = 'draft',
   username = NULL,
   password = NULL,
   auto_reconnect = false;
