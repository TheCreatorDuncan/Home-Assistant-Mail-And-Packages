"""Constants for Mail and Packages."""
from __future__ import annotations

from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "mail_and_packages"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0-dev"  # Now updated by release workflow
ISSUE_URL = "http://github.com/moralmunky/Home-Assistant-Mail-And-Packages"
PLATFORM = "sensor"
PLATFORMS = ["camera", "sensor"]
DATA = "data"
COORDINATOR = "coordinator_mail"
OVERLAY = ["overlay.png", "vignette.png", "white.png"]
SERVICE_FORCE_SCAN = "force_scan"
SERVICE_UPDATE_FILE_PATH = "update_file_path"
CAMERA = "cameras"

# Attributes
ATTR_AMAZON_IMAGE = "amazon_image"
ATTR_COUNT = "count"
ATTR_CODE = "code"
ATTR_ORDER = "order"
ATTR_TRACKING = "tracking"
ATTR_TRACKING_NUM = "tracking_#"
ATTR_IMAGE = "image"
ATTR_IMAGE_PATH = "image_path"
ATTR_SERVER = "server"
ATTR_IMAGE_NAME = "image_name"
ATTR_EMAIL = "email"
ATTR_SUBJECT = "subject"
ATTR_BODY = "body"
ATTR_PATTERN = "pattern"
ATTR_USPS_MAIL = "usps_mail"

# Configuration Properties
CONF_ALLOW_EXTERNAL = "allow_external"
CONF_CAMERA_NAME = "camera_name"
CONF_CUSTOM_IMG = "custom_img"
CONF_CUSTOM_IMG_FILE = "custom_img_file"
CONF_FOLDER = "folder"
CONF_PATH = "image_path"
CONF_DURATION = "gif_duration"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IMAGE_SECURITY = "image_security"
CONF_IMAP_TIMEOUT = "imap_timeout"
CONF_GENERATE_MP4 = "generate_mp4"
CONF_AMAZON_FWDS = "amazon_fwds"
CONF_AMAZON_DAYS = "amazon_days"
CONF_CORREOS_CODES = "correos_codes"

# Defaults
DEFAULT_CAMERA_NAME = "Mail USPS Camera"
DEFAULT_NAME = "Mail And Packages"
DEFAULT_PORT = "993"
DEFAULT_FOLDER = '"INBOX"'
DEFAULT_PATH = "custom_components/mail_and_packages/images/"
DEFAULT_IMAGE_SECURITY = True
DEFAULT_IMAP_TIMEOUT = 30
DEFAULT_GIF_DURATION = 5
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_GIF_FILE_NAME = "mail_today.gif"
DEFAULT_AMAZON_FWDS = '""'
DEFAULT_ALLOW_EXTERNAL = False
DEFAULT_CUSTOM_IMG = False
DEFAULT_CUSTOM_IMG_FILE = "custom_components/mail_and_packages/images/mail_none.gif"
DEFAULT_AMAZON_DAYS = 3
DEFAULT_CORREOS_CODES = []

# Amazon
AMAZON_DOMAINS = [
    "amazon.es",
]

AMAZON_DELIVERED_SUBJECT = [
    "Entregado:",
]

AMAZON_SHIPMENT_TRACKING = [
    "shipment-tracking",
    "confirmar-envio",
]

AMAZON_EMAIL = [
    "auto-confirm@amazon.es",
    "order-update@amazon.es",
    "confirmar-envio@amazon.es",
    "shipment-tracking@amazon.es",
]

AMAZON_PACKAGES = "amazon_packages"
AMAZON_ORDER = "amazon_order"
AMAZON_DELIVERED = "amazon_delivered"

AMAZON_IMG_PATTERN = (
    "(https://)([\\w_-]+(?:(?:\\.[\\w_-]+)+))([\\w.,@?^=%&:/~+#-;]*[\\w@?^=%&/~+#-;])?"
)

AMAZON_HUB = "amazon_hub"
AMAZON_HUB_CODE = "amazon_hub_code"
AMAZON_HUB_EMAIL = [
    "order-update@amazon.es",
]

AMAZON_HUB_SUBJECT = "ready for pickup from Amazon Hub Locker"
AMAZON_HUB_SUBJECT_SEARCH = "(You have a package to pick up)(.*)(\\d{6})"
AMAZON_HUB_BODY = "(Your pickup code is <b>)(\\d{6})"

AMAZON_TIME_PATTERN = [
    "En reparto:",
    "en reparto:",
    "¡Tu paquete está en reparto!",
    "¡Tu paquete se ha enviado!",
    "Entregado:",
]

