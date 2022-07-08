#!/bin/bash
echo "============ Running 🔝 isort ============"

isort -v .

retVal=$?
if [ $retVal -ne 0 ]
  then
    echo "❌ Failed isort with exit code ${retVal}"
fi
exit $retVal
	

