#!/bin/bash
set -e

pip install -r requirements.txt 
exec gunicorn -w 4 -b 0.0.0.0:5000 ndrest:app > /dev/null &

if [ -d NDLib_viz ]; then 
  rm -rf NDLib_viz 
fi

git clone https://github.com/GiulioRossetti/NDLib_viz.git > /dev/null 
cd NDLib_viz 
npm install 
npm run dev &
