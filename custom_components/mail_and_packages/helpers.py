"""Helper functions for Mail and Packages."""

import datetime
import email
import hashlib
import imaplib
import locale
import logging
import os
import quopri
import re
import unicodedata
import uuid
from datetime import timezone
from email.header import decode_header
from shutil import copyfile, copytree, which
from typing import Any, List, Optional, Type, Union
from urllib.parse import quote
from urllib.request import Request, urlopen


import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RESOURCES,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from .const import (
    AMAZON_DELIVERED,
    AMAZON_DELIVERED_SUBJECT,
    AMAZON_EMAIL,
    AMAZON_EXCEPTION,
    AMAZON_EXCEPTION_ORDER,
    AMAZON_EXCEPTION_SUBJECT,
    AMAZON_HUB,
    AMAZON_HUB_BODY,
    AMAZON_HUB_CODE,
    AMAZON_HUB_EMAIL,
    AMAZON_HUB_SUBJECT,
    AMAZON_HUB_SUBJECT_SEARCH,
    AMAZON_IMG_PATTERN,
    AMAZON_LANGS,
    AMAZON_ORDER,
    AMAZON_PACKAGES,
    AMAZON_PATTERN,
    AMAZON_TIME_PATTERN,
    ATTR_AMAZON_IMAGE,
    ATTR_BODY,
    ATTR_CODE,
    ATTR_COUNT,
    ATTR_EMAIL,
    ATTR_IMAGE_PATH,
    ATTR_ORDER,
    ATTR_PATTERN,
    ATTR_SUBJECT,
    ATTR_TRACKING,
    CONF_ALLOW_EXTERNAL,
    CONF_AMAZON_DAYS,
    CONF_AMAZON_FWDS,
    CONF_CORREOS_CODES,
    CONF_CUSTOM_IMG,
    CONF_CUSTOM_IMG_FILE,
    CONF_FOLDER,
    CONF_PATH,
    DEFAULT_AMAZON_DAYS,
    SENSOR_DATA,
    SENSOR_TYPES,
    SHIPPERS,
)

_LOGGER = logging.getLogger(__name__)


def get_resources() -> dict:
    """Resource selection schema.

    Returns dict of user selected sensors
    """
    known_available_resources = {
        sensor_id: sensor.name for sensor_id, sensor in SENSOR_TYPES.items()
    }
    return known_available_resources


async def _check_ffmpeg() -> bool:
    """Check if ffmpeg is installed.

    Returns boolean
    """
    return which("ffmpeg")


async def _test_login(host: str, port: int, user: str, pwd: str) -> bool:
    """Test IMAP login to specified server.

    Returns success boolean
    """
    try:
        account = imaplib.IMAP4_SSL(host, port)
    except Exception as err:
        _LOGGER.error("Error connecting into IMAP Server: %s", str(err))
        return False

    try:
        account.login(user, pwd)
        return True
    except Exception as err:
        _LOGGER.error("Error logging into IMAP Server: %s", str(err))
        return False


def default_image_path(
    hass: HomeAssistant, config_entry: ConfigEntry  # pylint: disable=unused-argument
) -> str:
    """Return value of the default image path."""
    return "custom_components/mail_and_packages/images/"

def _get_manual_correos_codes(hass: HomeAssistant, config: ConfigEntry) -> list:
    """Get manual Correos tracking codes from config and helper."""
    codes = []

    # Codes from integration config
    config_codes = config.get(CONF_CORREOS_CODES, [])
    if isinstance(config_codes, list):
        for code in config_codes:
            code = str(code).strip()
            if code and code not in codes:
                codes.append(code)

    # Codes from input_text helper
    helper = hass.states.get("input_text.correos_tracking")
    if helper is not None:
        helper_value = helper.state
        if helper_value not in [None, "", "unknown", "unavailable"]:
            helper_codes = [x.strip() for x in helper_value.split(",") if x.strip()]
            for code in helper_codes:
                if code not in codes:
                    codes.append(code)

    return codes

