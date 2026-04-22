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

Dashboard URLs:

- `http://localhost:18083`
- `http://localhost:18084`
- `http://localhost:18085`

Default dashboard login comes from your local `.env`.

Set `EMQX_DASHBOARD_DEFAULT_USERNAME` and `EMQX_DASHBOARD_DEFAULT_PASSWORD` there before starting the cluster.

## MQTT user authentication

`EMQX_ALLOW_ANONYMOUS=false` blocks anonymous clients, but EMQX still needs an authenticator configured for MQTT usernames/passwords.

For current EMQX versions, the usual next step is:

1. Start the cluster.
2. Log in to the dashboard.
3. Create a password-based authenticator using the built-in database.
4. Add MQTT users such as `mqttuser`.

If you want, I can add an automated bootstrap script for that as the next step.
