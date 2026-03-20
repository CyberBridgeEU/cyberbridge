import requests
import pathlib
from utils.file_helpers import  read_json
import argparse
import multiprocessing
from multiprocessing import cpu_count, freeze_support
import random
from bs4 import BeautifulSoup

#####  input ####
current_path = pathlib.Path(__file__).parent.resolve()
user_agents_json  = read_json(F"{current_path}/utils/desktop_agents.json")

path = 'output_bannerbuz_20230308184958.txt'
keyword_list= ["password", "database", "email", "infect", "leak", "account","hush","key","credentials","account","hush","config"
               ,"bin","logs","service","ventor",'SQL',"exploit","site","website","hidden","hack"]

# keyword_list=["password","p4ssw0rd", "p@ssw0rd", "p@$$word", "p455w0rd",
#               "email","3m@il", "e-m@il", "em4il", "em@i1",
#               "credentials","cr3d3ntial$", "cred3ntialz", "cr3ds", "cr3d5",
#               "database","d@tab@s3", "d@t@b@se", "d8tabase", "d@t@b4s3",
#               "leak", "l3ak", "l34k", "l3@k", "l3@kz"]

PROXY = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}

user_agents = user_agents_json.get("agents", [])

#####  Functions ####
# CLI Argument Parser
def parser_all():
    parser = argparse.ArgumentParser(description="Dark Web Keyword Searcher")
    parser.add_argument("--mp_units", type=int, default=0, help="Number of processing units (default: cores count - 1)")
    return parser.parse_args()

# ✅ Multiprocessing Function
def run(mp_units, func_args):
    """
    Runs multiprocessing to process search results.

    :param mp_units: Number of processing units.
    :param func_args: List of function arguments for multiprocessing.
    :return: List of all breaches found.
    """
    all_breaches = []
    print(f"🛠️ func_args being passed: {func_args}")

    # Determine the number of processing units
    units = mp_units if mp_units and mp_units > 0 else max((cpu_count() - 1), 1)

    print(f"search.py started with {units} processing units...")

    # Use 'spawn' context to avoid fork-in-thread deadlocks when
    # multiple scans run in parallel from worker threads.
    ctx = multiprocessing.get_context("spawn")
    freeze_support()

    with ctx.Pool(units) as p:
        try:
            results_list = p.starmap(search_url, func_args)

            #  Merge results properly
            for res in results_list:
                if isinstance(res, list):
                    all_breaches.extend(res)
                else:
                    print(f"Unexpected result type: {type(res)}, expected list. Skipping.")

        except Exception as e:
            print(f"❌ Error in multiprocessing: {e}")

    return all_breaches  #  Return final structured JSON

