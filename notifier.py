import requests
import json

class Notifier:
    def __init__(self, api_url, scraper_key=None, ultra_msg_token=None, ultra_msg_instance=None):
        self.website_api_url = api_url.rstrip('/')
        self.scraper_key = scraper_key
        self.ultra_msg_token = ultra_msg_token
        self.ultra_msg_instance = ultra_msg_instance

    def send_whatsapp_alert(self, message):
        """
        Placeholder for UltraMsg/Twilio WhatsApp alert.
        In a real scenario, you would use requests.post to the UltraMsg API.
        """
        print(f"[WHATSAPP ALERT]: {message}")
        if self.ultra_msg_token and self.ultra_msg_instance:
            # url = f"https://api.ultramsg.com/{self.ultra_msg_instance}/messages/chat"
            # payload = {
            #     "token": self.ultra_msg_token,
            #     "to": "GROUP_ID",
            #     "body": message
            # }
            # requests.post(url, data=payload)
            pass

    def sync_to_website(self, notice_data):
        """
        Send the notice data to the website's backend SQL database via POST request.
        """
        # notice_data format: {'title': '...', 'link': '...', 'semester': '1', 'date': '...'}
        try:
            # Map category 'notifications' and semester
            url = f"{self.website_api_url}/api/sol/notifications/{notice_data['semester']}"
            
            # Add required fields for the backend schema
            payload = {
                "title": notice_data['title'],
                "link": notice_data['link'],
                "date": notice_data['date'],
                "description": notice_data.get('description', f"MBA Notification for Semester {notice_data['semester']}")
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-scraper-key": self.scraper_key
            }
            
            print(f"[WEBSITE SYNC]: Sending {notice_data['title']} (Link: {notice_data['link']})")
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                print(f"[WEBSITE SYNC][SUCCESS]: {notice_data['title']}")
                return True
            else:
                print(f"[ERROR]: Sync failed for {notice_data['title']} (Status {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR]: Sync failed: {e}")
            return False

    def update_on_website(self, semester, item_id, notice_data):
        """
        Update an existing notification (e.g., to replace a #pending link).
        """
        try:
            url = f"{self.website_api_url}/api/sol/notifications/{semester}/{item_id}"
            payload = {
                "title": notice_data['title'],
                "link": notice_data['link'],
                "date": notice_data['date'],
                "description": notice_data.get('description', f"MBA Notification for Semester {notice_data['semester']}")
            }
            headers = {
                "Content-Type": "application/json",
                "x-scraper-key": self.scraper_key
            }
            
            print(f"[WEBSITE UPDATE]: Updating ID {item_id} with new data (Link: {notice_data['link']})")
            response = requests.put(url, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"[WEBSITE UPDATE][SUCCESS]: {notice_data['title']}")
                return True
            else:
                print(f"[ERROR]: Update failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR]: Update failed: {e}")
            return False

    def delete_from_website(self, semester, item_id):
        """
        Delete a notification from the website's backend SQL database via DELETE request.
        """
        try:
            url = f"{self.website_api_url}/api/sol/notifications/{semester}/{item_id}"
            headers = {
                "x-scraper-key": self.scraper_key
            }
            
            print(f"[WEBSITE DELETE]: Deleting ID {item_id} from {url}")
            response = requests.delete(url, headers=headers)
            if response.status_code == 200:
                return True
            else:
                print(f"[ERROR]: Delete failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR]: Delete failed: {e}")
            return False

    def get_from_website(self, semester):
        """
        Fetch existing notifications for a specific semester.
        """
        try:
            url = f"{self.website_api_url}/api/sol/notifications/{semester}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            print(f"[ERROR]: Failed to fetch from website: {e}")
            return []
