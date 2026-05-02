#!/usr/bin/env bash

set -euo pipefail

cd /workspace
make backend-init
make extension-init