def _strip_accents(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    )


def _normalize_correos_status(text: str) -> str:
    if not text:
        return "unknown"

    status = _strip_accents(text).strip().lower()

    if "entregado" in status:
        return "delivered"

    if "en reparto" in status or "en entrega" in status:
        return "delivering"

    if (
        "en transito" in status
        or "en camino" in status
        or "admitido" in status
        or "clasificado" in status
    ):
        return "in_transit"

    return "unknown"


def get_correos_tracking_data(codes: list) -> dict:
    """Fetch Correos tracking data for manually entered tracking codes."""
    result = {
        "correos_packages": 0,
        "correos_delivering": 0,
        "correos_delivered": 0,
        "correos_tracking": [],
        "correos_details": [],
    }

    if not codes:
        return result

    for code in codes:
        normalized_status = "unknown"
        raw_status = ""
        detail = {"code": code, "status": "unknown"}

        try:
            url = (
                "https://www.correos.es/es/es/herramientas/localizador/envios?numero="
                f"{quote(code)}"
            )
            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                },
            )

            with urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8", "ignore")

            text = " ".join(html.split())
            text_normalized = _strip_accents(text).lower()

            if "entregado" in text_normalized:
                raw_status = "entregado"
            elif "en reparto" in text_normalized:
                raw_status = "en reparto"
            elif "en entrega" in text_normalized:
                raw_status = "en entrega"
            elif "en transito" in text_normalized:
                raw_status = "en transito"
            elif "en camino" in text_normalized:
                raw_status = "en camino"
            elif "admitido" in text_normalized:
                raw_status = "admitido"
            elif "clasificado" in text_normalized:
                raw_status = "clasificado"
            else:
                raw_status = text_normalized[:300]

            normalized_status = _normalize_correos_status(raw_status)

            _LOGGER.debug("Correos raw status for %s: %s", code, raw_status)
            _LOGGER.debug(
                "Correos normalized status for %s: %s", code, normalized_status
            )

            detail["status"] = normalized_status

            if normalized_status == "delivered":
                result["correos_delivered"] += 1

            elif normalized_status == "delivering":
                result["correos_delivering"] += 1

            elif normalized_status == "in_transit":
                result["correos_delivering"] += 1

            else:
                _LOGGER.debug("Correos status for %s not recognized", code)

        except Exception as err:
            _LOGGER.debug("Correos tracking lookup failed for %s: %s", code, err)

        result["correos_tracking"].append(code)
        result["correos_details"].append(detail)

    result["correos_packages"] = (
        result["correos_delivering"] + result["correos_delivered"]
    )

    return result
    

def process_emails(hass: HomeAssistant, config: ConfigEntry) -> dict:
    """Process emails and return value.

    Returns dict containing sensor data
    """
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    user = config.get(CONF_USERNAME)
    pwd = config.get(CONF_PASSWORD)
    folder = config.get(CONF_FOLDER)
    resources = config.get(CONF_RESOURCES)

    # Manual Correos codes from config + helper
    correos_codes = _get_manual_correos_codes(hass, config)

    # Create the dict container
    data = {}

    account = login(host, port, user, pwd)
    if not account:
        return data

    if not selectfolder(account, folder):
        return data

    amazon_image_name = image_file_name(hass, config, amazon=True)
    _LOGGER.debug("Amazon Image Name: %s", amazon_image_name)

    image_path = config.get(CONF_PATH)
    _LOGGER.debug("Image path: %s", image_path)

    data.update(
        {
            ATTR_AMAZON_IMAGE: amazon_image_name,
            ATTR_IMAGE_PATH: image_path,
        }
    )

    _LOGGER.debug("Configured manual Correos codes: %s", correos_codes)

    if correos_codes:
        correos_info = get_correos_tracking_data(correos_codes)
        data.update(correos_info)
        _LOGGER.debug("Manual Correos tracking data: %s", correos_info)
    
    for sensor in resources:
        fetch(hass, config, account, data, sensor)

    if config.get(CONF_ALLOW_EXTERNAL):
        copy_images(hass, config)

    return data


