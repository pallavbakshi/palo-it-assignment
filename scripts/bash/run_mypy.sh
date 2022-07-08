#!/bin/bash
echo "============ Running 📦 mypy ============"

mypy .

retVal=$?
if [ $retVal -ne 0 ]
  then
    echo "❌ Failed mypy with exit code ${retVal}"
fi
exit $retVal