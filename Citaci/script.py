import json
import random
import requests
from datetime import datetime, timedelta
from time import sleep
import sys

# parametri 

sunday_to_start=sys.argv[1] # "2025/10/05"
num_weeks=int(sys.argv[2]) # 6


# ----------------------------
# Učitaj čitače iz JSON-a# ----------------------------
def load_readers(filename):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    return data["grupe_citaca"]

# ----------------------------
# Dohvat naziva nedjelje s CalAPI (HTTP)
# ----------------------------
def get_sunday_name(date_str, retries=3, delay=2):
    """
    Dohvati naziv nedjelje s CalAPI i prevedi na hrvatski koristeći FTAPI.
    """
    url = f"http://calapi.inadiutorium.cz/api/v0/en/calendars/default/{date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    for attempt in range(retries):
        try:
            # Dohvati naziv nedjelje s CalAPI
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if "celebrations" in data and len(data["celebrations"]) > 0:
                title_en = data["celebrations"][0]["title"]
            else:
                return None

            # Prevedi naziv na hrvatski koristeći FTAPI
            translate_url = f"https://ftapi.pythonanywhere.com/translate?sl=en&dl=hr&text={title_en}"
            translate_response = requests.get(translate_url, timeout=5)
            translate_response.raise_for_status()
            translate_data = translate_response.json()
            title_hr = translate_data.get("destination-text", title_en).replace("u uobičajenom vremenu", "kroz godinu").replace("Sve duše", "Dušni dan")
            
            return title_hr
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                sleep(delay)
            else:
                print("Failed to fetch data after retries.")
                return None

# ----------------------------
# Generiranje narednih n nedjelja i dohvat naziva
# ----------------------------
def fetch_next_sundays(start_date_str, num_weeks=6, results=None):
    if results is None:
        results = []

    if num_weeks == 0:
        return results

    start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
    if start_date.weekday() != 6:  # 6 = Sunday
        days_until_sunday = 6 - start_date.weekday()
        start_date += timedelta(days=days_until_sunday)

    date_str_api = start_date.strftime("%Y/%m/%d")
    sunday_name = get_sunday_name(date_str_api)
    results.append((start_date.strftime("%d.%m.%Y"), sunday_name))

    next_date_str = (start_date + timedelta(days=7)).strftime("%Y/%m/%d")
    return fetch_next_sundays(next_date_str, num_weeks - 1, results)

# ----------------------------
# Generiranje rasporeda čitača
# ----------------------------
def generate_schedule(sundays, readers_groups):
    # Initialize rotation pool per time slot
    rotation_pool = {time: group.copy() for time, group in readers_groups.items()}
    last_prayer = {time: None for time in readers_groups.keys()}
    schedule = []

    for date, sunday_name in sundays:
        day_schedule = {"datum": date, "nedjelja": sunday_name}
        for time, group in readers_groups.items():
            # Reset pool if not enough members left
            if len(rotation_pool[time]) < 3:
                rotation_pool[time] = group.copy()

            random.shuffle(rotation_pool[time])
            one_reading = rotation_pool[time].pop(0)
            two_reading = rotation_pool[time].pop(0)

            # Molitva vjernika
            possible_prayers = [r for r in rotation_pool[time] if r != last_prayer[time] and r not in {one_reading, two_reading}]
            if not possible_prayers:
                possible_prayers = [r for r in group if r not in {one_reading, two_reading}]
            prayer = possible_prayers[0]
            last_prayer[time] = prayer
            if prayer in rotation_pool[time]:
                rotation_pool[time].remove(prayer)

            day_schedule[time] = {"1c": one_reading, "2c": two_reading, "molitva": prayer}

        schedule.append(day_schedule)
    return schedule
# ----------------------------
# Generiranje HTML tablice
# ----------------------------
def generate_html(schedule):
    date_from = schedule[0]["datum"]
    date_to = schedule[num_weeks-1]["datum"]
    html = '<h1>RASPORED ČITAČA ZA NEDJELJE, SVETKOVINE I BLAGDANE OD ' + date_from + ' DO ' + date_to +'</h1>'
    html += '<table border="1" cellspacing="0" cellpadding="4">\n<thead>\n<tr>'
    html += "<th>Datum / Nedjelja</th><th>Misa</th><th>1. čitanje / psalam</th><th>2. čitanje</th><th>Molitva vjernika</th>"
    html += "</tr>\n</thead>\n<tbody>\n"

    for day in schedule:
        html += f'<tr><td rowspan="3">{day["datum"]}<br><small>{day["nedjelja"]}</small></td>'
        for i, time in enumerate(["9:00","10:30","19:00"]):
            if i>0:
                html += "<tr>"
            html += f'<td>{time}</td>'
            html += f'<td>{day[time]["1c"]}</td>'
            html += f'<td>{day[time]["2c"]}</td>'
            html += f'<td>{day[time]["molitva"]}</td>'
            html += "</tr>\n"
    html += "</tbody>\n</table>"
    
    return html

# ----------------------------
# Glavni program
# ----------------------------
if __name__ == "__main__":
    readers_groups = load_readers("citaci_grupe.json")

    # Generiraj narednih 6 nedjelja od zadanog datuma
    sundays = fetch_next_sundays(sunday_to_start, num_weeks=num_weeks)

    # Generiraj raspored
    schedule = generate_schedule(sundays, readers_groups)

    # Kreiraj HTML
    html_table = generate_html(schedule)
    with open("raspored.html", "w", encoding="utf-8") as f:
        f.write(html_table)

    print("Raspored generiran i spremljen u raspored.html")