def copy_images(hass: HomeAssistant, config: ConfigEntry) -> None:
    """Copy images to www directory if enabled."""
    src = f"{hass.config.path()}/{config.get(CONF_PATH)}"
    dst = f"{hass.config.path()}/www/mail_and_packages/"
    amazon_dst = f"{dst}amazon/"

    for path in [dst, amazon_dst]:
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as err:
                _LOGGER.error("Problem creating: %s, error returned: %s", path, err)
                return

    try:
        copytree(src, dst, dirs_exist_ok=True)
    except Exception as err:
        _LOGGER.error(
            "Problem copying files from %s to %s error returned: %s", src, dst, err
        )


def image_file_name(
    hass: HomeAssistant, config: ConfigEntry, amazon: bool = False
) -> str:
    """Determine image filename.

    Returns filename
    """
    if amazon:
        placeholder = f"{os.path.dirname(__file__)}/no_deliveries.jpg"
        image_name = "no_deliveries.jpg"
        path = f"{hass.config.path()}/{config.get(CONF_PATH)}amazon/"
        ext = ".jpg"
    else:
        path = f"{hass.config.path()}/{config.get(CONF_PATH)}"
        if config.get(CONF_CUSTOM_IMG):
            placeholder = config.get(CONF_CUSTOM_IMG_FILE)
        else:
            placeholder = f"{os.path.dirname(__file__)}/mail_none.gif"
        image_name = os.path.split(placeholder)[1]
        ext = ".gif"

    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as err:
            _LOGGER.error("Problem creating: %s, error returned: %s", path, err)
            return image_name

    try:
        sha1 = hash_file(placeholder)
    except OSError as err:
        _LOGGER.error(
            "Problem accessing file: %s, error returned: %s", placeholder, err
        )
        return image_name

    for file in os.listdir(path):
        if file.endswith(ext):
            try:
                created = datetime.datetime.fromtimestamp(
                    os.path.getctime(os.path.join(path, file))
                ).strftime("%d-%b-%Y")
            except OSError as err:
                _LOGGER.error(
                    "Problem accessing file: %s, error returned: %s", file, err
                )
                return image_name

            today = get_formatted_date()
            if sha1 != hash_file(os.path.join(path, file)) and today != created:
                image_name = f"{str(uuid.uuid4())}{ext}"
            else:
                image_name = file

    if image_name in placeholder:
        image_name = f"{str(uuid.uuid4())}{ext}"

    copyfile(placeholder, os.path.join(path, image_name))
    return image_name


def hash_file(filename: str) -> str:
    """Return the SHA-1 hash of the file passed into it."""
    the_hash = hashlib.sha1()  # nosec

    with open(filename, "rb") as file:
        chunk = b"1"
        while chunk != b"":
            chunk = file.read(1024)
            the_hash.update(chunk)

    return the_hash.hexdigest()


