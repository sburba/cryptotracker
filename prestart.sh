#!/usr/bin/env sh

set -e

if [ "$WAIT_FOR_DB" = "true" ]; then
  wait-for-it db:5432
fi