AMAZON_EXCEPTION_SUBJECT = "Actualización de entrega:"
AMAZON_EXCEPTION_BODY = "retraso"
AMAZON_EXCEPTION = "amazon_exception"
AMAZON_EXCEPTION_ORDER = "amazon_exception_order"
AMAZON_PATTERN = "[0-9]{3}-[0-9]{7}-[0-9]{7}"

AMAZON_LANGS = [
    "es_ES",
    "es_ES.UTF-8",
    "",
]

# Sensor Data
SENSOR_DATA = {
    # Amazon
    "amazon_packages": {},
    "amazon_delivered": {
        "email": ["order-update@amazon.es"],
        "subject": ["Entregado:"],
        "body": ["¡Tu paquete se ha entregado!"],
    },
    "amazon_exception": {
        "email": [
            "order-update@amazon.es",
            "confirmar-envio@amazon.es",
            "shipment-tracking@amazon.es",
        ],
        "subject": ["Actualización de entrega:"],
        "body": ["retraso"],
    },

    # Correos
    "correos_delivered": {
        "email": ["no-reply@correosexpress.com"],
        "subject": [], #yet to be defined
    },
    "correos_delivering": {
        "email": ["no-reply@correosexpress.com"],
        "subject": [], #yet to be defined
    },
    "correos_packages": {},
    "correos_tracking": {
        "pattern": [] #yet to be defined
    },

    # CTT Express
    "ctt_express_delivered": {
        "email": ["noreplyclientes@cttexpress.org"],
        "subject": ["Información envío -"],
        "body": [
            "(?i)ha sido entregado",
            "(?i)entregado a",
        ],
    },
    "ctt_express_delivering": {
        "email": ["noreplyclientes@cttexpress.org"],
        "subject": ["Información envío -"],
        "body": [
            "(?i)est[aá] en reparto",
            "(?i)est[aá] viajando a destino",
            "(?i)tenemos previsto entregarlo antes del d[ií]a",
        ],
    },
    "ctt_express_packages": {},
    "ctt_express_tracking": {
        "pattern": ["\\b\\d{22}\\b"]
    },

    # DHL
    "dhl_delivered": {
        "email": ["noreply@dhl.de"],
        "subject": ['Current status of the shipment'],
        "body": [
            "(?i)successfully delivered",
            "(?i)shipment has been delivered",
            "(?i)delivered",
        ],
    },
    "dhl_delivering": {
        "email": ["noreply@dhl.de"],
        "subject": ['Current status of the shipment'],
        "body": [
            "(?i)processed in the export parcel center",
            "(?i)processed in the parcel center of origin",
            "(?i)processed in the parcel center",
            "(?i)international shipment has been processed",
            "(?i)out for delivery",
            "(?i)with the delivery courier",
            "(?i)delivery vehicle",
        ],
    },
    "dhl_packages": {},
    "dhl_tracking": {
        "pattern": ["[A-Z]{2}\\d{9}[A-Z]{2}"]
    },

    # EcoScooting
    "ecoscooting_delivered": {
        "email": ["noreply@service.ecoscooting.com"],
        "subject": ["Punto de Recogida"],
        "body": [
            "(?i)ha sido entregado",
            "(?i)entregado",
        ],
    },
    "ecoscooting_delivering": {
        "email": ["noreply@service.ecoscooting.com"],
        "subject": ["Punto de Recogida"],
        "body": [
            "(?i)ya est[aá] de camino a nuestros almacenes",
            "(?i)ser[aá] entregado en la siguiente direcci[oó]n",
        ],
    },
    "ecoscooting_packages": {},
    "ecoscooting_tracking": {
        "pattern": ["\\bAP\\d{14}\\b"] #presumably, yet to be finally defined 
    },

    # GLS Spain
    "gls_delivered": {
        "email": ["noreply@comunicaciones.gls-spain.com"],
        "subject": [], #yet to be defined
        "body": [], #yet to be defined
    },
    "gls_delivering": {
        "email": ["noreply@comunicaciones.gls-spain.com"],
        "subject": [
            "está en reparto",
            "está en camino",
        ],
        "body": [
            "ya está en reparto",
            "está en camino",
        ],
    },
    "gls_packages": {},
    "gls_tracking": {
        "pattern": ["\\d{10}"]
    },

    # TIPSA
    "tipsa_delivered": {
        "email": ["no-reply@tip-sa.com"],
        "subject": ["INFORMACIÓN SOBRE TU ENVÍO - TIPSA"],
        "body": ["ha sido entregado"],
    },
    "tipsa_delivering": {
        "email": ["no-reply@tip-sa.com"],
        "subject": ["INFORMACIÓN SOBRE TU ENVÍO - TIPSA"],
        "body": ["se encuentra en reparto", "se encuentra en camino"],
    },
    "tipsa_packages": {},
    "tipsa_tracking": {
        "pattern": ["\\d{22}"]
    },
}

