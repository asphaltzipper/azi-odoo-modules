This module adds special handling for MQTT messages received from telematics client
devices on an Asphalt Zipper.

**TODO: combine the topic and subscription models**
- Why create multiple subscriptions for the same broker and topic?
- If creating one for inbound, and one for outbound, why call it a subscription?
- Maybe we should add a publication model?

**TODO: try out the metadata models from mqtt_integration module

## Clients

The mqtt.client model identifies each telematics device with Odoo.  The Name field has a
uniqueness constraint, and contains the ICCID of the SIM card installed in the device.

When a message is received, the message topic is parsed for a client_id (ICCID), and
matched to the name of a record in the mqtt.client model.

### Client Serials

Each client (telematics device) can be associated a physical Asphalt Zipper unit.  That
association is made via the mqtt.client.serial model.  Although the device When the device is moved from one
physical Asphalt Zipper unit to another, a new record must be created in the mqtt.client.serial model.

## Topics

The message topics, sent by our client devices, will include the ICCID:

- Message Topic = <equipment_type>/<ICCID>/<subtopic>
  - equipment_type = zipper
  - ICCID = The ICCID number from the SIM card
  - subtopic =
    - gps (QoS=2)
    - dtc (QoS=1)
    - hrs (QoS=0)

The names for Topic records in Odoo will include wildcards:

- Topic names:
  - zipper/+/gps
  - zipper/+/dtc
  - zipper/+/hrs

## Payload

- Message Payload (JSON format)
  - gps = {"lat": "40.355855937719305", "long": "-111.74536641215731"}
  - dtc = {"spn": "5432", "fmi": "4", "addr": "35"}
  - hrs = {"hrs": "235.4"}
