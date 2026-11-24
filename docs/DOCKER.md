# PostgreSQL in Docker

`docker-compose.yml` at the repository root runs PostgreSQL 16 with pgvector (`pgvector/pgvector:0.8.7-pg16-bookworm`) for cerebrollm. It replaces the PostgreSQL parts of the Quick start (steps 2 and 3 of the README); Python 3.12, Ollama and the models (step 4) are still needed.

## Steps

1. Install Docker Engine 28.0.0 or newer, with Compose v2. Older Engine releases can expose a port published on `127.0.0.1` to hosts on your network segment, so the loopback binding only holds from 28.0.0 (Docker Desktop includes an Engine; its version shows in the same command). Check: `docker version --format '{{.Server.Version}}'` prints 28.0.0 or higher, and `docker compose version` prints a version.
2. From the clone, choose a database password and start the database:

   ```
   export CEREBROLLM_PG_PASSWORD="choose-a-password"
   docker compose up -d --wait
   ```

   Check: `docker compose ps` lists `db` as `healthy`, and `docker compose port db 5432` prints `127.0.0.1:54329` (if it prints `0.0.0.0` or another address, stop the database with `docker compose down` and do not use it). Add the `export` line to your shell profile: cerebrollm reads the password from that variable and never from a file.
3. Create the Python environment, as `engine/setup/user.sh` does: `python3.12 -m venv ~/.cerebrollm/venv && ~/.cerebrollm/venv/bin/pip install -r engine/requirements.txt`. Check: `(cd engine && ~/.cerebrollm/venv/bin/python -c "import cerebrollm")` prints nothing; the parentheses keep your shell in the clone.
4. Pull the models (README step 4). Check: `ollama list` shows both.
5. Copy the configuration and add your rule (README, "First ask", step 2). In that copy, replace the line `socket_dir = ...` under `[postgres]` with the two lines below, and give the Docker database its own state folder by changing `state_dir`:

   ```
   host = "127.0.0.1"
   password_env = "CEREBROLLM_PG_PASSWORD"
   ```

   ```
   state_dir = "~/.cerebrollm-docker"
   ```

   `port = 54329` already matches the published port. Check, from the clone: the last line of `engine/bin/cerebrollm --config ~/cerebrollm.toml status` is `postgres connection: tcp 127.0.0.1:54329  user cerebrollm  password from $CEREBROLLM_PG_PASSWORD`.
6. Build the index with a full run: `engine/bin/cerebrollm --config ~/cerebrollm.toml index`. Check: `status` lists chunks for your tier.

## Things to know

- The container publishes `127.0.0.1:54329`. Do not change the mapping to `54329:5432`: that exposes the database to your network, and the connection is not encrypted. The database also needs the password you set, because the compose file refuses to start without it.
- Never run plain `docker compose config` with the real password exported: it prints the interpolated `POSTGRES_PASSWORD`. To validate the file use `docker compose config --quiet`, which prints nothing on success.
- PostgreSQL stores the password when it first creates the volume. Changing `CEREBROLLM_PG_PASSWORD` later does not change it; `docker compose down -v` deletes the volume (and the index in it), after which the next `up` uses the new value.
- `docker compose down` stops the database and keeps the data. The index can always be rebuilt from your files with `cerebrollm index`.
- The state folder (`state_dir`) holds `docstore.json`, the hashes of what one database contains, and `state.json`, which records that database's identity. `index --changed` uses them to skip unchanged files, so each database needs its own state folder. If a state folder written for another database is reused, or the database is empty while `docstore.json` exists, `index --changed` refuses with a message; run a full `cerebrollm index`, which rebuilds the table and replaces `docstore.json` in that folder.
- To go back to the socket database: in your configuration remove `host` and `password_env`, restore the `socket_dir` line and the original `state_dir`. The socket index and its state folder were not touched, because the Docker setup used its own `state_dir`. If you pointed the Docker database at the old `state_dir` instead, the next full index replaced its `docstore.json`: run a full `cerebrollm index` against the socket database to match it again.
- The engine creates the `vector` extension on first use. This works because the image's `POSTGRES_USER` (`cerebrollm`) is a superuser.
- Port 54329 is the engine's default. If another service uses it, change both the left side of `ports` in `docker-compose.yml` and `port` in your configuration.
- `[postgres] host` must be the IP address `127.0.0.1` or `::1`; `localhost` is accepted and read as `127.0.0.1`, so no name lookup decides where the connection goes. `port` is an integer from 1 to 65535. Any other host is refused when the configuration loads: remote databases are not supported in this release, because the connection has no `sslmode` setting and is unencrypted. The client connects to exactly that address (libpq `hostaddr`), so `PGHOSTADDR`, `PGHOST` and `PGPORT` in your environment cannot redirect it. A TCP connection that accepts and then stalls fails after 10 seconds.

## What was tested

- Unit tests (`engine/tests/test_postgres_tcp.py`) cover the configuration rules, the URL (a password with `@`, `:`, `/` and `#` is encoded), the `status` line and the MCP down message.
- The same test file starts its own throw-away PostgreSQL cluster that listens on 127.0.0.1 with password authentication, connects with `password_env`, writes a row through the vector store, runs a query through the async driver, and checks that a wrong password is refused. With `PGHOSTADDR`, `PGHOST` and `PGPORT` pointing elsewhere, every TCP path still reaches the configured server. A listener that accepts and never answers makes each driver reach its own timeout. `index --changed` refusals are tested with fakes and against an empty database. A manual run of `index`, `status`, `search` and `verify` against such a cluster also passed.
- `docker compose config --quiet` accepts the file with a dummy password and fails with a named message when the variable is unset (run with a dummy value, never the real password).
- These tests are client coverage against a stand-in cluster, not a run of this guide. Not tested yet: starting the image, the health check, the port check above, and every step above on a clean machine.
