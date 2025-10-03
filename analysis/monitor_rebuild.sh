#!/bin/bash
# Monitor Wiktionary rebuild progress

PID_FILE="analysis/wiktionary_rebuild.pid"
LOG_FILE="analysis/wiktionary_rebuild.log"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID file not found: $PID_FILE"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "❌ Process $PID is not running"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 "$LOG_FILE"
    exit 1
fi

# Get process info
ELAPSED=$(ps -p $PID -o etime= | tr -d ' ')
CPU=$(ps -p $PID -o %cpu= | tr -d ' ')
MEM=$(ps -p $PID -o %mem= | tr -d ' ')

# Get current page count
CURRENT=$(tail -1 "$LOG_FILE" | grep -oP 'Processed \K[0-9,]+' | tr -d ',')

if [ -z "$CURRENT" ]; then
    CURRENT=0
fi

# Estimate total pages (from previous runs)
TOTAL=10158088

# Calculate progress
if [ $CURRENT -gt 0 ]; then
    PERCENT=$(echo "scale=2; $CURRENT * 100 / $TOTAL" | bc)
    PAGES_LEFT=$(echo "$TOTAL - $CURRENT" | bc)

    # Estimate time (rough calculation based on current elapsed time)
    # Convert elapsed to seconds
    if [[ $ELAPSED =~ ([0-9]+):([0-9]+):([0-9]+) ]]; then
        HOURS=${BASH_REMATCH[1]}
        MINS=${BASH_REMATCH[2]}
        SECS=${BASH_REMATCH[3]}
        ELAPSED_SEC=$((10#$HOURS * 3600 + 10#$MINS * 60 + 10#$SECS))
    elif [[ $ELAPSED =~ ([0-9]+):([0-9]+) ]]; then
        MINS=${BASH_REMATCH[1]}
        SECS=${BASH_REMATCH[2]}
        ELAPSED_SEC=$((10#$MINS * 60 + 10#$SECS))
    else
        ELAPSED_SEC=0
    fi

    if [ $ELAPSED_SEC -gt 0 ]; then
        RATE=$(echo "scale=2; $CURRENT / $ELAPSED_SEC" | bc)
        if [ $(echo "$RATE > 0" | bc) -eq 1 ]; then
            ETA_SEC=$(echo "scale=0; $PAGES_LEFT / $RATE" | bc)
            ETA_MIN=$(echo "scale=0; $ETA_SEC / 60" | bc)
            ETA_HOUR=$(echo "scale=1; $ETA_MIN / 60" | bc)
        else
            ETA_HOUR="N/A"
        fi
    else
        RATE="N/A"
        ETA_HOUR="N/A"
    fi
else
    PERCENT=0
    PAGES_LEFT=$TOTAL
    RATE="N/A"
    ETA_HOUR="N/A"
fi

echo "════════════════════════════════════════════════════════════"
echo "  Wiktionary Database Rebuild Progress"
echo "════════════════════════════════════════════════════════════"
echo "PID:           $PID"
echo "Status:        Running"
echo "Elapsed:       $ELAPSED"
echo "CPU:           ${CPU}%"
echo "Memory:        ${MEM}%"
echo ""
echo "Progress:      $CURRENT / $TOTAL pages (${PERCENT}%)"
echo "Pages left:    $PAGES_LEFT"
if [ "$RATE" != "N/A" ]; then
    echo "Rate:          ${RATE} pages/sec"
fi
if [ "$ETA_HOUR" != "N/A" ]; then
    echo "ETA:           ${ETA_HOUR} hours"
fi
echo ""
echo "Last 5 log entries:"
tail -5 "$LOG_FILE"
echo "════════════════════════════════════════════════════════════"
