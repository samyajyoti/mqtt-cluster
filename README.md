# mqtt-cluster

Three-node EMQX cluster using Docker Compose, with settings split into a local `.env` file.

## What was wrong in the original compose

Your original file was close in structure, but a few parts were not correct for current `emqx/emqx:latest` images:

- `EMQX_CLUSTER__DISCOVERY` should be `EMQX_CLUSTER__DISCOVERY_STRATEGY`.
- `EMQX_NAME` and `EMQX_HOST` are older-style variables; current images are clearer with `EMQX_NODE__NAME`.
- `EMQX_NODE_COOKIE` should be `EMQX_NODE__COOKIE`.
- `EMQX_CLUSTER__STATIC__SEEDS` should contain node names such as `[emqx@emqx1,emqx@emqx2,emqx@emqx3]`, not Erlang port values like `:4369`.
- `EMQX_AUTH__USER_FILE=/opt/emqx/etc/emqx_auth.conf` and a plain file like:

  ```text
  admin:<password>
  mqttuser:<password>
  ```

  are not a valid username/password bootstrap method for current EMQX `latest`.

## Files

- `docker-compose.yml`: corrected 3-node cluster definition.
- `.env`: local runtime values.
- `.env.example`: template for other environments.

## TLS certificate files

Put these files under `certs/`:

- `certs/STAR_wrtual_in.chain.crt`
- `certs/star_wrtual.key`

You can change the filenames in `.env` if needed.

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
