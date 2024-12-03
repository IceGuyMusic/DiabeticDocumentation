from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import subprocess
import json
import os
import glob

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
        download_dir = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            # Öffnet die Website
            page.goto("https://de-fr.my.glooko.com/users/sign_in?locale=de", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            print("Website geöffnet.")

            # Akzeptiere Cookies (falls erforderlich)
            try:
                page.wait_for_selector("button:has-text('Allow All')", timeout=10000)
                page.evaluate("() => { const buttons = document.querySelectorAll('button'); buttons.forEach(button => { if (button.innerText.includes('Allow All')) { button.click(); } }); }")
                page.wait_for_selector("#onetrust-consent-sdk", state="detached", timeout=10000)
                print("Cookie-Banner entfernt.")
            except PlaywrightTimeoutError:
                print("Cookie-Banner nicht gefunden oder bereits akzeptiert.")
            except Exception as e:
                print(f"Fehler beim Akzeptieren der Cookies: {e}")

            # Entfernt blockierende Overlays
            try:
                page.evaluate("() => { const overlays = document.querySelectorAll('#onetrust-consent-sdk, .onetrust-pc-dark-filter'); overlays.forEach(overlay => overlay.remove()); }")
                print("Blockierende Overlays entfernt.")
            except Exception as e:
                print(f"Fehler beim Entfernen der Overlays: {e}")

            # Führt Login aus (falls erforderlich)
            page.fill("#user_email", benutzername)
            page.fill("#user_password", passwort)
            page.click("#sign-in-button") 
            page.wait_for_load_state("networkidle", timeout=60000)  # Warten auf die nächste Seite nach Login
            print("Login erfolgreich.")

            try:
                page.evaluate("() => { const overlays = document.querySelectorAll('#onetrust-consent-sdk, .onetrust-pc-dark-filter, [data-testid=\"backdrop\"], .ExportToCSVPresenter_dialog'); overlays.forEach(overlay => overlay.remove()); }")
                print("Blockierende Overlays nach Login entfernt.")
            except Exception as e:
                print(f"Fehler beim Entfernen der Overlays nach Login: {e}")

            # Navigiert zum Export-Button
            print("Navigieren zum CSV-Export.")
            page.click("text=Als CSV exportieren", timeout=30000)

            # Klick auf den Exportieren-Button per JavaScript
            page.evaluate("() => { const buttons = document.querySelectorAll('button'); buttons.forEach(button => { if (button.innerText.includes('Exportieren')) { button.click(); } }); }")
            print("Exportieren-Button per JavaScript geklickt.")

            # Entfernt blockierende Overlays vor dem Klick auf Exportieren
            try:
                page.evaluate("() => { const overlays = document.querySelectorAll('[data-testid=\"dialog-container-export-to-csv\"], [data-testid=\"backdrop\"]'); overlays.forEach(overlay => overlay.remove()); }")
                print("Blockierende Overlays vor Export entfernt.")
            except Exception as e:
                print(f"Fehler beim Entfernen der Overlays vor Export: {e}")

            # Verwenden von Download-Events
            download = page.wait_for_event('download', timeout=180000)
            print("Warten auf das Download-Event...")
            download_path = os.path.join(download_dir, download.suggested_filename)
            download.save_as(download_path)
            print(f"CSV-Download abgeschlossen: {download_path}")

        except PlaywrightTimeoutError as e:
            print(f"Ein Timeout-Fehler ist aufgetreten: {e}")
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        finally:
            # Schließt den Browser
            browser.close()

if __name__ == "__main__":
    download_csv()

