# mqtt-cluster

Three-node EMQX cluster using Docker Compose, with settings split into a local `.env` file.

The example configuration pins EMQX to `emqx/emqx:5.8.8` instead of floating on `latest`.

## What was wrong in the original compose

Your original file was close in structure, but a few parts were not correct for newer floating `emqx/emqx:latest` images:

- `EMQX_CLUSTER__DISCOVERY` should be `EMQX_CLUSTER__DISCOVERY_STRATEGY`.
- `EMQX_NAME` and `EMQX_HOST` are older-style variables; current images are clearer with `EMQX_NODE__NAME`.
- `EMQX_NODE_COOKIE` should be `EMQX_NODE__COOKIE`.
- `EMQX_CLUSTER__STATIC__SEEDS` should contain node names, and with EMQX 6 these should be FQDN-style names such as `[emqx@emqx1.mqtt.local,emqx@emqx2.mqtt.local,emqx@emqx3.mqtt.local]`, not Erlang port values like `:4369`.
- `EMQX_AUTH__USER_FILE=/opt/emqx/etc/emqx_auth.conf` and a plain file like:

  ```text
  admin:<password>
  mqttuser:<password>
  ```

  are not a valid username/password bootstrap method for newer EMQX images.

## Image version

Use a specific image tag rather than `latest`.

This project now uses `emqx/emqx:5.8.8` in `.env.example` because:

- it is a stable pinned release
- it avoids the moving-target behavior of `latest`
- it avoids the EMQX 6 cluster/licensing surprises you hit with `latest`

## Files

- `docker-compose.yml`: corrected 3-node cluster definition.
- `.env`: local runtime values.
- `.env.example`: template for other environments.

## TLS certificate files

Put these files under `certs/`:

- `certs/STAR_wrtual_in.chain.crt`
- `certs/star_wrtual.key`

You can change the filenames in `.env` if needed.

## Node naming for EMQX 6

EMQX 6 clustering expects fully qualified hostnames for Erlang node discovery.

This compose uses:

- `emqx@emqx1.mqtt.local`
- `emqx@emqx2.mqtt.local`
- `emqx@emqx3.mqtt.local`

Make sure your local `.env` uses the same values for `EMQX_CLUSTER_STATIC_SEEDS`.

## Start the cluster

```bash
docker compose up -d
```

Check container health:

```bash
docker compose ps
```

Each node now includes a Docker health check that runs `emqx ctl status`.

Dashboard URLs:

- `http://localhost:18083`
- `http://localhost:18084`
- `http://localhost:18085`

Default dashboard login comes from your local `.env`.

Set `EMQX_DASHBOARD_DEFAULT_USERNAME` and `EMQX_DASHBOARD_DEFAULT_PASSWORD` there before starting the cluster.

## Monitoring and logs

For an external MQTT smoke test, use a subscriber against your public DNS name:

```bash
mosquitto_sub -h stage-mqttcluster.1984.rocks -u admin -P stage9876 -t "test/topic" -v
```

Then publish from another terminal:

```bash
mosquitto_pub -h stage-mqttcluster.1984.rocks -u admin -P stage9876 -t "test/topic" -m "hello"
```

EMQX container logs do not show every published MQTT message by default, so not seeing publish payloads in `docker logs` is expected.

`docker logs` is useful for broker startup, auth failures, listener errors, and cluster problems. To inspect message traffic, use one of these approaches:

- subscribe with `mosquitto_sub`
- enable EMQX trace for a specific client or topic in the dashboard
- use EMQX metrics/dashboard views for connection and message counters

### Docker logger service

This project also includes a `mqtt-logger` service that subscribes to MQTT topics and writes received messages to its own container logs.

Set these values in your local `.env`:

- `MQTT_LOGGER_HOST=emqx1.mqtt.local`
- `MQTT_LOGGER_PORT=1883`
- `MQTT_LOGGER_USERNAME=admin`
- `MQTT_LOGGER_PASSWORD=<your-mqtt-password>`
- `MQTT_LOGGER_TOPIC=#`

Then restart the stack and inspect the logger output:

```bash
docker compose up -d
docker logs -f mqtt-logger
```

The logger shows topic and payload as received by the subscriber. It is useful for traffic visibility, but it does not guarantee full broker-side publisher identity in the logs.

## MQTT user authentication

`EMQX_ALLOW_ANONYMOUS=false` blocks anonymous clients, but EMQX still needs an authenticator configured for MQTT usernames/passwords.

For current EMQX versions, the usual next step is:

1. Start the cluster.
2. Log in to the dashboard.
3. Create a password-based authenticator using the built-in database.
4. Add MQTT users such as `mqttuser`.

If you want, I can add an automated bootstrap script for that as the next step.
