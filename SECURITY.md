# Politica de Securitate - FORMA OS

## 🛡️ Viziunea Noastră
Securitatea datelor sportive (telemetrie biomecanică, fișe medicale și tactici de joc) este nucleul platformei FORMA OS. Am proiectat arhitectura în jurul principiilor **Zero-Trust** și **Data Isolation (B2B SaaS Multi-Tenant)**.

## 🔒 Raportarea Vulnerabilităților
Încurajăm raportarea responsabilă a oricărei breșe de securitate descoperite în sistem.

Dacă descoperi o vulnerabilitate (de exemplu, scurgeri de token-uri JWT, bypass de autorizare Firestore sau expunere a metodelor BigQuery ML), te rugăm să **NU** creezi un Issue public pe GitHub.

În schimb, contactează direct echipa tehnică:
- **Email:** security@forma-os.tech
- Vom răspunde în termen de 24 de ore cu o evaluare inițială.

## 🏗️ Măsuri de Siguranță Implementate
- **Secret Scanning Automat:** Fiecare `git commit` local este auditat cu `detect-secrets` & `trufflehog` via pre-commit hooks. Niciun string sensibil nu părăsește mașina dezvoltatorului.
- **Role-Based Access Control (RBAC):** Documentele Firestore sunt fortificate cu Firebase Custom Claims. (ex: sub-colecția `/medical_records/` necesită strict flag-ul `MEDICAL == true`).
- **Data Isolation:** Scheme de tip tenant (ex: `/tenants/u_cluj/...`) validează criptografic că analiștii nu pot accesa sub nicio formă datele echipelor rivale.
- **Circuit Breaker & Rate Limiting:** Endpoint-urile FastAPI care expun modele de Deep Learning sunt protejate anti-DDoS folosind `SlowAPI` și `Chaos Engineering` rezilient.

Vă mulțumim că ne ajutați să protejăm inovația sportivă!
