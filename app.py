import os
import csv
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key
app.config['IMAGE_FOLDER'] = os.path.join('static', 'images')

# Define the 13 fields.
FIELDS = [
    {
        "key": "date_of_photo",
        "label": "Date of Photograph (MM/YY)",
        "ai_key": "ai_guess_Date of Photograph (MM/YY)"
    },
    {
        "key": "view_of",
        "label": "View of",
        "ai_key": "ai_guess_View of"
    },
    {
        "key": "city",
        "label": "City",
        "ai_key": "ai_guess_City"
    },
    {
        "key": "country",
        "label": "Country",
        "ai_key": "ai_guess_Country"
    },
    {
        "key": "author",
        "label": "Author (Architect, Engineers, etc)",
        "ai_key": "ai_guess_Author (Architect, Engineers, etc)"
    },
    {
        "key": "object_type",
        "label": "Object Type",
        "ai_key": "ai_guess_Object Type"
    },
    {
        "key": "medium_materials",
        "label": "Medium/Materials",
        "ai_key": "ai_guess_Medium/Materials"
    },
    {
        "key": "address",
        "label": "Address",
        "ai_key": "ai_guess_Address"
    },
    {
        "key": "gps_coordinates",
        "label": "GPS Coordinates",
        "ai_key": "ai_guess_GPS Coordinates"
    },
    {
        "key": "client",
        "label": "Client",
        "ai_key": "ai_guess_Client"
    },
    {
        "key": "date_of_design",
        "label": "Date of Design",
        "ai_key": "ai_guess_Date of Design"
    },
    {
        "key": "style_period",
        "label": "Style/Period",
        "ai_key": "ai_guess_Style/Period"
    },
    {
        "key": "additional_remarks",
        "label": "Additional remarks",
        "ai_key": "ai_guess_Additional remarks"
    }
]

def get_all_prefixes():
    """
    Scan the image folder for files ending with '_slide.jpg' and ensure a corresponding
    '_sleeve.jpg' exists. Return a sorted list of base strings (e.g. "000001", "000002").
    """
    folder = app.config['IMAGE_FOLDER']
    try:
        all_files = os.listdir(folder)
    except FileNotFoundError:
        return []
    valid_prefixes = set()
    for filename in all_files:
        if filename.endswith("_slide.jpg"):
            prefix = filename.split("_")[0]
            if f"{prefix}_sleeve.jpg" in all_files:
                valid_prefixes.add(prefix)
    return sorted(list(valid_prefixes))

def load_ai_guesses():
    """
    Load the AI guess CSV (ai_guesses.csv) into a dictionary keyed by slide_filename.
    """
    ai_data = {}
    try:
        with open("ai_guesses.csv", newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                slide_filename = row.get("slide_filename")
                if slide_filename:
                    slide_filename = slide_filename.strip()  # Remove extra whitespace
                    ai_data[slide_filename] = row
                    print("DEBUG: Loaded AI guess for", slide_filename, "Row:", row)
        print("DEBUG: Total AI guess entries loaded:", len(ai_data))
    except FileNotFoundError:
        print("DEBUG: ai_guesses.csv not found")
    return ai_data

@app.route('/')
def index():
    # Redirect to the splash page if the user hasn't started a session.
    if 'username' not in session:
        return redirect(url_for('start'))
    else:
        return redirect(url_for('tag'))

@app.route('/start', methods=['GET', 'POST'])
def start():
    """
    Splash page for starting a session.
    The user enters their name, which is stored in the session.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            session['username'] = username
            session['current_index'] = 0  # Start at the first image pair.
            return redirect(url_for('tag'))
    return render_template('start.html')

@app.route('/tag', methods=['GET', 'POST'])
def tag():
    """
    Main tagging page.
    Displays the current image pair and the data entry form.
    On form submission, writes the data (including the username) to data.csv.
    """
    if 'username' not in session:
        return redirect(url_for('start'))
    all_prefixes = get_all_prefixes()
    if not all_prefixes:
        return "No image pairs found.", 404
    ai_all = load_ai_guesses()

    if request.method == 'POST':
        current_index = session.get('current_index', 0)
        # Gather the 13 user-entered field values.
        user_values = []
        for field in FIELDS:
            value = request.form.get(field["key"], "")
            user_values.append(value)

        current_pair = all_prefixes[current_index]
        slide_filename = f"{current_pair}_slide.jpg"
        sleeve_filename = f"{current_pair}_sleeve.jpg"
        username = session.get('username', '')

        print("DEBUG: Writing data.csv row with:", username, slide_filename, sleeve_filename)
        with open('data.csv', 'a', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([username, slide_filename, sleeve_filename] + user_values)

        next_index = current_index + 1
        if next_index >= len(all_prefixes):
            session.pop('current_index', None)
            return "All image pairs processed."
        session['current_index'] = next_index
        next_pair = all_prefixes[next_index]
        slide_filename = f"{next_pair}_slide.jpg"
        sleeve_filename = f"{next_pair}_sleeve.jpg"
        current_ai = ai_all.get(slide_filename, {})
        print("DEBUG: Next pair:", slide_filename, sleeve_filename, "with index:", next_index)
        return render_template('index.html',
                               slide=slide_filename,
                               sleeve=sleeve_filename,
                               current_index=next_index,
                               fields=FIELDS,
                               ai_data=current_ai)
    else:
        # GET: Start with the first image pair.
        session['current_index'] = 0
        current_index = 0
        first_pair = all_prefixes[0]
        slide_filename = f"{first_pair}_slide.jpg"
        sleeve_filename = f"{first_pair}_sleeve.jpg"
        current_ai = ai_all.get(slide_filename, {})
        print("DEBUG: Starting with:", slide_filename, sleeve_filename, "index:", current_index)
        return render_template('index.html',
                               slide=slide_filename,
                               sleeve=sleeve_filename,
                               current_index=current_index,
                               fields=FIELDS,
                               ai_data=current_ai)

if __name__ == '__main__':
    app.run(debug=False)
