#!/bin/bash
echo "============ Running 🎱 flake8 ============"

flake8 .

retVal=$?
if [ $retVal -ne 0 ]
  then
    echo "❌ Failed flake8 with exit code ${retVal}"
fi
exit $retVal
	

