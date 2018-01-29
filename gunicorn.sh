#!/bin/bash
set -e
exec gunicorn -w 4 -b 0.0.0.0:5000 ndrest:app &
