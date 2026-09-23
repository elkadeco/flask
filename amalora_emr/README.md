# Amalora Unified Clinic OS

Independent Amalora-native clinic management / EMR prototype benchmarked against publicly documented UAE clinic-platform capabilities.

This code does **not** copy Unite EMR proprietary source code, private APIs, UI assets or confidential logic.

## Modules
- Multi-branch patient registry
- Scheduling, waitlists and resource conflict protection
- Structured EMR / SOAP records and clinical templates
- Digital consent foundation
- Prescriptions + eRx adapter boundary
- AI Scribe draft workflow requiring clinician approval
- Cash/insurance billing and RCM workflow
- Inventory, expiry, supplier and BOM tracking
- Lab/radiology queue, barcodes, results and approval
- Pharmacy dispensing workflow
- Patient portal foundation
- Telehealth identity / consent / device-check / waiting-room flow
- Notifications through in-app/email/WhatsApp/SMS/push adapter model
- Role-oriented workspaces and audit trail
- Operational reporting
- Integration registry for calendars, messaging, accounting and payments
- UAE compliance adapter boundaries: NABIDH, Malaffi, Riayati, eClaimLink/Shafafiya and eRx

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Production boundary
Do not use this preview for real patient data. Production requires approved UAE data residency, IAM/MFA, encryption, backups, monitoring, privacy/legal/clinical review, authority onboarding, payer contracts and certified connector testing.