def fetch(
    hass: HomeAssistant, config: ConfigEntry, account: Any, data: dict, sensor: str
) -> int:
    """Fetch data for a single sensor, including any sensors it depends on.

    Returns integer of sensor passed to it
    """
    img_out_path = f"{hass.config.path()}/{config.get(CONF_PATH)}"
    amazon_fwds = config.get(CONF_AMAZON_FWDS)
    amazon_image_name = data.get(ATTR_AMAZON_IMAGE)
    amazon_days = config.get(CONF_AMAZON_DAYS)

    if sensor in data:
        return data[sensor]

    count = {}

    if sensor == AMAZON_PACKAGES:
        count[sensor] = get_items(
            account=account,
            param=ATTR_COUNT,
            fwds=amazon_fwds,
            days=amazon_days,
        )
        count[AMAZON_ORDER] = get_items(
            account=account,
            param=ATTR_ORDER,
            fwds=amazon_fwds,
            days=amazon_days,
        )

    elif sensor == AMAZON_HUB:
        value = amazon_hub(account, amazon_fwds)
        count[sensor] = value.get(ATTR_COUNT, 0)
        count[AMAZON_HUB_CODE] = value.get(ATTR_CODE, [])

    elif sensor == AMAZON_EXCEPTION:
        info = amazon_exception(account, amazon_fwds)
        count[sensor] = info.get(ATTR_COUNT, 0)
        count[AMAZON_EXCEPTION_ORDER] = info.get(ATTR_ORDER, [])

    elif sensor.endswith("_packages"):
        prefix = sensor.replace("_packages", "")
        delivering = fetch(hass, config, account, data, f"{prefix}_delivering")
        delivered = fetch(hass, config, account, data, f"{prefix}_delivered")
        count[sensor] = delivering + delivered

    elif sensor.endswith("_delivering"):
        prefix = sensor.replace("_delivering", "")
        delivered = fetch(hass, config, account, data, f"{prefix}_delivered")
        info = get_count(account, sensor, True)
        count[sensor] = max(0, info[ATTR_COUNT] - delivered)
        count[f"{prefix}_tracking"] = info[ATTR_TRACKING]

    elif sensor == "zpackages_delivered":
        total = 0
        for shipper in SHIPPERS:
            delivered = f"{shipper}_delivered"
            total += fetch(hass, config, account, data, delivered)
        count[sensor] = total

    elif sensor == "zpackages_transit":
        total = 0
        for shipper in SHIPPERS:
            delivering = f"{shipper}_delivering"
            total += fetch(hass, config, account, data, delivering)
        count[sensor] = max(0, total)

    elif sensor == "mail_updated":
        count[sensor] = update_time()

    else:
        count[sensor] = get_count(
            account, sensor, False, img_out_path, hass, amazon_image_name
        )[ATTR_COUNT]

    data.update(count)
    _LOGGER.debug("Sensor: %s Count: %s", sensor, str(count[sensor]))
    return count[sensor]


def login(
    host: str, port: int, user: str, pwd: str
) -> Union[bool, Type[imaplib.IMAP4_SSL]]:
    """Login to IMAP server.

    Returns account object
    """
    try:
        account = imaplib.IMAP4_SSL(host, port)
    except Exception as err:
        _LOGGER.error("Network error while connecting to server: %s", str(err))
        return False

    try:
        account.login(user, pwd)
    except Exception as err:
        _LOGGER.error("Error logging into IMAP Server: %s", str(err))
        return False

    return account


def selectfolder(account: Type[imaplib.IMAP4_SSL], folder: str) -> bool:
    """Select folder inside the mailbox."""
    try:
        account.list()
    except Exception as err:
        _LOGGER.error("Error listing folders: %s", str(err))
        return False
    try:
        account.select(folder)
    except Exception as err:
        _LOGGER.error("Error selecting folder: %s", str(err))
        return False
    return True


def get_formatted_date() -> str:
    """Return today in specific format."""
    return datetime.datetime.today().strftime("%d-%b-%Y")


def update_time() -> Any:
    """Get update time."""
    return datetime.datetime.now(timezone.utc)


def build_search(address: list, date: str, subject: str = None) -> tuple:
    """Build IMAP search query.

    Return tuple of utf8 flag and search query.
    """
    the_date = f"SINCE {date}"
    utf8_flag = False
    prefix_list = None

    if isinstance(address, list):
        if len(address) == 1:
            email_list = address[0]
        else:
            email_list = '" FROM "'.join(address)
            prefix_list = " ".join(["OR"] * (len(address) - 1))
    else:
        email_list = address

    if subject is not None:
        if not subject.isascii():
            utf8_flag = True
            imap_search = f"{the_date} SUBJECT"
        else:
            if prefix_list is not None:
                imap_search = (
                    f'({prefix_list} FROM "{email_list}" SUBJECT "{subject}" {the_date})'
                )
            else:
                imap_search = f'(FROM "{email_list}" SUBJECT "{subject}" {the_date})'
    else:
        if prefix_list is not None:
            imap_search = f'({prefix_list} FROM "{email_list}" {the_date})'
        else:
            imap_search = f'(FROM "{email_list}" {the_date})'

    return (utf8_flag, imap_search)


