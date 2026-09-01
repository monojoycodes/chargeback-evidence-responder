Here's the updated table with reason code titles included, network-wise:

### UPI

| Category | Code - Title | Documents Required |
|---|---|---|
| Customer Dispute | 1061 - Credit Not Processed | Refund proof, bank statement, customer confirmation, refund policy |
| | 1062 - Goods/Services Not As Described | Product screenshots, delivery proof, customer dissatisfaction comms, return policy |
| | 1064 - Goods/Services Not Received | Delivery proof, customer enquiries, T&C on refund/fulfilment |
| Fraud | 128 - Fraudulent Transaction | Auth logs, invoice with price breakdown, delivery proof with customer details |
| Authorisation Error | 108 - Remiter Debited but Beneficiary Not Credited | Delivery proof, customer enquiries, withdrawal letter, T&C |
| | 1065 - Debit on Failed Transaction | Same as above |
| | 121 - TCC Raised but Beneficiary Not Credited | Same as above |
| Processing Error | 1063 - Paid by Other Means | Proof no other payment received, refund proof, proof of different product/service |
| | 1084 - Duplicate Processing | System logs, invoicing for separate transactions |
| | 1085 - Charge Amount Exceeds Authorisation Amount | Invoice breakdown, product screenshot, authorisation proof, system logs |
| | 1081 - Not Settled Within Timeline | Internal logs, timestamps, re-auth proof, customer authorisation, invoice |

### Visa

| Category | Code - Title | Documents Required |
|---|---|---|
| Customer Dispute | 1 - Merchandise/Services Not Received | Delivery confirmation, tracking info, service records, delivery logs |
| | 2 - Cancelled Recurring Transaction | Cancellation policy, no cancellation request, usage logs, ToS |
| | 3 - Not as Described or Defective | Product images, QC records, no return proof, T&C |
| | 4 - Counterfeit Merchandise | Authenticity certificates, supplier verification, brand authorisation |
| | 5 - Misrepresentation | Marketing materials, terms display, customer acknowledgement |
| | 6 - Credit Not Processed | Refund proof, credit timestamp, refund policy compliance |
| | 7 - Cancelled Merchandise/Services | No cancellation received, cancellation policy, shipping proof |
| | 8 - Original Credit Transaction Not Accepted | Account verification, OCT compliance, approval records |
| Fraud | 1 - EMV Liability Shift – Counterfeit Fraud | EMV certificate, terminal capability, chip read receipt |
| | 2 - EMV Liability Shift – Non-Counterfeit Fraud | EMV docs, terminal logs, chip data, PIN verification |
| | 3 - Other Fraud – Card-Present | Signed receipt, EMV data, footage timestamp, PIN verification |
| | 4 - Other Fraud – Card-Absent | AVS/CVV2, IP/device fingerprint, order history, 3D Secure |
| | 5 - Visa Fraud Monitoring Program | Fraud prevention docs, authentication records, risk protocols |
| Authorisation Error | 1 - Card Recovery Bulletin | Bulletin check confirmation, card validity proof, terminal records |
| | 2 - Declined Authorisation | Valid auth code, subsequent approval, terminal logs |
| Processing Error | 2 - Incorrect Transaction Code | Correct transaction records, processing logs |
| | 3 - Incorrect Currency Code | Currency agreement, screenshots, exchange rate disclosure |
| | 4 - Incorrect Account Number | Account verification, customer confirmation |
| | 5 - Incorrect Amount | Original receipt, authorisation for exact amount |
| | 6.1 - Duplicate Processing – Single Authorisation | Authorisation logs, batch reports |
| | 6.2 - Paid by Other Means | Proof of single payment method, reconciliation |
| | 7 - Invalid Data | Corrected data, valid processing records |

### Mastercard

| Category | Code - Title | Documents Required |
|---|---|---|
| Customer Dispute | 4841 - Cancelled Recurring/Digital Goods Transaction | Cancellation policy, usage logs, ToS |
| | 4850 - Installment Billing Dispute | Installment agreement, payment schedule, billing records |
| | 4853 - Cardholder Dispute | Delivery/quality proof, product description, return policy (varies) |
| | 4854 - Cardholder Dispute - NEC | General proof of valid transaction/delivery/authorisation |
| Fraud | 4837 - No Cardholder Authorisation | Cardholder verification, AVS/CVV, 3D Secure, delivery proof |
| | 4840 - Fraudulent Processing of Transactions | Fraud screening, authentication records, risk assessment |
| | 4849 - Questionable Business Activity | Business legitimacy proof, delivery confirmation |
| | 4870 - Chip Liability Shift | EMV terminal capability, chip data, fallback reason |
| | 4871 - Chip/PIN Liability Shift | PIN verification, chip+PIN terminal proof |
| Authorisation Error | 4808 - Authorisation-Related Chargeback | Valid auth code, correct amount authorisation, terminal records |
| Processing Error | 4834 - Duplicate Processing | Single transaction proof, void/refund records, timestamps |

### RuPay

| Category | Code - Title | Documents Required |
|---|---|---|
| Customer Dispute | 1061 - Credit Not Processed | Refund proof, bank statement, refund policy |
| | 1062 - Goods/Services Not As Described | Product screenshots, delivery proof, return policy |
| | 1064 - Goods/Services Not Received | Delivery proof, customer enquiries, T&C |
| | 1101 - Illegible Fulfilment | Delivery proof, customer enquiries, T&C |
| | 1102 - Retrieval Request Not Fulfilled | Delivery proof, customer enquiries, T&C |
| | 1103 - Invalid Fulfilment | Delivery proof, customer enquiries, T&C |
| Fraud | 1104 - Cardholder Does Not Recognise the Transaction | Masked-card invoice, auth logs, price breakdown |
| | 1141 - Fraudulent Card-Present Transaction | Matching prior payments, invoices, delivery proof |
| | 1142 - Fraudulent Card-Not-Present Transaction | Matching device/IP parameters, invoices, delivery proof |
| | 1143 - Fraudulent Multiple Transactions | Matching device/IP parameters, invoices, delivery proof |
| Authorisation Error | 1065 - Debit on Failed Transaction | Delivery proof, withdrawal letter, T&C |
| | 1121 - Transaction Received Declined Authorisation Response | Authorisation docs, invoices, timestamps, delivery proof |
| | 1122 - Transaction Not Authorised | (see [Submit Evidence](/docs/payments/disputes/submit-evidence) for full detail) |
