import os
from dotenv import load_dotenv

load_dotenv()

DASHBOARD_URL = "https://www-kiltst.wisegrid.net/Portals/TWD/Desktop#/index"

def login_if_needed(page):
  try:
    page.get_by_role("textbox", name="Username").wait_for(timeout=10000)
    user = os.getenv("CW1_USER")
    pw = os.getenv("CW1_PASS")
    page.get_by_role("textbox", name="Username").fill(user)
    page.get_by_role("textbox", name="Password").fill(pw)
    page.get_by_role("button", name="Log In").click()

    #Check for "User already logged in" window
    try:
      page.get_by_text("User already logged in").wait_for(timeout=3000)
      page.get_by_role("button", name="Yes").click()
      page.get_by_role("button", name="Log In").click()
    except Exception:
      pass

    #Wait for dashboard to load
    page.wait_for_url(DASHBOARD_URL, timeout=10000)
    page.wait_for_selector('text="Receive Consignments"', timeout=10000)

  except Exception:
    #If not found, check if already on dashboard
    if page.url.startswith(DASHBOARD_URL):
      return
    print("Login failed or dashboard didn't load.")
    page.screenshot(path="login_error.png")
    raise
