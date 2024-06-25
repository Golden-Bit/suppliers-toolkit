import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import hashlib
from jinja2 import Template
import base64
import zipfile
from io import BytesIO

# Impostare il layout wide
st.set_page_config(layout="wide")

# Funzione per controllare le credenziali
def check_credentials(username, password):
    stored_username = st.secrets["username"]
    stored_password_hash = st.secrets["password_hash"]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return username == stored_username and password_hash == stored_password_hash

# Funzione di login
def login():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if check_credentials(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()  # Rerun the script after successful login to load the main app
        else:
            st.error("Username o password errati.")

# Mostrare il modulo di login se l'utente non è autenticato
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login()
    st.stop()

# Assicurarsi che la cartella 'data' e le sottocartelle 'media' e 'documents' esistano
data_dir = 'data'
media_dir = os.path.join(data_dir, 'media')
documents_dir = os.path.join(data_dir, 'documents')
template_dir = os.path.join(data_dir, 'reports/templates')
report_dir = os.path.join(data_dir, 'reports')

os.makedirs(media_dir, exist_ok=True)
os.makedirs(documents_dir, exist_ok=True)
os.makedirs(template_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

# Creare la directory per il template HTML
template_html = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dettagli Fornitore</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f3f4f6;
            color: #333;
        }
        header {
            background-color: #333;
            color: #fff;
            text-align: center;
            padding: 1em 0;
            margin-bottom: 20px;
        }
        section {
            margin-bottom: 20px;
        }
        h1, h2, h3 {
            margin: 0 0 10px 0;
            padding: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .section-title {
            background-color: #f2f2f2;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        .note {
            font-style: italic;
            color: #555;
        }
    </style>
</head>
<body>
    <header>
        <h1>Dettagli Fornitore</h1>
    </header>
    <section>
        <div class="section-title">
            <h2>Recapiti</h2>
        </div>
        <p><strong>Nome:</strong> {{ name }}</p>
        <p><strong>Indirizzo:</strong> {{ address }}</p>
        <p><strong>Telefono:</strong> {{ phone }}</p>
        <p><strong>Email:</strong> {{ email }}</p>
        <p><strong>Sito Web:</strong> <a href="{{ website }}" target="_blank">{{ website }}</a></p>
        <p class="note"><strong>Note sui recapiti:</strong> {{ contact_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Qualità</h2>
        </div>
        <p><strong>Qualità:</strong> {{ quality }} / 5</p>
        <p class="note"><strong>Note sulla qualità:</strong> {{ quality_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Prezzo</h2>
        </div>
        <p><strong>Prezzo (in denaro):</strong> {{ price_money }} {{ currency }}</p>
        <p><strong>Prezzo (in stelle):</strong> {{ price_stars }} / 5</p>
        <p class="note"><strong>Note sul prezzo:</strong> {{ price_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Affidabilità</h2>
        </div>
        <p><strong>Affidabilità:</strong> {{ reliability }} / 5</p>
        <p class="note"><strong>Note sull'affidabilità:</strong> {{ reliability_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Consegna</h2>
        </div>
        <p><strong>Tempi di Consegna:</strong> {{ delivery_times }}</p>
        <p class="note"><strong>Note sulla consegna:</strong> {{ delivery_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Categorie</h2>
        </div>
        <p><strong>Categorie:</strong> {{ category }}</p>
        <p class="note"><strong>Note sulle categorie:</strong> {{ category_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Note Generali</h2>
        </div>
        <p class="note">{{ general_notes }}</p>
    </section>
    <section>
        <div class="section-title">
            <h2>Campi Addizionali</h2>
        </div>
        {% for field_title, field_value in additional_fields.items() %}
        <p><strong>{{ field_title }}:</strong> {{ field_value }}</p>
        {% endfor %}
    </section>
</body>
</html>
"""

# Salvare il template HTML in un file
template_path = os.path.join(template_dir, 'supplier_visualization.html')
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(template_html)

# Funzioni per gestire i fornitori
def load_suppliers(file_path=None):
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            suppliers = json.load(f)
    else:
        suppliers = st.session_state.get("suppliers", [])
    return suppliers

def save_suppliers_to_file(file_path):
    suppliers = load_suppliers()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(suppliers, f, ensure_ascii=False, indent=4)
    st.success(f"Fornitori salvati con successo in {file_path}")

def save_supplier(supplier):
    suppliers = load_suppliers()
    suppliers.append(supplier)
    st.session_state["suppliers"] = suppliers

def update_suppliers(suppliers):
    st.session_state["suppliers"] = suppliers

def reset_form():
    st.session_state.update({
        "name": "",
        "address": "",
        "phone": "",
        "contact_notes": "",
        "email": "",
        "website": "",
        "quality": 0,
        "quality_notes": "",
        "price_stars": 0,
        "price_money": 0.0,
        "price_notes": "",
        "currency": "EUR",
        "reliability": 0,
        "reliability_notes": "",
        "delivery_times_value": 0,
        "delivery_times_unit": "giorni",
        "delivery_notes": "",
        "category": [],
        "category_notes": "",
        "general_notes": "",
        "additional_fields": [],
        "media": [],
        "documents": []
    })

def add_custom_field(fields):
    fields.append({"title": "", "type": "text"})
    return fields

# Funzione per salvare i file caricati
def save_uploaded_file(uploaded_file, folder):
    folder_path = os.path.join(data_dir, folder)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Funzione per creare uno zip da un elenco di file
def create_zip(file_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    return zip_buffer

# Inizializzazione dello stato della sessione
if "suppliers" not in st.session_state:
    st.session_state.suppliers = []
if "name" not in st.session_state:
    reset_form()

# Creazione delle pagine dell'applicazione
pages = {
    "Ricerca Fornitori": "search_suppliers",
    "Ricerca Avanzata": "advanced_search",
    "Aggiungi Fornitore": "add_supplier",
    "Visualizza Fornitori": "supplier_reports",
    "Storico Fornitori": "historical_suppliers"
}
st.sidebar.title("Gestione Fornitori")
page = st.sidebar.radio("Seleziona la pagina", list(pages.keys()))

# Funzione per la pagina di ricerca fornitori
def search_suppliers():
    st.header("Ricerca Fornitori")

    search_input = st.text_input("Cerca per nome, email, categoria", key="search_input")
    category_input = st.multiselect("Seleziona una o più categorie",
                                    ["Fotovoltaico", "Solare Termico", "Plug and Play", "Smart Solutions",
                                     "Riscaldamento", "Climatizzazione", "Illuminazione", "E-Mobility",
                                     "Power Station"], key="category_input")

    if st.button("Cerca", use_container_width=True):
        filtered_suppliers = [s for s in load_suppliers() if
                              search_input.lower() in s["name"].lower() or search_input.lower() in s[
                                  "email"].lower() or any(c.lower() in s["category"] for c in category_input)]
        if category_input:
            filtered_suppliers = [s for s in filtered_suppliers if any(cat in s["category"] for cat in category_input)]

        if filtered_suppliers:
            df = pd.DataFrame(filtered_suppliers)
            st.dataframe(df)
        else:
            st.write("Nessun fornitore trovato.")

# Funzione per la pagina di ricerca avanzata
def advanced_search():
    st.header("Ricerca Avanzata Fornitori")

    filters = {
        "name": st.text_input("Nome"),
        "address": st.text_input("Indirizzo"),
        "phone": st.text_input("Telefono"),
        "email": st.text_input("Email"),
        "website": st.text_input("Sito Web")
    }

    col1, col2, col3, col4, col9 = st.columns(5)
    with col1:
        filters["quality_min"] = st.number_input("Qualità minima (da 1 a 5)", 1, 5)
    with col2:
        filters["quality_max"] = st.number_input("Qualità massima (da 1 a 5)", 1, 5)
    with col3:
        filters["price_min"] = st.number_input("Prezzo minimo (in denaro)", min_value=0.0, step=0.01)
    with col4:
        filters["price_max"] = st.number_input("Prezzo massimo (in denaro)", min_value=0.0, step=0.01)
    with col9:
        filters["price_currency"] = st.selectbox("Valuta", ["EUR", "USD", "GBP"], key="price_currency")

    col5, col6, col7, col8, col10 = st.columns(5)
    with col5:
        filters["reliability_min"] = st.number_input("Affidabilità minima (da 1 a 5)", 1, 5)
    with col6:
        filters["reliability_max"] = st.number_input("Affidabilità massima (da 1 a 5)", 1, 5)
    with col7:
        filters["delivery_times_min"] = st.number_input("Tempi di Consegna minimi (valore)", min_value=0, step=1)
    with col8:
        filters["delivery_times_max"] = st.number_input("Tempi di Consegna massimi (valore)", min_value=0, step=1)
    with col10:
        filters["delivery_unit"] = st.selectbox("Tempi di Consegna (unità di misura)",
                                                ["giorni", "settimane", "mesi", "anni"], key="delivery_unit")

    filters["category"] = st.multiselect("Categoria",
                                         ["Fotovoltaico", "Solare Termico", "Plug and Play", "Smart Solutions",
                                          "Riscaldamento", "Climatizzazione", "Illuminazione", "E-Mobility",
                                          "Power Station"])

    if st.button("Cerca", use_container_width=True):
        suppliers = load_suppliers()
        filtered_suppliers = suppliers

        if filters["name"]:
            filtered_suppliers = [s for s in filtered_suppliers if filters["name"].lower() in s["name"].lower()]
        if filters["address"]:
            filtered_suppliers = [s for s in filtered_suppliers if filters["address"].lower() in s["address"].lower()]
        if filters["phone"]:
            filtered_suppliers = [s for s in filtered_suppliers if filters["phone"].lower() in s["phone"].lower()]
        if filters["email"]:
            filtered_suppliers = [s for s in filtered_suppliers if filters["email"].lower() in s["email"].lower()]
        if filters["website"]:
            filtered_suppliers = [s for s in filtered_suppliers if filters["website"].lower() in s["website"].lower()]
        if filters["quality_min"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["quality"] >= filters["quality_min"]]
        if filters["quality_max"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["quality"] <= filters["quality_max"]]
        if filters["price_min"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["price_money"] >= filters["price_min"]]
        if filters["price_max"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["price_money"] <= filters["price_max"]]
        if filters["reliability_min"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["reliability"] >= filters["reliability_min"]]
        if filters["reliability_max"]:
            filtered_suppliers = [s for s in filtered_suppliers if s["reliability"] <= filters["reliability_max"]]
        if filters["delivery_times_min"]:
            filtered_suppliers = [s for s in filtered_suppliers if
                                  int(s["delivery_times"].split()[0]) >= filters["delivery_times_min"]]
        if filters["delivery_times_max"]:
            filtered_suppliers = [s for s in filtered_suppliers if
                                  int(s["delivery_times"].split()[0]) <= filters["delivery_times_max"]]
        if filters["category"]:
            filtered_suppliers = [s for s in filtered_suppliers if
                                  any(cat in s["category"] for cat in filters["category"])]

        if filtered_suppliers:
            df = pd.DataFrame(filtered_suppliers)
            st.dataframe(df)
        else:
            st.write("Nessun fornitore trovato con i criteri di ricerca avanzata.")

# Funzione per la pagina di aggiunta fornitori
def add_supplier():
    st.header("Aggiungi Fornitore")

    with st.form("supplier_form"):
        st.subheader("Recapiti")
        name = st.text_input("Nome")
        address = st.text_input("Indirizzo")
        phone = st.text_input("Telefono")
        email = st.text_input("Email")
        website = st.text_input("Sito Web")
        contact_notes = st.text_area("Note sui recapiti")

        st.markdown("---")

        st.subheader("Qualità")
        quality = st.number_input("Qualità (da 1 a 5)", 1, 5)
        quality_notes = st.text_area("Note sulla qualità")

        st.markdown("---")

        st.subheader("Prezzo")
        col1, col2, col3 = st.columns(3)
        with col1:
            price_money = st.number_input("Prezzo (in denaro)", min_value=0.0, step=0.01)
        with col2:
            currency = st.selectbox("Valuta", ["EUR", "USD", "GBP"])
        with col3:
            price_stars = st.number_input("Prezzo (da 1 a 5 stelle)", 1, 5)
        price_notes = st.text_area("Note sul Prezzo")

        st.markdown("---")

        st.subheader("Affidabilità")
        reliability = st.number_input("Affidabilità (da 1 a 5)", 1, 5)
        reliability_notes = st.text_area("Note sull'affidabilità")

        st.markdown("---")

        st.subheader("Consegna")
        col4, col5 = st.columns(2)
        with col4:
            delivery_times_value = st.number_input("Tempi di Consegna (valore)", min_value=0, step=1)
        with col5:
            delivery_times_unit = st.selectbox("Tempi di Consegna (unità di misura)",
                                               ["giorni", "settimane", "mesi", "anni"])
        delivery_notes = st.text_area("Note sulla consegna")

        st.markdown("---")

        st.subheader("Categorie")
        category = st.multiselect("Categoria", ["Fotovoltaico", "Solare Termico", "Plug and Play", "Smart Solutions",
                                                "Riscaldamento", "Climatizzazione", "Illuminazione", "E-Mobility",
                                                "Power Station"])
        category_notes = st.text_area("Note sulle categorie")

        st.markdown("---")

        st.subheader("Note Generali")
        general_notes = st.text_area("Note Generali")

        st.markdown("---")

        st.subheader("Campi Addizionali")
        additional_fields = st.session_state.get("additional_fields", [])

        if st.form_submit_button("Aggiungi Campo Addizionale"):
            additional_fields = add_custom_field(additional_fields)

        for idx, field in enumerate(additional_fields):
            field["title"] = st.text_input(f"Titolo Campo {idx + 1}", value=field["title"], key=f"field_title_{idx}")
            field["type"] = st.selectbox(f"Tipo Campo {idx + 1}", ["text", "number", "textarea"],
                                         index=["text", "number", "textarea"].index(field["type"]),
                                         key=f"field_type_{idx}")
            field["value"] = st.text_input(f"Valore Campo {idx + 1}", key=f"field_value_{idx}")

        st.session_state["additional_fields"] = additional_fields

        st.markdown("---")

        st.subheader("Media e Documenti")
        uploaded_media = st.file_uploader("Carica Media", accept_multiple_files=True,
                                          type=["jpg", "jpeg", "png", "mp4", "mov"])
        uploaded_documents = st.file_uploader("Carica Documenti", accept_multiple_files=True,
                                              type=["pdf", "doc", "docx", "html", "md", "mdx", "ipynb", "csv", "xlsx",
                                                    "xls"])

        st.markdown("---")

        submitted = st.form_submit_button("Salva Fornitore", use_container_width=True)

    if submitted:
        additional_data = {field["title"]: field["value"] for field in additional_fields}

        media_paths = [save_uploaded_file(file, "media") for file in uploaded_media]
        documents_paths = [save_uploaded_file(file, "documents") for file in uploaded_documents]

        new_supplier = {
            "name": name if name else "Campo non fornito",
            "address": address if address else "Campo non fornito",
            "phone": phone if phone else "Campo non fornito",
            "contact_notes": contact_notes if contact_notes else "Nessuna nota sui recapiti",
            "email": email if email else "Campo non fornito",
            "website": website if website else "Campo non fornito",
            "quality": quality,
            "quality_notes": quality_notes if quality_notes else "Nessuna nota sulla qualità",
            "price_stars": price_stars,
            "price_money": price_money,
            "currency": currency,
            "price_notes": price_notes if price_notes else "Nessuna nota sul prezzo",
            "reliability": reliability,
            "reliability_notes": reliability_notes if reliability_notes else "Nessuna nota sull'affidabilità",
            "delivery_times": f"{delivery_times_value} {delivery_times_unit}",
            "delivery_notes": delivery_notes if delivery_notes else "Nessuna nota sulla consegna",
            "category": category if category else [],
            "category_notes": category_notes if category_notes else "Nessuna nota sulle categorie",
            "general_notes": general_notes if general_notes else "Nessuna nota generale",
            "additional_fields": additional_data,
            "media": media_paths,
            "documents": documents_paths
        }

        save_supplier(new_supplier)
        st.success("Fornitore aggiunto con successo!")
        reset_form()

# Funzione per la pagina dei report fornitori
def supplier_reports():
    st.header("Visualizza Fornitori")

    suppliers = load_suppliers()
    supplier_ids = [i for i in range(len(suppliers))]

    selected_supplier_id = st.selectbox("Seleziona l'ID del fornitore", supplier_ids)

    if st.button("Visualizza Fornitore", use_container_width=True) or "last_selected_supplier" in st.session_state and st.session_state.last_selected_supplier == selected_supplier_id:
        selected_supplier = suppliers[selected_supplier_id]
        st.session_state.last_selected_supplier = selected_supplier_id

        with open(template_path, encoding='utf-8') as f:
            template = Template(f.read())
        html_content = template.render(selected_supplier)

        # Convertire il contenuto HTML in base64
        b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')

        # Visualizzare il file HTML tramite un iframe
        st.markdown(f"""
        <div style="text-align: center;">
            <iframe src="data:text/html;base64,{b64}" width="100%" height="600" id="preview-iframe" style="border: none;"></iframe>
        </div>
        """, unsafe_allow_html=True)

        # Visualizzare i media associati al fornitore in una galleria scorrevole
        if selected_supplier.get("media"):
            st.subheader("Media")
            st.markdown(
                """
                <style>
                .media-gallery {
                    display: flex;
                    overflow-x: auto;
                    white-space: nowrap;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .media-item {
                    display: inline-block;
                    margin-right: 10px;
                }
                .media-item img, .media-item video {
                    max-width: 150px;
                    max-height: 150px;
                }
                .media-item video {
                    margin-bottom: 5px;
                }
                </style>
                """, unsafe_allow_html=True
            )

            media_gallery = ""
            for media_path in selected_supplier["media"]:
                media_ext = media_path.split(".")[-1]
                if media_ext in ["jpg", "jpeg", "png", "svg", "gif", "JPG", "JPEG", "PNG", "SVG", "GIF"]:
                    with open(media_path, "rb") as file:
                        img_bytes = file.read()
                    b64_img = base64.b64encode(img_bytes).decode("utf-8")
                    media_gallery += f'<div class="media-item"><img src="data:image/{media_ext};base64,{b64_img}" alt="{media_path}"></div>'
                elif media_ext in ["mp4", "mov"]:
                    media_gallery += f'<div class="media-item"><video controls><source src="{media_path}" type="video/{media_ext}"></video></div>'
            st.markdown(f'<div class="media-gallery">{media_gallery}</div>', unsafe_allow_html=True)

        # Selezionare e scaricare media
        if selected_supplier.get("media"):
            st.subheader("Scarica Media")
            selected_media = st.multiselect("Seleziona i media da scaricare", selected_supplier["media"], key="media_multiselect")
            st.write("Media selezionati per il download:")
            st.write(selected_media)

            zip_buffer = create_zip(selected_media) if selected_media else None
            if zip_buffer:
                st.download_button(
                    label="Scarica Media Selezionati",
                    data=zip_buffer,
                    file_name="media_files.zip",
                    mime="application/zip",
                    use_container_width=True
                )

            # Pulsante per scaricare tutti i media
            all_media_zip_buffer = create_zip(selected_supplier["media"])
            st.download_button(
                label="Scarica Tutti i Media",
                data=all_media_zip_buffer,
                file_name="all_media_files.zip",
                mime="application/zip",
                use_container_width=True
            )

        # Selezionare e scaricare documenti
        if selected_supplier.get("documents"):
            st.subheader("Scarica Documenti")
            selected_documents = st.multiselect("Seleziona i documenti da scaricare", selected_supplier["documents"], key="documents_multiselect")
            st.write("Documenti selezionati per il download:")
            st.write(selected_documents)

            zip_buffer = create_zip(selected_documents) if selected_documents else None
            if zip_buffer:
                st.download_button(
                    label="Scarica Documenti Selezionati",
                    data=zip_buffer,
                    file_name="document_files.zip",
                    mime="application/zip",
                    use_container_width=True
                )

            # Pulsante per scaricare tutti i documenti
            all_documents_zip_buffer = create_zip(selected_supplier["documents"])
            st.download_button(
                label="Scarica Tutti i Documenti",
                data=all_documents_zip_buffer,
                file_name="all_document_files.zip",
                mime="application/zip",
                use_container_width=True
            )

# Funzione per la gestione dei file
def historical_suppliers():
    st.header("Storico Fornitori")

    # Caricamento fornitori
    existing_files = [f for f in os.listdir('data') if f.endswith('.json')]
    file_to_load = st.selectbox("Seleziona un file fornitori", existing_files, key="load_file_path")
    if st.button("Carica Fornitori", use_container_width=True):
        suppliers = load_suppliers(os.path.join('data', file_to_load))
        update_suppliers(suppliers)
        st.success(f"Fornitori caricati da {file_to_load}")

    # Salvataggio fornitori
    file_name = st.text_input("Nome file fornitori", key="save_file_name")
    if st.button("Salva Fornitori", use_container_width=True):
        if file_name:
            if not file_name.endswith('.json'):
                file_name += '.json'
            file_path = os.path.join('data', file_name)
            save_suppliers_to_file(file_path)
        else:
            st.error("Per favore, inserisci un nome di file valido.")

# Visualizzazione della pagina selezionata
if page == "Ricerca Fornitori":
    search_suppliers()
elif page == "Ricerca Avanzata":
    advanced_search()
elif page == "Aggiungi Fornitore":
    add_supplier()
elif page == "Visualizza Fornitori":
    supplier_reports()
elif page == "Storico Fornitori":
    historical_suppliers()
