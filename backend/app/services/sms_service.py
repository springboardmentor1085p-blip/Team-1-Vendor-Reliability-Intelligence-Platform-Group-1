from abc import ABC, abstractmethod
import logging
import httpx
from app.config import settings

logger = logging.getLogger("sms_service")

class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, to_phone: str, message: str) -> bool:
        pass

class TwilioSMSProvider(SMSProvider):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_sms(self, to_phone: str, message: str) -> bool:
        try:
            # Use direct REST API call to keep dependencies minimal
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            data = {
                "To": to_phone,
                "From": self.from_number,
                "Body": message
            }
            # Twilio uses HTTP Basic Auth with Account SID and Auth Token
            auth = (self.account_sid, self.auth_token)
            
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, data=data, auth=auth)
                if resp.status_code == 201:
                    logger.info(f"SMS sent successfully to {to_phone} via Twilio")
                    return True
                else:
                    logger.error(f"Twilio API error: {resp.status_code} - {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to transmit Twilio SMS: {e}")
            return False

class MockSMSProvider(SMSProvider):
    def send_sms(self, to_phone: str, message: str) -> bool:
        logger.info(f"[SMS MOCK ALERT] Destination: {to_phone} | Message: {message}")
        return True

def get_sms_provider() -> SMSProvider:
    if (
        settings.SMS_PROVIDER == "twilio"
        and settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_PHONE_NUMBER
    ):
        return TwilioSMSProvider(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_number=settings.TWILIO_PHONE_NUMBER
        )
    else:
        logger.info("SMS provider credentials missing or inactive. Falling back to Mock SMS logger.")
        return MockSMSProvider()

def send_sms_notification(to_phone: str, message: str) -> bool:
    if not to_phone:
        logger.warning("Recipient phone number empty. Skipping SMS notification.")
        return False
    
    provider = get_sms_provider()
    return provider.send_sms(to_phone, message)
