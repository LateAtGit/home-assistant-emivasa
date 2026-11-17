from datetime import datetime, timedelta
import logging
import requests

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ha_emivasa"


class EmivasaAuthError(Exception):
    """Error to indicate invalid authentication."""


class EmivasaConnectionError(Exception):
    """Error to indicate connection failure."""


class EmivasaApiClient:
    """API Client to handle Emivasa authentication and data fetching."""

    def __init__(self, username: str, password: str, hass: HomeAssistant) -> None:
        self.username = username
        self.password = password
        self.hass = hass
        self.session = requests.Session()
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    def authenticate(self) -> bool:
        """Authenticate against Emivasa Virtual Office."""
        login_url = "https://www.emivasa.es/VirtualOffice/action_Login"
        login_data = {
            "login": self.username,
            "pass": self.password,
            "remember": "true",
            "suministro": "",
            "action": "",
        }
        try:
            _LOGGER.debug("Attempting login to Emivasa for user: %s", self.username)
            response = self.session.post(login_url, data=login_data, verify=False, timeout=15)
            res_json = response.json()
            _LOGGER.debug("Login response received: %s", res_json)

            if not res_json.get("result"):
                _LOGGER.error("Authentication failed: invalid credentials or response")
                raise EmivasaAuthError("Invalid credentials")

            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise EmivasaConnectionError("Failed to connect") from err

    def fetch_daily_data(self) -> dict:
        """Fetch daily reading history from recent days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)  # Fetches last 10 days to ensure table data is populated

        start_str = start_date.strftime("%d/%m/%Y")
        end_str = end_date.strftime("%d/%m/%Y")

        historial_url = "https://www.emivasa.es/VirtualOffice/Secure/action_getHistorialLecturasWmtM"

        cookies = {
            "x_SessionId": self.session.cookies.get("x_SessionId"),
            "GO01_SessionId": self.session.cookies.get("GO01_SessionId"),
            "cc_cookie_accept": "cc_cookie_accept",
        }

        historial_data = {
            "start": start_str,
            "end": end_str,
        }

        try:
            _LOGGER.debug("Fetching historical data from %s to %s", start_str, end_str)
            response = self.session.post(historial_url, data=historial_data, cookies=cookies, verify=False, timeout=15)

            # If session expired, try re-authenticating once
            if response.status_code != 200 or not response.text:
                _LOGGER.warning("Session expired or invalid response, re-authenticating...")
                self.authenticate()
                cookies["x_SessionId"] = self.session.cookies.get("x_SessionId")
                cookies["GO01_SessionId"] = self.session.cookies.get("GO01_SessionId")
                response = self.session.post(historial_url, data=historial_data, cookies=cookies, verify=False,
                                             timeout=15)

            data = response.json()
            _LOGGER.debug("Historical data fetched successfully. Records in table: %s", len(data.get("table", [])))
            return data
        except Exception as err:
            _LOGGER.error("Error fetching historical data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err


class EmivasaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Emivasa data day-by-day."""

    def __init__(self, hass: HomeAssistant, client: EmivasaApiClient) -> None:
        """Initialize coordinator."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=4),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint day-by-day."""
        try:
            return await self.hass.async_add_executor_job(self.client.fetch_daily_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err