import re
import subprocess
import time
import datetime
import json
import csv

def open_file():
    # Create or check for CSV file
    return open('network-errors.csv', 'a+', newline='')

# Function to ping 8.8.8.8
def ping_google():
    while True:
        timestamp = datetime.datetime.now().isoformat()

        # Ping 8.8.8.8 (Google DNS)
        try:
            # Different ping command based on operating system
            output = subprocess.run(['ping', '-n', '1', '-w', '1000', '8.8.8.8'], capture_output=True).stdout.decode("utf-8")

            if re.search(r'Lost\s*=\s*(\d+)', output).group(1) == "0":
                # Ping successful - no need to record
                pass
            else:
                # Ping failed - record to database
                record_failed_ping(timestamp)
        except Exception:
            # Error executing ping - record to database
            record_failed_ping(timestamp)

        # Wait 1 second before next ping
        time.sleep(1)


# Function to record failed pings
def record_failed_ping(timestamp):
    with open_file() as file:
        writer = csv.writer(file)
        writer.writerow([timestamp])
        print(f"[{timestamp}] Ping failed, event logged.")

def group_consecutive_timestamps(timestamps):
    if not timestamps:
        return []

    intervals = []
    current_interval = [timestamps[0][0]]  # Start with first timestamp

    for i in range(1, len(timestamps)):
        current_time = datetime.datetime.fromisoformat(timestamps[i][0])
        previous_time = datetime.datetime.fromisoformat(timestamps[i-1][0])

        # Check if timestamps are consecutive (within 5 seconds to account for variations)
        time_diff = (current_time - previous_time).total_seconds()

        if time_diff <= 5:  # Consecutive failed pings with more tolerance
            current_interval.append(timestamps[i][0])
        else:
            # If the difference is more than 5 seconds, end current interval
            # Include even single timestamps as their own interval
            intervals.append({
                'start': current_interval[0],
                'end': current_interval[-1],
                'duration': (datetime.datetime.fromisoformat(current_interval[-1]) -
                           datetime.datetime.fromisoformat(current_interval[0])).total_seconds(),
                'failed_pings': len(current_interval)
            })
            current_interval = [timestamps[i][0]]  # Start new interval

    # Always add the last interval, even if it's a single timestamp
    if current_interval:  # As long as there's at least one timestamp
        intervals.append({
            'start': current_interval[0],
            'end': current_interval[-1],
            'duration': (datetime.datetime.fromisoformat(current_interval[-1]) -
                       datetime.datetime.fromisoformat(current_interval[0])).total_seconds(),
            'failed_pings': len(current_interval)
        })

    return intervals


print('"Boldyn Notworks" – Because nothing actually works.')
time.sleep(3)

choice = input("Enter 'j' for JSON output or any other key to start ping loop: ")

if choice.lower() == 'j':
    # Get MAC address
    mac_address = input("Enter your MAC address: ")
    interface = input("Enter your network interface: ")

    # Fetch all data
    with open('network-errors.csv') as file:
        csvreader = csv.reader(file)
        results = list(csvreader)  # Read all data at once

    # After fetching results
    intervals = group_consecutive_timestamps(results)

    f = open(f'network_errors_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w')
    f.write(json.dumps(
        [dict(**interval, mac_address=mac_address, interface=interface) for interval in intervals],
        indent=4
    ))
    f.close()
    print(f'File created: {f.name}')
else:
    print("Starting ping loop...")
    ping_google()
    print("Ping loop stopped.\n")
    # Read timestamps from CSV
    with open_file() as file:
        csvreader = csv.DictReader(file)
        results = [row['time'] for row in csvreader]

    # After fetching results
    intervals = group_consecutive_timestamps(results)
    # Print intervals in a readable format
    if intervals:
        print("\nConsecutive Failed Ping Intervals:")
        for interval in intervals:
            print(f"\nOutage from {interval['start']} to {interval['end']}")
            print(f"Duration: {interval['duration']} seconds")
            print(f"Failed pings: {interval['failed_pings']}")
    else:
        print("\nNo consecutive failed pings found.")