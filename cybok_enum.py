import asyncio
import aiohttp
from aiohttp import ClientSession
import dns.asyncresolver
from queue import Queue
import json
import pyfiglet
from tabulate import tabulate
from colorama import Fore, Style, init
import time
import signal
import sys

# Initialize colorama
init()

# Tool title using pyfiglet
TOOL_NAME = "cybok_enum"
title_banner = pyfiglet.figlet_format(TOOL_NAME)
print(title_banner)
print("=" * len(max(title_banner.splitlines(), key=len)))
print(f"{Fore.YELLOW}Created by: Sathish_Cybok".center(len(max(title_banner.splitlines(), key=len))))
print(f"Version: v1.0".center(len(max(title_banner.splitlines(), key=len))))
print("=" * len(max(title_banner.splitlines(), key=len)))

# Customizable settings
CONCURRENT_REQUESTS = 50
BATCH_SIZE = 100  # Number of subdomains processed in a single batch
WORDLIST = "subdomains.txt"  # A file with common subdomain names
OUTPUT_FILE = "output.txt"
OUTPUT_FILE_JSON = "discovered_subdomains.json"

# Shared data structures
found_subdomains = set()
subdomain_queue = Queue()
detailed_results = []
interrupted = False

# Asynchronous DNS resolution
async def resolve_subdomain(subdomain, semaphore):
    """Attempt to resolve a subdomain."""
    async with semaphore:
        try:
            resolver = dns.asyncresolver.Resolver()
            answers = await resolver.resolve(subdomain, "A")
            ip = answers[0].to_text()
            return subdomain, ip
        except:
            return subdomain, None

# Get the HTTP status of a subdomain
async def fetch_status(subdomain, session, semaphore):
    """Fetch HTTP status code for a subdomain."""
    async with semaphore:
        try:
            async with session.get(f"http://{subdomain}", timeout=5) as response:
                return response.status
        except:
            return None

# Brute-force subdomains with batching
async def brute_force_subdomains(domain, session, semaphore):
    """Brute-force subdomains using a wordlist with batching."""
    tasks = []
    with open(WORDLIST, "r") as wordlist:
        for word in wordlist:
            subdomain = f"{word.strip()}.{domain}"
            if subdomain not in found_subdomains:
                tasks.append(resolve_subdomain(subdomain, semaphore))

                # Process in batches
                if len(tasks) >= BATCH_SIZE:
                    results = await asyncio.gather(*tasks)
                    tasks.clear()  # Clear the batch
                    yield results
        # Process any remaining tasks
        if tasks:
            yield await asyncio.gather(*tasks)

# Recursive subdomain discovery
async def recursive_discovery(session, semaphore):
    """Recursively discover subdomains and nested subdomains."""
    while not subdomain_queue.empty():
        base_domain = subdomain_queue.get()

        # Display header only for the root domain discovery
        if base_domain == target_domain:
            print("\n" + "=" * 88)
            print(f"{Fore.CYAN}[INFO] Discovering subdomains for: {base_domain}{Style.RESET_ALL}")
            print("=" * 88)

        # Brute-force subdomains
        async for discovered_batch in brute_force_subdomains(base_domain, session, semaphore):
            for sub, ip in discovered_batch:
                if sub not in found_subdomains and ip:
                    # Fetch HTTP status code
                    status = await fetch_status(sub, session, semaphore)
                    print(
                        f"{Fore.GREEN}[DISCOVERED] {sub} ---> [IP: {ip}] ---> [Status: {status if status else 'N/A'}]{Style.RESET_ALL}"
                    )
                    found_subdomains.add(sub)
                    detailed_results.append((sub, ip, status if status else "N/A"))
                    subdomain_queue.put(sub)  # Add subdomain to queue for nested discovery

# Save results to a text file
async def save_results():
    """Save results to a text file and JSON format."""
    # Save plain subdomains to text file
    with open(OUTPUT_FILE, "w") as f:
        for subdomain, _, _ in detailed_results:
            f.write(f"{subdomain}\n")
    print(f"{Fore.YELLOW}[SAVED] Results saved to {OUTPUT_FILE}{Style.RESET_ALL}")

    # Save detailed results to JSON
    with open(OUTPUT_FILE_JSON, "w") as f:
        json.dump(
            [{"Subdomain": sub, "IP": ip, "Status": status} for sub, ip, status in detailed_results],
            f,
            indent=4,
        )
    print(f"{Fore.YELLOW}[SAVED] Results saved to {OUTPUT_FILE_JSON}{Style.RESET_ALL}")

# Handle keyboard interruption
def handle_interrupt(signal, frame):
    global interrupted
    interrupted = True
    print(f"\n{Fore.RED}[INFO] Interrupted by user. Saving results...{Style.RESET_ALL}")
    asyncio.run(save_results())
    sys.exit(0)

# Display results in CLI format
def display_results():
    """Display results in a CLI-formatted table."""
    print("\n" + "-" * 88)
    print(f"  Discovered Subdomains: {len(detailed_results)}")
    print("-" * 88)
    print(tabulate(
        [[i, sub, ip, status] for i, (sub, ip, status) in enumerate(detailed_results, 1)],
        headers=["#", "Subdomain", "IP", "Status"],
        tablefmt="grid",
    ))
    print("-" * 88)

# Main function
async def main(domain):
    """Main function to coordinate enumeration."""
    start_time = time.time()

    # Initialize with the target domain
    found_subdomains.add(domain)
    subdomain_queue.put(domain)

    # Set up an asynchronous session
    async with ClientSession() as session:
        # Semaphore for concurrency control
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

        # Start recursive discovery
        try:
            await recursive_discovery(session, semaphore)
        except KeyboardInterrupt:
            handle_interrupt(None, None)

    # Save the results
    await save_results()

    # Display the results in the CLI format
    print(f"{Fore.MAGENTA}[SUMMARY] Results:{Style.RESET_ALL}")
    display_results()

    # Print elapsed time
    elapsed_time = time.time() - start_time
    print(f"[+] Completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    # Set up interrupt signal handler
    signal.signal(signal.SIGINT, handle_interrupt)

    # Start the tool
    target_domain = input("Enter the target domain: ").strip()
    asyncio.run(main(target_domain))
