# FORMA SCOUT - Opponent Intelligence Platform

> **Câștigăm meciul înainte de fluierul de start**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-Web-02569B.svg?style=for-the-badge&logo=flutter&logoColor=white)
![Google Cloud Platform](https://img.shields.io/badge/GCP-BigQuery%20%7C%20Cloud%20Run-4285F4.svg?style=for-the-badge&logo=googlecloud&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28.svg?style=for-the-badge&logo=firebase&logoColor=black)

---

## 👁️ Viziune & Problemă

Analiza video tradițională (prin metode retrospective precum platforma Hudl standard) nu mai este suficientă în fotbalul modern. Aceasta ne arată *ce s-a întâmplat*, dar nu ne spune **când și cum se va repeta**. 

**FORMA SCOUT** aduce o schimbare radicală de paradigmă: o platformă de inteligență predictivă concepută exclusiv pentru analiza meticuloasă a **adversarului**. Prin fuziunea datelor de tip eveniment și a tracking-ului 360°, sistemul descoperă tipare invizibile cu ochiul liber, vulnerabilități cronice și momentele exacte în care adversarul cedează sub presiune.

---

## 🏗️ Arhitectura: Unified Data Lake

Platforma se bazează pe o arhitectură scalabilă de ingestie la nivel Enterprise (FAANG). Datele sunt centralizate și fuzionate într-un *Unified Data Lake* propulsat de **Google BigQuery**:

- **Hudl (Proprietar Superliga):** Datele meciului tratate ca evenimente primare (pase, deposedări, dueluri).
- **StatsBomb 360° (Open-Source):** Folosite pentru tracking-ul spațial avansat și calcularea automată a *Presingului Defensiv* pe baza proximității inamicilor în *freeze frames*.

Acest strat de date solid ne permite să generăm modele ML, o "Hartă de Căldură a Erorilor" direct din SQL și rapoarte de detecție în timp real.

---

## 🧩 Modulele FORMA SCOUT

| Modul | Descriere Tehnologică & Tactică |
| :--- | :--- |
| **🔮 ORACLE** | **Pattern Recognition & Passing Networks**: Scanează rețelele de pase folosind `networkx` pentru a identifica *Playmaker-ul* advers. Folosește *K-Means Clustering* pentru a detecta Formațiile Dinamice și calculează Triggerul de Presing (linia unde adversarul devine agresiv). |
| **📡 X-RAY** | **Vulnerability Mapping**: Analizează datele topografice pentru a găsi *Chronic Gaps* (spații lăsate libere) și zonele cu xT (Expected Threat) ridicat permise de adversar pe tranziția negativă. |
| **🛡️ SHIELD** | **Opponent Weakness Profiling**: Urmărește datele pentru a profila *Veriga Slabă* a adversarului - jucătorul cu cel mai mare risc de eroare analizând oboseala și cedările tehnice sub presiune. |
| **🧠 TACTICIAN**| **The Master Strategist**: Propulsat de *Gemini 2.0 Flash* într-o arhitectură Multi-Agent. Preia toate agregatele și generează "The Winning Game Plan", prezentat sub forma unor *Scouting Cards* pentru domnul antrenor Sabău. |

---

## 🛠️ Tech Stack

| Tehnologie | Utilizare în FORMA SCOUT |
| :--- | :--- |
| **FastAPI** | Backend de înaltă performanță, expune endpoint-urile analitice și rute de AI. |
| **BigQuery / SQL** | Stocare Unified Data Lake și agregări complexe de densitate a erorilor. |
| **Scikit-Learn & NetworkX** | Algoritmi de Clustering (K-Means) și Teoria Grafurilor pentru pase. |
| **Gemini 2.0 Flash** | Motorul de sinteză tactică ce generează deciziile finale NLP din date brute. |
| **Flutter Web** | Dashboard interactiv, performant, pregătit pentru tablete (*Opponent Intel Card*). |

---

## 🚀 Instalare & Rulare

### 1. Backend (Python + FastAPI)
1. Instalați dependențele din folderul de cloud:
   ```bash
   cd cloud_run
   pip install -r requirements.txt
   ```
2. Porniți serverul folosind Uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 2. Frontend (Flutter)
1. Asigurați-vă că aveți Flutter SDK instalat și canalul configurat pe web/desktop.
2. Descărcați și compilați pachetele:
   ```bash
   cd flutter_app
   flutter pub get
   ```
3. Porniți aplicația web:
   ```bash
   flutter run -d chrome
   ```

---

## 🎓 Context Hackathon

Acest proiect a fost dezvoltat cu pasiune și dedicare în cadrul evenimentului oficial:
**"U" Hack! Code in Black & White** (24-26 Aprilie 2026, Cluj-Napoca).

**Membrii Echipei:**
- **Product Manager / Tactic Analyst:** [Nume Membru]
- **Lead AI & Data Engineer:** [Nume Membru]
- **Frontend / Flutter Architect:** [Nume Membru]
- **Backend / Cloud Engineer:** [Nume Membru]

*Suntem U. Dincolo de linii.* ⚽🤍🖤