def search_url(result_entry, search, keyword_list):
    """
    Scrapes a website URL and dynamically searches for multiple keywords.
    
    :param result_entry: A dictionary from `self.results` containing {"engine": ..., "link": ...}.
    :param search: The keyword being searched.
    :param keyword_list: List of keywords to search for.
    :return: A list of dictionaries containing found keyword matches with surrounding context.
    """
    results = []
    print(f"🔍 Processing result_entry: {result_entry} (Type: {type(result_entry)})")
    
    if not isinstance(result_entry, dict):
        print(f"⚠️ Expected dictionary, but got {type(result_entry)}: {result_entry}")
        return []
    
    torurl = result_entry.get("link", "").strip()
    search_engine = result_entry.get("engine", "unknown")
    
    if not torurl.startswith("http://"):
        torurl = f"http://{torurl}"
    
    # Each process creates its own session
    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://localhost:9050',
        'https': 'socks5h://localhost:9050'
    }
    
    retries = 1  # Retry mechanism
    for attempt in range(retries):
        random_user_agent = random.choice(user_agents)
        headers = {
            "User-Agent": random_user_agent
        }
        try:
            response = session.get(torurl, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove all script and style elements and their contents
            # for script_or_style in soup(["script", "style"]):
            #     script_or_style.decompose()
            for element in soup([
                "script",        # JavaScript code
                "style",         # CSS styling
                "meta",          # Metadata
                "noscript",      # Fallback content for when JS is disabled
                "iframe",        # Embedded frames
                "object",        # Embedded objects like Flash
                "embed",         # Embedded content
                "head",          # Head section with metadata
                "header",        # Site headers often containing navigation
                "footer",        # Site footers with links/copyright
                "nav",           # Navigation menus
                "aside",         # Sidebars
                "form",          # Forms with inputs
                "button",        # Buttons
                "svg",           # Vector graphics
                "canvas",        # Drawing elements
                "link",          # External resource links
                "select",        # Dropdown menus
                "input",         # Form inputs
                "textarea",      # Text input areas
                "br",            # Line breaks that might add extra spaces
                "hr"             # Horizontal rules
            ]):
                element.decompose()
            # Get the text from the parsed HTML
            page_text = soup.get_text(separator=' ')
            
            # Clean up the text by normalizing whitespace
            import re
            page_text = re.sub(r'\s+', ' ', page_text).strip()
            
            # Create lowercase version for case-insensitive searching
            text_lower = page_text.lower()













            # page_text = response.text
            # text_lower = page_text.lower()
            
            
            print(f"✅ Successfully scraped {torurl} with User-Agent: {headers['User-Agent']}")
            break  # Exit loop if successful
        except requests.exceptions.RequestException as e:
            print(f"❌ Error scraping {torurl} (Attempt {attempt+1}/{retries}): {e}")
            continue  # Retry if failed
    else:
        print(f"🚨 Skipping {torurl} after {retries} failed attempts.")
        return []
    
    # Split the text into words for context extraction
    words = page_text.split()
    
    # For each keyword, find all occurrences and extract surrounding context
    for keyword in keyword_list:
        if keyword.lower() in text_lower:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            
            # Get all character positions of the keyword
            positions = []
            pos = 0
            while True:
                pos = text_lower.find(keyword_lower, pos)
                if pos == -1:
                    break
                positions.append(pos)
                pos += len(keyword)
            
            # Convert character positions to word positions
            word_positions = []
            for char_pos in positions:
                text_before = page_text[:char_pos]
                word_pos = len(text_before.split())
                word_positions.append(word_pos)
            
            # Group overlapping contexts
            grouped_contexts = []
            current_group = []
            
            for idx, word_pos in enumerate(word_positions):
                if not current_group:
                    current_group = [word_pos]
                elif word_pos - current_group[-1] <= 1000:  # If within 100 words of previous position
                    current_group.append(word_pos)
                else:
                    # Process the current group
                    start_word_idx = max(0, min(current_group) - 500)
                    end_word_idx = min(len(words), max(current_group) + 500)
                    context = " ".join(words[start_word_idx:end_word_idx])
                    grouped_contexts.append(context)
                    
                    # Start a new group
                    current_group = [word_pos]
            
            # Process the last group if it exists
            if current_group:
                start_word_idx = max(0, min(current_group) - 500)
                end_word_idx = min(len(words), max(current_group) + 500)
                context = " ".join(words[start_word_idx:end_word_idx])
                grouped_contexts.append(context)
            
            results.append({
                "found_link": torurl,
                "word": keyword,
                "times": count,
                "contexts": grouped_contexts  # List of merged contexts
            })
    
    return results
# ✅ Main Function to Run Search
def main(search, mp_units, results):
    """
    Main function to process search results and run keyword analysis.

    :param search: Search string.
    :param mp_units: Number of processing units.
    :param results: List of search results containing extracted links.
    :return: Processed breach results in JSON format.
    """
    print("🚀 Starting keyword analysis...")

    if not results:
        print("\nNo results exist.")
        return []

    print(f"🔎 Processing {len(results)} links...")
    keyword_list.append(search.lower())

    # Remove `session` from func_args (it’s created per process now)
    func_args = [(entry, search, keyword_list) for entry in results]

    if func_args:
        extracted_data = run(mp_units, func_args)

        # ✅ Reorder each entry to have "searched_term" first
        extracted_data = [
            {"searched_term": search, **entry} for entry in extracted_data
        ]

        return extracted_data
    else:
        print("\n⚠️ No valid URLs to process.")
        return []