def email_search(
    account: Type[imaplib.IMAP4_SSL], address: list, date: str, subject: str = None
) -> tuple:
    """Search emails with from, subject, senton date.

    Returns a tuple
    """
    utf8_flag, search = build_search(address, date, subject)

    if utf8_flag:
        subject = subject.encode("utf-8")
        account.literal = subject
        try:
            value = account.uid("SEARCH", "CHARSET", "UTF-8", search)
        except Exception as err:
            _LOGGER.warning(
                "Error searching emails with unicode characters: %s", str(err)
            )
            value = "BAD", err.args[0]
    else:
        try:
            value = account.search(None, search)
        except Exception as err:
            _LOGGER.error("Error searching emails: %s", str(err))
            value = "BAD", err.args[0]

    (check, new_value) = value
    if new_value and new_value[0] is None:
        value = (check, [b""])
    return value


def email_fetch(
    account: Type[imaplib.IMAP4_SSL], num: int, parts: str = "(RFC822)"
) -> tuple:
    """Download specified email for parsing.

    Returns tuple
    """
    try:
        value = account.fetch(num, parts)
    except Exception as err:
        _LOGGER.error("Error fetching emails: %s", str(err))
        value = "BAD", err.args[0]

    return value


def cleanup_images(path: str, image: Optional[str] = None) -> None:
    """Clean up image storage directory."""
    if image is not None:
        try:
            os.remove(path + image)
        except Exception as err:
            _LOGGER.error("Error attempting to remove image: %s", str(err))
        return

    for file in os.listdir(path):
        if file.endswith(".gif") or file.endswith(".mp4") or file.endswith(".jpg"):
            try:
                os.remove(path + file)
            except Exception as err:
                _LOGGER.error("Error attempting to remove found image: %s", str(err))


def get_count(
    account: Type[imaplib.IMAP4_SSL],
    sensor_type: str,
    get_tracking_num: bool = False,
    image_path: Optional[str] = None,
    hass: Optional[HomeAssistant] = None,
    amazon_image_name: Optional[str] = None,
) -> dict:
    """Get Package Count.

    Returns dict of sensor data
    """
    count = 0
    tracking = []
    result = {}
    today = get_formatted_date()
    track = None
    found = []

    if sensor_type == AMAZON_DELIVERED:
        result[ATTR_COUNT] = amazon_search(account, image_path, hass, amazon_image_name)
        result[ATTR_TRACKING] = []
        return result

    if sensor_type not in SENSOR_DATA or ATTR_EMAIL not in SENSOR_DATA[sensor_type]:
        _LOGGER.debug("Unknown sensor type: %s", str(sensor_type))
        result[ATTR_COUNT] = 0
        result[ATTR_TRACKING] = []
        return result

    email_addresses = SENSOR_DATA[sensor_type][ATTR_EMAIL]
    subjects = SENSOR_DATA[sensor_type].get(ATTR_SUBJECT, [])

    if not subjects:
        _LOGGER.debug(
            "Attempting to find mail from (%s) without subject filter",
            email_addresses,
        )
        (server_response, data) = email_search(account, email_addresses, today)

        if server_response == "OK" and data[0] is not None:
            if ATTR_BODY in SENSOR_DATA[sensor_type] and SENSOR_DATA[sensor_type][ATTR_BODY]:
                total_body_matches = 0
                for body_search in SENSOR_DATA[sensor_type][ATTR_BODY]:
                    total_body_matches += find_text(data, account, body_search)
                count += total_body_matches
            else:
                count += len(data[0].split())

            found.append(data[0])

    else:
        for subject in subjects:
            _LOGGER.debug(
                "Attempting to find mail from (%s) with subject (%s)",
                email_addresses,
                subject,
            )

            (server_response, data) = email_search(
                account, email_addresses, today, subject
            )

            if server_response == "OK" and data[0] is not None:
                if ATTR_BODY in SENSOR_DATA[sensor_type] and SENSOR_DATA[sensor_type][ATTR_BODY]:
                    total_body_matches = 0
                    for body_search in SENSOR_DATA[sensor_type][ATTR_BODY]:
                        total_body_matches += find_text(data, account, body_search)
                    count += total_body_matches
                else:
                    count += len(data[0].split())

                found.append(data[0])

    tracking_key = f"{'_'.join(sensor_type.split('_')[:-1])}_tracking"
    if (
        tracking_key in SENSOR_DATA
        and ATTR_PATTERN in SENSOR_DATA[tracking_key]
        and SENSOR_DATA[tracking_key][ATTR_PATTERN]
    ):
        track = SENSOR_DATA[tracking_key][ATTR_PATTERN][0]

    if track is not None and get_tracking_num and count > 0:
        for sdata in found:
            tracking.extend(get_tracking(sdata, account, track))
        tracking = list(dict.fromkeys(tracking))

    if len(tracking) > 0:
        count = len(tracking)

    result[ATTR_TRACKING] = tracking
    result[ATTR_COUNT] = count
    return result


