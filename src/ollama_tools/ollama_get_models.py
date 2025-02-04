#!/usr/bin/env python

from bs4 import BeautifulSoup
import requests
import json
import os

def scrape_ollama_library():
    input_file_path = f"{os.path.expanduser('~')}/saves/ollama_models_html.txt"
    output_file_path = f"{os.path.expanduser('~')}/saves/ollama_models.json"

    # Create the './code/' directory if it doesn't exist
    os.makedirs(f'{os.path.expanduser('~')}/saves/', exist_ok=True)
    if os.path.exists(input_file_path):
        print("Reading from existing file...")
        print(f"fichier existant : {output_file_path}")
        with open(input_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    else:
        print("Scraping website...")
        url = "https://ollama.com/search"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return

        content = response.text

        # Save the raw HTML content to file
        with open(input_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    # Parse the content and extract information
    soup = BeautifulSoup(content, 'html.parser')
    models = parse_content(soup)
    print(models)

    # Print the extracted information
    for model in models:
        print(f"Name: {model.get('name', 'N/A')}")
        print(f"Description: {model.get('description', 'N/A')}")
        if 'sizes' in model:
            print(f"Sizes: {', '.join(model['sizes'])}")
        print(f"Pulls: {model.get('pulls', 'N/A')}")
        print(f"Tags: {model.get('tags', 'N/A')}")
        print(f"Last Updated: {model.get('last_updated', 'N/A')}")
        print("-" * 50)

    # Save the extracted information to output file as JSON
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(models, file, indent=2)

    print(f"Extracted information saved to {output_file_path}")

def parse_content(soup):
    models = []
    li_elements = soup.find_all('li', class_='flex items-baseline border-b border-neutral-200 py-6')

    for li in li_elements:
        model = {}

        # Extract name
        name_elem = li.find('h2', class_='truncate text-xl font-medium underline-offset-2 group-hover:underline md:text-2xl')
        if name_elem and name_elem.find('span'):
            model['name'] = name_elem.find('span').text.strip()

        # Extract description
        desc_elem = li.find('p', class_='max-w-lg break-words text-neutral-800 text-md')
        if desc_elem:
            model['description'] = desc_elem.text.strip()

        # Extract sizes
        sizes = []
        size_elements = li.find_all('span', class_='inline-flex items-center rounded-md bg-[#ddf4ff] px-2 py-[2px] text-xs sm:text-[13px] font-medium text-blue-600')
        for size_elem in size_elements:
            sizes.append(size_elem.text.strip())
        if sizes:
            model['sizes'] = sizes

        # Extract pulls, tags, and last updated
        stats_elem = li.find('p', class_='my-1 flex space-x-5 text-[13px] font-medium text-neutral-500')
        if stats_elem:
            pulls_elem = stats_elem.find('span', {'x-test-pull-count': True})
            if pulls_elem:
                model['pulls'] = pulls_elem.text.strip().replace(',', '')

            tags_elem = stats_elem.find('span', {'x-test-tag-count': True})
            if tags_elem:
                model['tags'] = tags_elem.text.strip()

            updated_elem = stats_elem.find('span', {'x-test-updated': True})
            if updated_elem:
                model['last_updated'] = updated_elem.text.strip()

        models.append(model)

    return models

