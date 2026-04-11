# Home Assistant Mail & Packages (EU Fork)

![GitHub](https://img.shields.io/github/license/moralmunky/Home-Assistant-Mail-And-Packages)
![GitHub Repo stars](https://img.shields.io/github/stars/moralmunky/Home-Assistant-Mail-And-Packages)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/moralmunky/Home-Assistant-Mail-And-Packages)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

---

## What is this?

This is a **European-focused fork** of the original  
[Mail and Packages integration](https://github.com/moralmunky/Home-Assistant-Mail-And-Packages).

It improves package tracking for **EU carriers** and fixes limitations in the original integration.

---

## Key Features

### Multi-carrier tracking (EU focused)
- Correos (API-based tracking)
- DHL (email parsing support)
- GLS / CTT / others (via email parsing)

---

### Persistent manual tracking
- Add tracking codes manually
- Stored **persistently** in Home Assistant storage
- Packages remain visible even after:
  - rescans
  - clearing input fields
  - restarts

---

### Improved tracking behavior
- No more disappearing packages after rescans
- Works independently from email presence
- Better handling of multi-carrier environments

---

### Dashboard-friendly sensors
- Active packages
- In transit
- Delivered
- Per carrier + total overview

## Example Dashboard

### PC
<p align="center">
  <img src="docs/dashboard_example_1.png" alt="Example PC Dashboard" width="800"> 
</p>
<p align="center">
  <img src="docs/dashboard_example_2.png" alt="Example PC Dashboard" width="800"> 
</p>

### Mobile
<p align="center">
  <img src="docs/dashboard_example_mobile_1.jpg" alt="Example Mobile Dashboard" width="250">
</p>
<p align="center">
  <img src="docs/dashboard_example_mobile_2.jpg" alt="Example Mobile Dashboard" width="250">
</p>

---

## Important difference from original

Original integration:
- Focused mainly on **USPS / US carriers**
- Relies heavily on **email presence**
- No persistent manual tracking

This fork:
- Focused on **EU logistics**
- Adds **persistent tracking**
- Improves reliability for daily usage

---

## How it works

The integration connects to your email (IMAP) and:
- Parses shipment emails from supported carriers
- Extracts tracking info and status
- Combines with manually added tracking codes
- Updates Home Assistant sensors

All processing is **local** (no external services)

---

## Privacy & Security

- Runs fully local in Home Assistant
- No external APIs required (except optional carrier APIs like Correos)
- Files in `/www` may be publicly accessible (see HA docs)

---

## Installation

### HACS (recommended)
1. Add this repository as a custom repository
2. Install the integration
3. Restart Home Assistant

---

## Configuration

See original documentation:
https://github.com/moralmunky/Home-Assistant-Mail-And-Packages/wiki

---

## Credits

- Original project:  
  https://github.com/moralmunky/Home-Assistant-Mail-And-Packages

- This fork builds upon that work and extends it for EU usage

---

## Feedback / Issues

If you encounter issues or have feature requests:
Open an issue on this repository

---

## Support

If this project helps you:
- Star the repo
- Report issues
- Suggest improvements