def get_tracking(
    sdata: Any, account: Type[imaplib.IMAP4_SSL], the_format: Optional[str] = None
) -> list:
    """Parse tracking numbers from email.

    Returns list of tracking numbers
    """
    tracking = []
    mail_list = sdata.split()

    pattern = re.compile(rf"{the_format}")

    for i in mail_list:
        data = email_fetch(account, i, "(RFC822)")[1]
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                email_subject = msg["subject"] or ""
                if (found := pattern.findall(email_subject)) and len(found) > 0:
                    if found[0] not in tracking:
                        tracking.append(found[0])
                    continue

                for part in msg.walk():
                    if part.get_content_type() not in ["text/html", "text/plain"]:
                        continue

                    email_msg = part.get_payload(decode=True)
                    if email_msg is None:
                        continue

                    email_msg = email_msg.decode("utf-8", "ignore")
                    if (found := pattern.findall(email_msg)) and len(found) > 0:
                        if found[0] not in tracking:
                            tracking.append(found[0])
                        continue

    return tracking


def find_text(sdata: Any, account: Type[imaplib.IMAP4_SSL], search: str) -> int:
    """Filter for specific words in email.

    Return count of items found as integer
    """
    mail_list = sdata[0].split()
    count = 0

    for i in mail_list:
        data = email_fetch(account, i, "(RFC822)")[1]
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                for part in msg.walk():
                    if part.get_content_type() not in ["text/html", "text/plain"]:
                        continue

                    email_msg = part.get_payload(decode=True)
                    if email_msg is None:
                        continue

                    email_msg = email_msg.decode("utf-8", "ignore")
                    pattern = re.compile(rf"{search}")
                    found = pattern.findall(email_msg)
                    if found:
                        count += len(found)

    return count


def amazon_search(
    account: Type[imaplib.IMAP4_SSL],
    image_path: str,
    hass: HomeAssistant,
    amazon_image_name: str,
) -> int:
    """Find Amazon Delivered email.

    Returns email found count as integer
    """
    subjects = AMAZON_DELIVERED_SUBJECT
    today = get_formatted_date()
    found_ids = []

    for email_address in AMAZON_EMAIL:
        for subject in subjects:
            (server_response, data) = email_search(
                account, [email_address], today, subject
            )

            if server_response == "OK" and data[0] is not None:
                ids = data[0].split()
                for msg_id in ids:
                    if msg_id not in found_ids:
                        found_ids.append(msg_id)

    if found_ids:
        get_amazon_image(
            b" ".join(found_ids), account, image_path, hass, amazon_image_name
        )

    return len(found_ids)


