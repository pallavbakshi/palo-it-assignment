#!/bin/bash
echo "============ Running ⚫️ black ============"

black .

retVal=$?
if [ $retVal -ne 0 ]
  then
    echo "❌ Failed black with exit code ${retVal}"
fi
exit $retVal
	

