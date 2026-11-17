import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import requests

from .coordinator import EmivasaApiClient, EmivasaAuthError, EmivasaConnectionError

DOMAIN = "ha_emivasa"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    client = EmivasaApiClient(data["username"], data["password"], hass)
    await hass.async_add_executor_job(client.authenticate)
    return {"title": data["username"]}

class EmivasaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Emivasa."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except EmivasaAuthError:
                errors["base"] = "invalid_auth"
            except EmivasaConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )