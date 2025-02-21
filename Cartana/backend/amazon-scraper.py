import requests
import os

url = 'https://www.amazon.com/Bose-QuietComfort-45-Bluetooth-Canceling-Headphones/dp/B098FKXT8L'

response = requests.get(url)

print(response.text)
print(response.status_code)

with open("amazon_page.html", "w") as f:
    f.write(response.text)