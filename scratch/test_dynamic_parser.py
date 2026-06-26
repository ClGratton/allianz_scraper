import re
from bs4 import BeautifulSoup

html = open('scratch/dashboard_page.html', encoding='utf-8', errors='ignore').read()
soup = BeautifulSoup(html, 'html.parser')

policy_info = {
    'policy_number': '6609273',
    'policy_name': 'Insieme',
    'status': 'Attiva',
    'full_name': 'CLAUDIO GRATTON',
    'agency': 'Elsa S.r.l.'
}

# 1. Parse Name
nome_input = soup.find('input', id='inputNome')
cognome_input = soup.find('input', id='inputCognome')
if nome_input and cognome_input:
    first_name = nome_input.get('value', '').strip().title()
    last_name = cognome_input.get('value', '').strip().title()
    policy_info['full_name'] = f"{first_name} {last_name}"

# 2. Parse Agency from digitalData
agency_match = re.search(r"'agenzia_riferimento'\s*:\s*'([^']+)'", html)
if agency_match:
    agency_code = agency_match.group(1)
    if 'elsa' in agency_code.lower():
        policy_info['agency'] = 'Elsa S.r.l.'
    else:
        policy_info['agency'] = agency_code.replace('_', ' ').title()

# 3. Parse Status
status_box = soup.find(class_='side-stato')
if status_box:
    status_text = status_box.get_text(separator=' ', strip=True)
    if 'attiva' in status_text.lower():
        policy_info['status'] = 'Attiva'
    else:
        policy_info['status'] = status_text

# 4. Parse Policy Name
title_box = soup.find(class_='side-title')
if title_box:
    span_el = title_box.find('span')
    if span_el:
        policy_info['policy_name'] = span_el.get_text(strip=True).title()
    else:
        policy_info['policy_name'] = title_box.get_text(strip=True).title()

print(policy_info)
