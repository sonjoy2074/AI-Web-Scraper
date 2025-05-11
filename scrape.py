import json
import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
#"C:\Users\Sonjoy Dey\Desktop\scrapping"
# Set the correct path to your Edge WebDriver
EDGE_DRIVER_PATH = "C:\\Users\\Sonjoy Dey\\Desktop\\scrapping\\msedgedriver.exe"

def main():
    print("🚀 Starting Scraper...")
    driver = init_driver()

    print("🌍 Opening Homepage")
    url = "https://www.whed.net/home.php"
    driver.get(url)
    #time.sleep(3)

    print("📌 Gathering Countries...")    
    countries = get_countries(driver)
    driver.quit()

    print("🔍 Scraping Universities...")
    start = time.time()
    asyncio.run(fetch_all(countries))
    end = time.time()

    print(f"✅ Completed! Total Time: {round(end - start, 2)}s")

def init_driver():
    """Initialize Selenium WebDriver."""
    options = webdriver.EdgeOptions()
    options.add_argument("headless")  # Run in background
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=options)
    return driver

def get_countries(driver):
    """Extract country options from dropdown."""
    select = Select(driver.find_element(By.ID, "Chp1"))
    countries = [c.get_attribute('value') for c in select.options]
    return countries[1:]  # Remove first empty option

def extract_university_details(driver, university):
    """Extract details from a university page (General Information, Degrees, Divisions)."""
    driver.get(university['url'])
    #time.sleep(3)  # Allow the page to fully load

    # Select ONLY "Degrees" section from dropdown
    try:
        select = Select(driver.find_element(By.NAME, "ancres"))
        for option in select.options:
            if "Degrees" in option.text:
                select.select_by_visible_text(option.text)
                #time.sleep(2)
                break  # Only select the Degrees option
    except Exception as e:
        print(f"⚠️ Could not select Degrees section for {university['name']}: {e}")
        
    # Now select "General Information" section
    try:
        select = Select(driver.find_element(By.NAME, "ancres"))
        for option in select.options:
            if "General Information" in option.text:
                select.select_by_visible_text(option.text)
                #time.sleep(2)
                break
    except Exception as e:
        print(f"⚠️ Could not select General Information section for {university['name']}: {e}")

    # Extract Divisions section
    divisions = extract_divisions(driver)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    details = {}
    degrees = {}

    # Extract General Information
    for label in soup.find_all('span', class_='libelle'):
        value = label.find_next('span', class_='contenu')
        if value:
            details[label.get_text(strip=True)] = value.get_text(strip=True)

    # Extract Degrees - Filter to include only degree types
    degree_sections = soup.find_all('p', class_='principal')
    for degree in degree_sections:
        degree_name = degree.get_text(strip=True)
        
        # Skip any "Faculty" entries
        if "Faculty" in degree_name:
            continue
            
        # Only include known degree types
        degree_types = ["Bachelor", "Master", "Doctorate", "PhD", "Diploma", "Certificate", "Postgraduate",
                        "License", "Diplôme", "Doctorat", "Doctor", "Degree", "Professional" , "Associate", "Doctorate",
                        "Dyplom Bakalavra", "Dyplom Magistra", "Dyplom Doktora Filosofii", "Dyplom Doktora Nauk",
                        "Dyplom Spetsialista", "Bakalawryň diplomy", "Hünärmeniň diplomy", "Magistriň diplomy", "Mastère", "Licenciatura", 
                        "Bakalavr", "Magistr", "Doctorontura", "Yrkesexamen", "Título de Graduado", 
                        "Máster Propio", "Máster Universitario", "Título Superior de Música", "Bakalár", "Magister", "Doktor", 
                        "Doktor lekárstva/ Magister/ Inžinier", "Licenciatura", "Mestrado", "Bakalavr",

                        "Diplom Spetsialista", "Magistr", "Kandidat Nauk", "Doktor Nauk", "Inżynier", "Licencjat", "Świadectwo ukończenia studiów podyplomowych", 
                        "Licenciatura", "Especialización", "Maestría", "Bakalavriat", "Magistratura", "Doctorantura", "Gakushi",
                        "Shushi", "Hakase", "Sarjana I", "Magister", "Técnico" , "Licenciatura", "Bakalavris diploma", "Magistris diploma", 
                        "Diplôme d'ingénieur", "Mastère spécialisé", "Diplôme d'études d'école de commerce et gestion", "Licence professionnelle", 
                        "Diplôme national d'art", "Diplôme d'études en architecture", "Bakalář", "Magistr", "Doktor", "Diplôme d'Ingénieur, Graduat",
                        "Profesional Universitario", "Especialización", "Maestría", "Doctorado", "Técnico Profesional",
                        "Tecnólogo, Doctorado, Bachelier", "Doctorat en Médecine", "Mastère", "Diplôme d'Ingénieur",
                        "Bakalavr, Magistr" , "Doktor", "Bacharelado", "Licenciatura",
                        "Tecnólogo", "Especialização / Aperfeiçoamento" 
                        ]
        if not any(degree_type in degree_name for degree_type in degree_types):
            continue
            
        # Find the fields of study that follow this degree
        next_element = degree.find_next_sibling()
        
        # Look for Fields of study text in nearby elements
        if next_element and "Fields of study:" in next_element.get_text():
            fields_text = next_element.find('span', class_='contenu')
            if fields_text:
                # Extract only the fields part (remove "Fields of study:" text if present)
                fields_content = fields_text.get_text(strip=True)
                if "Fields of study:" in fields_content:
                    fields_content = fields_content.replace("Fields of study:", "")
                
                # Split by comma and clean up each field
                fields = [field.strip() for field in fields_content.split(',')]
                degrees[degree_name] = fields

    university['details'] = details
    university['degrees'] = degrees
    university['divisions'] = divisions

    # ✅ Save the results immediately into a JSON file
    with open("main1.json", "a", encoding="utf-8") as f:
        json.dump(university, f, indent=4, ensure_ascii=False)
        f.write(",\n")

    print(f"✅ Extracted: {university['name']}")