def get_amazon_image(
    sdata: Any,
    account: Type[imaplib.IMAP4_SSL],
    image_path: str,
    hass: HomeAssistant,
    image_name: str,
) -> None:
    """Find Amazon delivery image."""
    img_url = None
    mail_list = sdata.split()

    for i in mail_list:
        data = email_fetch(account, i, "(RFC822)")[1]
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                for part in msg.walk():
                    if part.get_content_type() != "text/html":
                        continue

                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue

                    html = payload.decode("utf-8", "ignore")
                    pattern = re.compile(rf"{AMAZON_IMG_PATTERN}")
                    found = pattern.findall(html)

                    for url in found:
                        full_url = url[0] + url[1] + url[2]
                        if "amazon" not in url[1] and "images" not in url[1]:
                            continue
                        img_url = full_url
                        break

    if img_url is not None:
        hass.add_job(download_img(img_url, image_path, image_name))


async def download_img(img_url: str, img_path: str, img_name: str) -> None:
    """Download image from url."""
    img_path = f"{img_path}amazon/"
    filepath = f"{img_path}{img_name}"

    async with aiohttp.ClientSession() as session:
        async with session.get(img_url.replace("&amp;", "&")) as resp:
            if resp.status != 200:
                _LOGGER.error("Problem downloading file http error: %s", resp.status)
                return

            content_type = resp.headers.get("content-type", "")
            if "image" not in content_type:
                return

            data = await resp.read()
            with open(filepath, "wb") as the_file:
                the_file.write(data)


def _process_amazon_forwards(email_list: Union[List[str], None]) -> list:
    """Process amazon forward emails.

    Returns list of email addresses
    """
    result = []
    if email_list:
        for fwd in email_list:
            if fwd and fwd != '""' and fwd not in result:
                result.append(fwd)
    return result


def _get_sender_list(base_senders: list, fwds: Optional[list] = None) -> list:
    """Combine base senders and forwarded senders into a unique list."""
    result = []

    for sender in base_senders:
        if sender and sender not in result:
            result.append(sender)

    if fwds:
        for sender in fwds:
            if sender and sender != '""' and sender not in result:
                result.append(sender)

    return result


def amazon_hub(account: Type[imaplib.IMAP4_SSL], fwds: Optional[str] = None) -> dict:
    """Find Amazon Hub info emails.

    Returns dict of sensor data
    """
    body_regex = AMAZON_HUB_BODY
    subject_regex = AMAZON_HUB_SUBJECT_SEARCH
    info = {}
    found = []
    today = get_formatted_date()

    forward_list = _process_amazon_forwards(fwds)
    email_addresses = _get_sender_list(AMAZON_HUB_EMAIL, forward_list)

    for address in email_addresses:
        (server_response, sdata) = email_search(
            account, [address], today, subject=AMAZON_HUB_SUBJECT
        )

        if server_response != "OK" or sdata[0] is None:
            continue

        id_list = sdata[0].split()
        for i in id_list:
            data = email_fetch(account, i, "(RFC822)")[1]
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    email_subject = msg["subject"] or ""
                    pattern = re.compile(rf"{subject_regex}")
                    search = pattern.search(email_subject)
                    if search is not None and len(search.groups()) > 1:
                        found.append(search.group(3))
                        continue

                    try:
                        email_msg = quopri.decodestring(str(msg.get_payload(0)))
                    except Exception:
                        continue

                    email_msg = email_msg.decode("utf-8", "ignore")
                    pattern = re.compile(rf"{body_regex}")
                    search = pattern.search(email_msg)
                    if search is not None and len(search.groups()) > 1:
                        found.append(search.group(2))

    info[ATTR_COUNT] = len(found)
    info[ATTR_CODE] = found
    return info


def amazon_exception(
    account: Type[imaplib.IMAP4_SSL], fwds: Optional[str] = None
) -> dict:
    """Find Amazon exception emails.

    Returns dict of sensor data
    """
    order_number = []
    tfmt = get_formatted_date()
    count = 0
    info = {}

    forward_list = _process_amazon_forwards(fwds)
    email_addresses = _get_sender_list(AMAZON_EMAIL, forward_list)

    for email_address in email_addresses:
        (server_response, sdata) = email_search(
            account, [email_address], tfmt, AMAZON_EXCEPTION_SUBJECT
        )

        if server_response == "OK" and sdata[0] is not None:
            count += len(sdata[0].split())
            order_numbers = get_tracking(sdata[0], account, AMAZON_PATTERN)
            for order in order_numbers:
                if order not in order_number:
                    order_number.append(order)

    info[ATTR_COUNT] = count
    info[ATTR_ORDER] = order_number
    return info


