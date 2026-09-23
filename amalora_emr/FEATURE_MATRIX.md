# Feature Matrix

## Public benchmark capabilities represented
Scheduling, recurring appointments, waitlists, patient registration, multi-branch records, SOAP notes, specialty templates, case sheets, treatment plans, digital consent, eRx boundary, invoicing, cash/insurance split, price-card-ready billing, pre-authorization, claim validation/submission/remittance/resubmission/reconciliation, inventory, purchase-order/BOM concepts, lab/radiology queue and barcode concepts, patient portal, payments, telehealth workflow, WhatsApp/SMS communication, Google Calendar/accounting/payment adapters, role-based access, audit events, reporting and AI clinical documentation draft workflow.

## Amalora-specific extensions
- Ask Amalora can act as a controlled natural-language front end.
- UI, chat, notification and appointment languages are separate settings.
- Booking collision checks cover clinician and room/device resources together.
- AI-generated clinical content remains draft until clinician approval.
- Regulated connector states are explicit; the system never simulates government acceptance.
- One notification outbox can route to in-app, email, WhatsApp, SMS and push.

## Connectors intentionally not faked
NABIDH, Malaffi, Riayati, eClaimLink/Shafafiya, government eRx, Emirates ID services, production lab device feeds, payment gateway webhooks, WhatsApp Business and accounting sync all require real credentials/contracts/specifications and acceptance testing.
