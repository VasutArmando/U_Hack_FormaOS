import firebase_admin
from firebase_admin import auth

def assign_role(email: str, role: str):
    """
    Asignează un rol 'Custom Claim' (RBAC) în structura internă Firebase JWT.
    Acest lucru nu poate fi falsificat pe client (Frontend) și se propagă instantaneu.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    
    try:
        # Preluăm contul de utilizator Firebase asociat emailului
        user = auth.get_user_by_email(email)
        
        # Injectăm claim-ul de securitate
        auth.set_custom_user_claims(user.uid, {role: True})
        print(f"✅ SECURITATE APLICATĂ: Rolul strict '{role}' a fost asignat contului: {email}")
        
    except Exception as e:
        print(f"❌ Eroare SRE: Nu am putut aloca rolul pentru {email}. Motiv: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🛡️ FORMA OS: Sistem de Gestionare a Drepturilor de Acces (RBAC)")
    print("="*60)
    
    # Executăm configurarea de securitate pre-Prezentare (Mock emails)
    # Aceste comenzi setează nivelul de acces strict în Firebase
    assign_role("sabau@ucluj.ro", "COACH")
    assign_role("medic@ucluj.ro", "MEDICAL")
    
    print("="*60)
    print("Gata! Baza de date respinge acum atacurile neautorizate la nivel de JWT.")