def get_items(
    account: Type[imaplib.IMAP4_SSL],
    param: str = None,
    fwds: Optional[str] = None,
    days: int = DEFAULT_AMAZON_DAYS,
) -> Union[List[str], int]:
    """Parse Amazon emails for order number and active package state.

    Returns list of active order numbers or active email count as integer
    """
    past_date = datetime.date.today() - datetime.timedelta(days=days)
    tfmt = past_date.strftime("%d-%b-%Y")

    active_orders = []
    delivered_orders = []
    order_number = []

    forward_list = _process_amazon_forwards(fwds)
    email_addresses = _get_sender_list(AMAZON_EMAIL, forward_list)

    active_subjects = [
        "pedido:",
        "enviado:",
        "en reparto:",
        "fw: pedido:",
        "fw: enviado:",
        "fw: en reparto:",
    ]

    active_body_markers = [
        "¡gracias por tu pedido",
        "¡tu paquete se ha enviado!",
        "¡tu paquete está en reparto!",
    ]

    delivered_subjects = [
        "entregado:",
        "fw: entregado:",
    ]

    delivered_body_markers = [
        "¡tu paquete se ha entregado!",
    ]

    order_pattern = re.compile(r"[0-9]{3}-[0-9]{7}-[0-9]{7}")

    for email_address in email_addresses:
        (server_response, sdata) = email_search(account, [email_address], tfmt)

        if server_response != "OK" or sdata[0] is None:
            continue

        id_list = sdata[0].split()
        for i in id_list:
            data = email_fetch(account, i, "(RFC822)")[1]
            for response_part in data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                # Decode subject safely
                try:
                    raw_subject = msg["subject"] or ""
                    decoded_parts = decode_header(raw_subject)
                    subject_parts = []
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            subject_parts.append(
                                part.decode(encoding or "utf-8", "ignore")
                            )
                        else:
                            subject_parts.append(part)
                    email_subject = "".join(subject_parts)
                except Exception:
                    email_subject = str(msg["subject"] or "")

                email_subject_l = email_subject.lower()

                # Get all body text
                email_msg = ""
                for part in msg.walk():
                    if part.get_content_type() not in ["text/html", "text/plain"]:
                        continue
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    try:
                        email_msg += payload.decode("utf-8", "ignore")
                    except Exception:
                        continue

                email_msg_l = email_msg.lower()

                found_subject_orders = order_pattern.findall(email_subject)
                found_body_orders = order_pattern.findall(email_msg)

                all_found_orders = []
                for found in found_subject_orders + found_body_orders:
                    if found not in all_found_orders:
                        all_found_orders.append(found)
                    if found not in order_number:
                        order_number.append(found)

                is_active = False
                is_delivered = False

                if any(text in email_subject_l for text in active_subjects):
                    is_active = True
                if any(text in email_msg_l for text in active_body_markers):
                    is_active = True

                if any(text in email_subject_l for text in delivered_subjects):
                    is_delivered = True
                if any(text in email_msg_l for text in delivered_body_markers):
                    is_delivered = True

                # If delivered, remember order so it can be removed from active
                if is_delivered:
                    for found in all_found_orders:
                        if found not in delivered_orders:
                            delivered_orders.append(found)

                # If active, add order unless already known active
                if is_active:
                    for found in all_found_orders:
                        if found not in active_orders:
                            active_orders.append(found)

    # Remove delivered orders from active list
    active_orders = [order for order in active_orders if order not in delivered_orders]

    if param == "count":
        return len(active_orders)

    return active_orders
