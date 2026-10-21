#!/bin/sh
# First start: load the bundled registry into the database volume. Every
# start after that serves what the volume holds, including codes this
# deployment issued.
set -eu
DB="${ADDRESSES_DB:-/data/addresses.sqlite}"
if [ ! -s "$DB" ]; then
  echo "no database at $DB: importing the bundled registry" >&2
  python3 -m server import --registry "${REGISTRY_DIR:-/app/registry}" --db "$DB"
fi
exec python3 -m server serve --db "$DB" --port "${PORT:-8080}"
