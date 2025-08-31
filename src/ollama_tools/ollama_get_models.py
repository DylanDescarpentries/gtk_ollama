#!/usr/bin/env python

from bs4 import BeautifulSoup
import requests
import json
import os

import os
import requests
import json
from bs4 import BeautifulSoup

def scrape_ollama_library():
    input_file_path = f"{os.path.expanduser('~')}/Documents/saves_ollama/ollama_models_html.txt"
    output_file_path = f"{os.path.expanduser('~')}/Documents/saves_ollama/ollama_models.json"
    url = "https://ollama.com/search"

    # Crée le dossier si nécessaire
    os.makedirs(f'{os.path.expanduser("~")}/Documents/saves_ollama/', exist_ok=True)

    # Récupération du HTML
    if os.path.exists(input_file_path):
        print("Reading from existing file...")
        with open(input_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    else:
        print("Scraping website...")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return
        content = response.text
        with open(input_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    # Parser le contenu principal
    soup = BeautifulSoup(content, 'html.parser')
    models = parse_content(soup)  # informations principales

    # Récupérer les versions pour chaque modèle
    for model in models:
        model_name = model.get('name')
        if not model_name:
            continue

        model_url = f"https://ollama.com/library/{model_name}"
        
        print(f"url models : {model_url}")
        response = requests.get(model_url)
        if response.status_code != 200:
            print(f"Failed to retrieve page for {model_name}. Status code: {response.status_code}")
            continue

        model_soup = BeautifulSoup(response.text, 'html.parser')
        versions = parse_model_versions(model_soup)  # versions du modèle
        model['versions'] = versions

    # Affichage formaté
    for model in models:
        print(f"Name: {model.get('name', 'N/A')}")
        print(f"Description: {model.get('description', 'N/A')}")
        print(f"Pulls: {model.get('pulls', 'N/A')}")
        print(f"Tags: {model.get('tags', 'N/A')}")
        print(f"Last Updated: {model.get('last_updated', 'N/A')}")
        if 'versions' in model and model['versions']:
            print("Versions:")
            for version in model['versions']:
                print(f"  - Name: {version.get('name', 'N/A')}")
                print(f"    Latest: {version.get('latest', 'N/A')}")
                print(f"    Size: {version.get('size', 'N/A')}")
                print(f"    Context: {version.get('context', 'N/A')}")
                print(f"    Input: {version.get('input', 'N/A')}")
        print("-" * 50)

    # Sauvegarder en JSON
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

def parse_model_versions(soup):
    """
    Parse the Ollama library HTML and extract model versions in a format
    similar to parse_content().
    """
    models = []

    # Desktop entries
    desktop_entries = soup.select("div.sm\\:grid")
    for entry in desktop_entries:
        model = {}

        # Name
        name_tag = entry.select_one("span.col-span-6 a")
        if name_tag:
            model['name'] = name_tag.text.strip()

        # Latest badge
        latest_tag = entry.select_one("span.ml-2")
        if latest_tag:
            model['latest'] = latest_tag.text.strip()

        # Sizes, context, input
        size_tag = entry.select_one("p.col-span-2:nth-of-type(1)")
        if size_tag:
            model['size'] = size_tag.text.strip()

        context_tag = entry.select_one("p.col-span-2:nth-of-type(2)")
        if context_tag:
            model['context'] = context_tag.text.strip()

        input_tag = entry.select_one("p.col-span-2:nth-of-type(3)")
        if input_tag:
            model['input'] = input_tag.text.strip()

        models.append(model)

    # Mobile entries
    mobile_entries = soup.select("a.sm\\:hidden")
    for entry in mobile_entries:
        model = {}

        # Name
        name_tag = entry.select_one("p.font-medium")
        if name_tag:
            model['name'] = name_tag.text.strip()

        # Info string
        info_tag = entry.select_one("p.text-neutral-500")
        if info_tag:
            parts = [p.strip() for p in info_tag.text.strip().split("·")]
            if len(parts) >= 3:
                model['size'] = parts[0]
                model['context'] = parts[1]
                model['input'] = parts[2]

        # Pas de badge latest pour mobile
        model['latest'] = None

        models.append(model)

    return models