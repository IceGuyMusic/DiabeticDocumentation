from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import subprocess
import json

def download_csv():
    # Sicherstellen, dass die benötigten Browser installiert sind
    try:
        subprocess.run(["playwright", "install"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei der Installation der Browser: {e}")
        return

    # Benutzername und Passwort aus einer Secret-Datei laden
    try:
        with open("secrets.json", "r") as secrets_file:
            secrets = json.load(secrets_file)
            benutzername = secrets.get("username")
            passwort = secrets.get("password")
            if not benutzername or not passwort:
                print("Benutzername oder Passwort fehlen in der secrets.json Datei.")
                return
    except FileNotFoundError:
        print("Die secrets.json Datei wurde nicht gefunden.")
        return
    except json.JSONDecodeError:
        print("Fehler beim Lesen der secrets.json Datei.")
        return

    # Startet Playwright
    with sync_playwright() as p:
        # Wählt den Browser (z. B. Chromium)
        browser = p.chromium.launch(headless=False)  # headless=True für unsichtbaren Modus
        context = browser.new_context()
        page = context.new_page()

        try:
            # Öffnet die Website
            page.goto("https://de-fr.my.glooko.com/", timeout=60000)
            print("Website geöffnet.")

            # Akzeptiere Cookies (falls erforderlich)
            try:
                page.click("text=Cookies akzeptieren", timeout=5000)
                print("Cookies akzeptiert.")
            except PlaywrightTimeoutError:
                print("Cookie-Banner nicht gefunden oder bereits akzeptiert.")

            # Führt Login aus (falls erforderlich)
            page.fill("input[name='username']", benutzername)
            page.fill("input[name='password']", passwort)
            page.click("text=Anmelden")  # Passe diesen Selektor an die Login-Schaltfläche an
            page.wait_for_navigation(timeout=60000)  # Warten auf die nächste Seite nach Login
            print("Login erfolgreich.")

            # Navigiert zum Export-Button
            print("Navigieren zum CSV-Export.")
            page.click("text=Als CSV exportieren", timeout=30000)
            page.click("text=Exportieren", timeout=30000)

            # Warten auf Download
            download = context.wait_for_event("download", timeout=60000)
            download_path = download.path()
            if download_path:
                print(f"CSV-Download abgeschlossen: {download_path}")
            else:
                print("Download fehlgeschlagen.")

        except PlaywrightTimeoutError as e:
            print(f"Ein Timeout-Fehler ist aufgetreten: {e}")
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        finally:
            # Schließt den Browser
            browser.close()

if __name__ == "__main__":
    download_csv()