def extract_divisions(driver):
    """Extract divisions and fields of study from the 'Divisions' section."""
    divisions = {}
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Debugging: Check if we're getting the right content
    print("🔍 Extracting Divisions...")

    # Look for any <p> with class 'principal', these are the sections we're interested in
    division_sections = soup.find_all('p', class_='principal')

    if not division_sections:
        print("⚠️ No division sections found.")
    
    for division in division_sections:
        division_name = division.get_text(strip=True)
        
        # Check for any mention of "College" or "Department" in the division name
        if any(word in division_name for word in ["College", "Faculty", "Department", "Course/Programme", "School", "Area", "Campus", "College", "Institute", "Department/Division", "Research Division", "Centre", "Graduate School"]):
            print(f"🏫 Found division: {division_name}")
            
            # Extract the division name after the colon (if present)
            if ':' in division_name:
                division_name = division_name.split(':')[1].strip()
            
            next_element = division.find_next_sibling()
            
            # Look for Fields of study text in nearby elements
            if next_element and "Fields of study:" in next_element.get_text():
                fields_text = next_element.find('span', class_='contenu')
                if fields_text:
                    # Extract only the fields part (remove "Fields of study:" text if present)
                    fields_content = fields_text.get_text(strip=True)
                    if "Fields of study:" in fields_content:
                        fields_content = fields_content.replace("Fields of study:", "")
                    
                    # Split by comma and clean up each field
                    fields = [field.strip() for field in fields_content.split(',')]
                    divisions[division_name] = fields
                    print(f"🎓 Divisions {division_name} have fields: {fields}")
    
    # If no divisions were extracted, log that
    if not divisions:
        print("⚠️ No fields of study found in divisions.")

    return divisions



async def get_institutions(country, session):
    """Fetch university list for a country."""
    try:
        async with session.post(
            url="https://www.whed.net/results_institutions.php",
            data={"Chp1": country, "nbr_ref_pge": 10000}
        ) as response:
            html = await response.text()
            print(f"✅ Successfully fetched institutions for {country}")
            return extract_institutions(html, country)
    except Exception as e:
        print(f"❌ Unable to get {country} due to {e}")
        return []

def extract_institutions(html, country):
    """Extract institution details from the main search results page."""
    soup = BeautifulSoup(html, 'html.parser')
    institutions = []

    for item in soup.find_all('a', {'class': 'fancybox fancybox.iframe'}):
        institutions.append({
            "name": item.text.strip(),
            "url": "https://www.whed.net/" + item["href"].strip(),
            "country": country,
            "details": {},
            "degrees": {},
            "divisions": {}
        })

    return institutions

async def fetch_all(countries):
    """Fetch and save universities for all countries."""
    async with aiohttp.ClientSession() as session:
        institutions_by_country = await asyncio.gather(*[get_institutions(country, session) for country in countries])

    institutions = [uni for country_institutions in institutions_by_country for uni in country_institutions]

    # ✅ Start JSON file
    with open("main1.json", "w", encoding="utf-8") as f:
        f.write("[\n")

    driver = init_driver()
    for index, uni in enumerate(institutions):
        try:
            extract_university_details(driver, uni)
        except Exception as e:
            print(f"❌ Error scraping {uni['name']}: {e}")

    driver.quit()

    # ✅ Close JSON array
    with open("main1.json", "a", encoding="utf-8") as f:
        # Remove the trailing comma from the last university entry
        f.seek(f.tell() - 2, 0)  # Move back to remove trailing comma and newline
        f.truncate()  # Truncate the file at this position
        f.write("\n]")  # Close the JSON array properly

# Run the scraper
if __name__ == "__main__":
    main()