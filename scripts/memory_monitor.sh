#!/usr/bin/env bash
# Memory monitoring script for graph-sitter tests
# This script helps prevent segmentation faults by monitoring memory usage

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
MAX_MEMORY_GB=31
CHECK_INTERVAL=1
PID_TO_MONITOR=$1

if [ -z "$PID_TO_MONITOR" ]; then
    echo -e "${RED}Error: No PID provided to monitor${NC}"
    echo -e "Usage: $0 <pid> [max_memory_gb] [check_interval]"
    exit 1
fi

if [ -n "$2" ]; then
    MAX_MEMORY_GB=$2
fi

if [ -n "$3" ]; then
    CHECK_INTERVAL=$3
fi

echo -e "${BLUE}Starting memory monitor for PID ${PID_TO_MONITOR}${NC}"
echo -e "${BLUE}Maximum memory: ${MAX_MEMORY_GB} GB${NC}"
echo -e "${BLUE}Check interval: ${CHECK_INTERVAL} seconds${NC}"

while ps -p $PID_TO_MONITOR > /dev/null; do
    # Get memory usage in KB
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        MEMORY_KB=$(ps -o rss= -p $PID_TO_MONITOR)
    else
        # Linux
        MEMORY_KB=$(ps -o rss= -p $PID_TO_MONITOR)
    fi
    
    # Convert to GB with 2 decimal places
    MEMORY_GB=$(echo "scale=2; $MEMORY_KB / 1024 / 1024" | bc)
    
    # Log memory usage
    echo -e "${YELLOW}Memory usage: ${MEMORY_GB} GB / ${MAX_MEMORY_GB} GB${NC}"
    
    # Check if memory exceeds threshold
    if (( $(echo "$MEMORY_GB > $MAX_MEMORY_GB" | bc -l) )); then
        echo -e "${RED}${BOLD}Memory usage exceeded ${MAX_MEMORY_GB} GB!${NC}"
        echo -e "${RED}Sending SIGTERM to process ${PID_TO_MONITOR} to prevent segmentation fault${NC}"
        kill -15 $PID_TO_MONITOR
        
        # If process doesn't terminate within 5 seconds, force kill it
        sleep 5
        if ps -p $PID_TO_MONITOR > /dev/null; then
            echo -e "${RED}Process did not terminate gracefully. Sending SIGKILL.${NC}"
            kill -9 $PID_TO_MONITOR
        fi
        
        exit 1
    fi
    
    sleep $CHECK_INTERVAL
done

echo -e "${GREEN}Process ${PID_TO_MONITOR} has terminated. Memory monitor stopping.${NC}"
exit 0

