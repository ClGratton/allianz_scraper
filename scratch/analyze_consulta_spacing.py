from bs4 import BeautifulSoup

html_content = open('anagrafe_consulta_correct.html', encoding='utf-8', errors='ignore').read()
soup = BeautifulSoup(html_content, 'html.parser')

# Let's find the content cell
content = soup.find('td', width='85%')
if not content:
    content = soup.find('table', class_='defaultPage')
    
if content:
    print("Printing content block structure:")
    # Print the prettified HTML of content but truncate if too long, showing structural tags
    lines = content.prettify().split('\n')
    for line in lines[:200]:
        print(line)
else:
    print("No content block found.")
