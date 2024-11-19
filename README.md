# Cybok Enumeration

**Version:** v1.0  
**Created by:** Sathish_Cybok

## Overview
`cybok_enumuration` is an advanced subdomain enumeration tool designed for penetration testing and security analysis. It supports features like:
- Recursive subdomain discovery.
- Batch-based brute-forcing.
- HTTP status checks.
- Results export to text and JSON.

## Requirements
- Python 3.8 or higher
- Install dependencies:  
  ```bash
  pip install -r requirements.txt

Usage
Step 1: Clone the Repository

Clone the project from GitHub:
```
git clone https://github.com/cybok10/cybok_enumuration.git
cd cybok_enumuration
```
Step 2: Install Dependencies

Install the required Python libraries:
```bash
pip install -r requirements.txt
```
#Step 3: 

Run the Tool

Run the script and provide the target domain:
```bash
python cybok_enumuration.py
```
Step 4: 

Provide Input

When prompted, enter the target domain (e.g., example.com):
```
Enter the target domain: example.com
```
Step 5: Review Results
``
    The results are printed live in the terminal, showing discovered subdomains, IP addresses, and HTTP status codes.
    The results are saved to:
        output.txt: List of discovered subdomains.
        discovered_subdomains.json: Detailed results in JSON format.