# Sensor definitions
SENSOR_TYPES: Final[dict[str, SensorEntityDescription]] = {
    "mail_updated": SensorEntityDescription(
        name="Mail Updated",
        icon="mdi:update",
        key="mail_updated",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),

    # Amazon
    "amazon_packages": SensorEntityDescription(
        name="Mail Amazon Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package",
        key="amazon_packages",
    ),
    "amazon_delivered": SensorEntityDescription(
        name="Mail Amazon Packages Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="amazon_delivered",
    ),
    "amazon_exception": SensorEntityDescription(
        name="Mail Amazon Exception",
        native_unit_of_measurement="package(s)",
        icon="mdi:archive-alert",
        key="amazon_exception",
    ),
    "amazon_hub": SensorEntityDescription(
        name="Mail Amazon Hub Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package",
        key="amazon_hub",
    ),

    # Correos
    "correos_delivered": SensorEntityDescription(
        name="Mail Correos Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="correos_delivered",
    ),
    "correos_delivering": SensorEntityDescription(
        name="Mail Correos Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="correos_delivering",
    ),
    "correos_packages": SensorEntityDescription(
        name="Mail Correos Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="correos_packages",
    ),

    # CTT Express
    "ctt_express_delivered": SensorEntityDescription(
        name="Mail CTT Express Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="ctt_express_delivered",
    ),
    "ctt_express_delivering": SensorEntityDescription(
        name="Mail CTT Express Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="ctt_express_delivering",
    ),
    "ctt_express_packages": SensorEntityDescription(
        name="Mail CTT Express Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="ctt_express_packages",
    ),

    # TIPSA
    "tipsa_delivered": SensorEntityDescription(
        name="Mail TIPSA Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="tipsa_delivered",
    ),
    "tipsa_delivering": SensorEntityDescription(
        name="Mail TIPSA Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="tipsa_delivering",
    ),
    "tipsa_packages": SensorEntityDescription(
        name="Mail TIPSA Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="tipsa_packages",
    ),

    # GLS Spain
    "gls_delivering": SensorEntityDescription(
        name="Mail GLS Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="gls_delivering",
    ),
    "gls_delivered": SensorEntityDescription(
        name="Mail GLS Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="gls_delivered",
    ),
    "gls_packages": SensorEntityDescription(
        name="Mail GLS Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="gls_packages",
    ),

    # DHL
    "dhl_delivering": SensorEntityDescription(
        name="Mail DHL Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="dhl_delivering",
    ),
    "dhl_delivered": SensorEntityDescription(
        name="Mail DHL Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="dhl_delivered",
    ),
    "dhl_packages": SensorEntityDescription(
        name="Mail DHL Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="dhl_packages",
    ),

    # EcoScooting
    "ecoscooting_delivering": SensorEntityDescription(
        name="Mail EcoScooting Delivering",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="ecoscooting_delivering",
    ),
    "ecoscooting_delivered": SensorEntityDescription(
        name="Mail EcoScooting Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="ecoscooting_delivered",
    ),
    "ecoscooting_packages": SensorEntityDescription(
        name="Mail EcoScooting Packages",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant-closed",
        key="ecoscooting_packages",
    ),
    
    ###
    # !!! Insert new sensors above these two !!!
    ###
    "zpackages_delivered": SensorEntityDescription(
        name="Mail Packages Delivered",
        native_unit_of_measurement="package(s)",
        icon="mdi:package-variant",
        key="zpackages_delivered",
    ),
    "zpackages_transit": SensorEntityDescription(
        name="Mail Packages In Transit",
        native_unit_of_measurement="package(s)",
        icon="mdi:truck-delivery",
        key="zpackages_transit",
    ),
}

IMAGE_SENSORS: Final[dict[str, SensorEntityDescription]] = {}

# Name
CAMERA_DATA = {
    "amazon_camera": ["Mail Amazon Delivery Camera"],
}

# Sensor Index
SENSOR_NAME = 0
SENSOR_UNIT = 1
SENSOR_ICON = 2

# For sensors with delivering and delivered statuses
SHIPPERS = [
    "correos",
    "ctt_express",
    "gls",
    "tipsa",
    "dhl",
    "ecoscooting",
    # TODO: Add when sensor data is implemented
    # "seur",
    # "mrw",
]
