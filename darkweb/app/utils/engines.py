
import sys
import requests
import concurrent.futures


def check_status(engines, max_retries=3, retry_delay=2):
    """ 
    Check the status of search engines concurrently with retry logic.
    
    :param engines: Dictionary of search engines (name -> URL).
    :param max_retries: Maximum number of retry attempts per engine (default: 3).
    :param retry_delay: Delay in seconds between retries (default: 2).
    :return: (List of up engines, List of down engines)
    """
    import time
    
    up_engines = []
    down = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
    
    def check_engine(name, url):
        """Check a single engine's status with retry logic."""
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, proxies=proxies, headers=headers, timeout=5)
                if response.status_code == 200:
                    if attempt > 1:
                        print(f"✅ Engine '{name}' is UP (after {attempt} attempts)")
                    return name
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    print(f"⚠️ Engine '{name}' attempt {attempt}/{max_retries} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Engine '{name}' is DOWN after {max_retries} attempts")
        return None
    
    # Run checks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_engine = {executor.submit(check_engine, name, url): name for name, url in engines.items()}
        for future in concurrent.futures.as_completed(future_to_engine):
            name = future_to_engine[future]
            result = future.result()
            if result:
                up_engines.append(result)
            else:
                down.append(name)

    print(f"Up Engines: {up_engines}")
    print(f"Down Engines: {down}")

    return up_engines, down

 
def validate_engines(args, supported_engines):
    """ 
    Validate and select the engines for the search dynamically 
    handling --engines and --exclude.
    """

    #  Check if both --engines and --exclude were specified (invalid case)
    if args.engines and args.exclude:
        print("Error: You cannot specify both --engines and --exclude at the same time.")
        sys.exit(1)  # Exit the program with an error code

    #  If --engines is provided, filter only valid engines
    if args.engines:
        selected_engines = {name: supported_engines[name] for name in args.engines if name in supported_engines}
        if not selected_engines:
            print("Error: None of the provided engines are valid. Exiting.")
            sys.exit(1)  #  Exit if no valid engines are found
        #print(f"Using selected engines: {list(selected_engines.keys())}")

    #  If --exclude is provided, remove selected engines from the list
    elif args.exclude:
        excluded_engines = set(engine for sublist in args.exclude for engine in sublist)  # Handle nested lists
        selected_engines = {name: url for name, url in supported_engines.items() if name not in excluded_engines}
        print(f"Using all engines except: {excluded_engines}")

    # If no --engines or --exclude, use all available engines
    else:
        print("No engines provided. Using all available engines.")
        selected_engines = supported_engines  #  Default to all engines

    return selected_engines  #  Return final selection



def print_flag_info():
    """ Display the flag descriptions and usage instructions """
    flag_info = {
        "--proxy": "Tor proxy address. Default is 'localhost:9050'.",
        "--output": "Output file where results will be saved. Supports dynamic $SEARCH and $DATE replacements.",
        "--continuous_write": "Whether to write to the output file progressively or not.",
        "--search": "Search term or phrase to use. Default is 'bannerbuzz.com'.",
        "--limit": "Maximum number of pages per engine to load. Default is 3.",
        "--engines": "List of engines to request. Default is the full list.",
        "--exclude": "List of engines to exclude from the search.",
        "--mp_units": "Number of multiprocessing units to use. Default is system cores minus 1."
    }

    print("\nAvailable flags and instructions:")
    for flag, description in flag_info.items():
        print(f"{flag}: {description}")
    print("\n")

