from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_submenu_items(soup, current_path):
    submenu_items = []
    menu_table = soup.find('table', id='menu')
    if not menu_table:
        print("menu_table not found!")
        return submenu_items
        
    menuhere_td = menu_table.find(id='menuhere')
    if not menuhere_td:
        print("menuhere_td not found!")
        return submenu_items
        
    active_tr = menuhere_td.find_parent('tr')
    if not active_tr:
        print("active_tr not found!")
        return submenu_items
        
    # Find the main menu item tr (the one with colspan="2" on its td)
    main_menu_tr = None
    td = active_tr.find('td')
    if td:
        print(f"td found, colspan is: {td.get('colspan')} (type: {type(td.get('colspan'))})")
    
    if td and td.get('colspan') == '2':
        main_menu_tr = active_tr
        print("main_menu_tr set to active_tr because of colspan=2")
    else:
        # Traverse backwards to find the main menu header tr
        prev = active_tr.find_previous_sibling('tr')
        while prev:
            prev_td = prev.find('td')
            if prev_td and prev_td.get('colspan') == '2':
                main_menu_tr = prev
                print("main_menu_tr set to prev tr because of colspan=2")
                break
            prev = prev.find_previous_sibling('tr')
            
    if not main_menu_tr:
        main_menu_tr = active_tr
        print("Fallback: main_menu_tr set to active_tr")
        
    # Now traverse forward from main_menu_tr to collect all sub-menu items
    for sibling in main_menu_tr.find_next_siblings('tr'):
        sib_td = sibling.find('td')
        if not sib_td:
            print("sibling tr has no td")
            continue
        print(f"Checking sibling td: colspan={sib_td.get('colspan')}, text={sib_td.get_text(strip=True)}")
        # Stop when we reach the next main menu item
        if sib_td.get('colspan') == '2':
            print("Hit next main menu item (colspan=2), stopping.")
            break
            
        a = sib_td.find('a')
        is_active_item = (sib_td.get('id') == 'menuhere') or (a and a.get('id') == 'menuhere')
        
        text = ""
        href = ""
        if a:
            href = a.get('href', '')
            text = a.get_text(strip=True)
        else:
            text = sib_td.get_text(strip=True)
            
        if text.startswith('-'):
            text = text[1:].strip()
            
        if href:
            if not href.startswith('#') and not href.startswith('javascript:') and not href.startswith('http'):
                resolved = urljoin(current_path, href)
                proxied_url = f"/proxy{resolved}"
            else:
                proxied_url = href
        else:
            proxied_url = "#"
            
        submenu_items.append({
            "text": text,
            "url": proxied_url,
            "active": is_active_item
        })
    return submenu_items

with open("anagrafe_raw.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

items = get_submenu_items(soup, "/UnifondiRASNP/priv/")
print("\n=== Resulting items ===")
print(items)
