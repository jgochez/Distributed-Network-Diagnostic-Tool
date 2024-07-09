from application_layer_services import check_ntp_server, check_dns_server, check_server_http, check_server_https
from transport_layer_services import check_tcp_port, check_udp_port
from network_layer_services import ping, traceroute
import time
import datetime
import json

"""
persistent_connection(function, *args) is the only function called from outside
which in turn calls the specific task to run indefinitely. 
Each task will return and dynamically output to its own corresponding json file titled
by the specific task's service id.
"""


def write_to_json_file(filename, results):
    try:
        # Attempt to read existing data
        with open(filename, 'r') as file:
            data_to_read = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list
        data_to_read = []

        # Append new data
    data_to_read.append(results)

    # Write updated data back to file
    with open(filename, 'w') as file:
        json.dump(data_to_read, file, indent=4)


def persistent_connection(function, service_id, frequency, pause_event, stop_event, *args):
    count = 1
    try:
        start_time = time.perf_counter()
        while not stop_event.is_set():
            if not pause_event.is_set():  # pause_event.clear()
                print(f"\n**Service ID #{service_id} has paused.\n")
                print("-" * 50)
                # .wait() -> Resumes when pause_event.set()
                pause_event.wait()
                if stop_event.is_set():  # stop_event.set()
                    break
                print(f"\n**Service ID #{service_id} has resumed.\n")

            # Execute the task function and capture its return value
            result = function(*args)

            # Include a timestamp in the result
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_with_timestamp = {"timestamp": current_time, "iteration": count, "result": result}

            # Dynamically output to a JSON file named after the service ID
            filename = f"{service_id}.json"
            write_to_json_file(filename, result_with_timestamp)

            # print(f"\n{service_id}: Task iteration count: {count}, Time: {current_time}")
            count += 1
            time.sleep(frequency)

    except KeyboardInterrupt:
        print(f"\n{service_id}: Monitoring stopped by user.")
    finally:
        end_time = time.perf_counter()
        print(f"Service ID #{service_id} has stopped:")
        print(f"    Task iteration count: {count - 1}")
        print(f"    Total monitoring lasted: {round(end_time - start_time, 2)} seconds.")

    return pause_event, stop_event


def ping_task(domain, num_pings):
    results = {}
    ping_results = ping(domain, num_pings=int(num_pings))
    domain_results = []

    for ping_addr, ping_time in ping_results:
        if ping_addr is not None and ping_time is not None:
            result = {"query": ping_addr, "time_ms": ping_time}
        else:
            result = {"error": "Request timed out or no reply received"}
        domain_results.append(result)

    results[domain] = domain_results

    return results


def traceroute_task(domain, num_query):
    results = {}
    traceroute_results = traceroute(domain, num_query_packets=int(num_query))
    results[domain] = traceroute_results

    return results


def http_task(domain):
    results = {}
    status, code = check_server_http(domain)
    results[domain] = {"status": status, "code": code}

    return results


def https_task(domain):
    results = {}
    status, code, description = check_server_https(domain)
    results[domain] = {"status": status, "code": code, "description": description}

    return results


def ntp_task(server):
    results = {}
    status, time = check_ntp_server(server)
    results[server] = {"status": status, "time": time}

    return results


def dns_task(domain, server, record_type):
    results = {}
    status, query_results = check_dns_server(server, domain, record_type)
    results[f"{domain}_{server}_{record_type}"] = {"status": status, "query_results": query_results}

    return results


def tcp_task(domain, port):
    results = {}
    status, description = check_tcp_port(domain, int(port))
    results[domain] = {"port": port, "status": status, "description": description}

    return results


def udp_task(domain, port):
    results = {}
    status, description = check_udp_port(domain, int(port))
    results[domain] = {"port": port, "status": status, "description": description}

    return results
