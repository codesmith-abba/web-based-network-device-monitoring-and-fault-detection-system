#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"

printf 'Checking public health endpoint...\n'
curl --fail --silent --show-error "${BASE_URL}/api/health/" >/dev/null

printf 'Checking frontend...\n'
curl --fail --silent --show-error "${BASE_URL}/" >/dev/null

printf 'Checking static asset path...\n'
if curl --fail --silent --show-error "${BASE_URL}/static/admin/css/base.css" >/dev/null; then
    printf 'Static files: OK\n'
else
    printf 'Static files: unavailable; verify collectstatic and Nginx configuration.\n'
    exit 1
fi

printf 'Production smoke test passed.\n'
