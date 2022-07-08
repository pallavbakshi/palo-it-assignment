#!/bin/bash
echo "============ Running 🦅 vulture ============"

vulture .

retVal=$?
if [ $retVal -ne 0 ]
  then
    echo "❌ Failed vulture with exit code ${retVal}"
fi
exit $retVal