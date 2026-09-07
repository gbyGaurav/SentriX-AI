"""Comprehensive scam/phishing text pattern definitions for the Text Fraud Detector."""

URGENCY_PATTERNS = [
    'act now', 'immediately', 'within 24 hours', 'urgent', 'expire', 'last chance',
    'limited time', 'hurry', 'right away', 'don\'t delay', 'before it\'s too late',
    'final notice', 'action required', 'respond immediately', 'time sensitive',
    'deadline', 'running out', 'only today', 'hours left', 'minutes left',
    'expiring soon', 'about to expire', 'suspension notice', 'final warning',
    'must respond', 'time is running out', 'don\'t miss', 'ending soon',
    'act fast', 'right now', 'asap', 'without delay', 'promptly',
    'within 48 hours', 'your account will be', 'will be closed',
    'will be suspended', 'will be terminated', 'will be locked',
]

CREDENTIAL_PATTERNS = [
    'password', 'otp', 'pin', 'ssn', 'credit card', 'bank account', 'verify your',
    'social security', 'login credentials', 'account number', 'routing number',
    'cvv', 'security code', 'card number', 'expiry date', 'date of birth',
    'mother\'s maiden', 'secret question', 'security answer', 'enter your',
    'provide your', 'confirm your identity', 'verify your identity',
    'update your information', 'confirm your account', 'validate your',
    'verify your account', 'sign in to confirm', 'login to verify',
    'share your', 'send your', 'aadhaar', 'pan card', 'passport number',
    'driver\'s license', 'tax id', 'taxpayer', 'user id', 'username and password',
    'kyc', 'kyc expired', 'update kyc', 'complete kyc', 'pan number', 'aadhaar card',
]

FINANCIAL_PATTERNS = [
    'wire transfer', 'bitcoin', 'gift card', 'western union', 'payment', 'prize',
    'won', 'lottery', 'inheritance', 'beneficiary', 'unclaimed funds',
    'million dollars', 'lakh', 'crore', 'investment opportunity', 'guaranteed returns',
    'double your money', 'crypto', 'cryptocurrency', 'ethereum', 'usdt',
    'money transfer', 'send money', 'pay now', 'make payment', 'processing fee',
    'advance fee', 'handling charge', 'tax payment', 'customs fee',
    'release fee', 'clearance fee', 'transfer fee', 'bank transfer',
    'moneygram', 'cash app', 'venmo', 'zelle', 'paypal', 'upi',
    'google pay', 'phonepe', 'paytm', 'direct deposit', 'routing number',
    'forex', 'binary options', 'high yield', 'risk free investment',
    'minimum deposit', 'trading signal', 'guaranteed profit',
    'shipping fee', 'courier fee', 'delivery fee', '₹', 'rs.', 'inr', 'rupees',
    'free iphone', 'cash prize', '50,000', '499',
]

THREAT_PATTERNS = [
    'account suspended', 'legal action', 'arrest', 'warrant', 'police', 'blocked',
    'unauthorized access', 'suspicious activity detected', 'your account has been',
    'compromised', 'hacked', 'breached', 'unauthorized transaction',
    'unusual activity', 'security alert', 'fraud alert', 'account locked',
    'account disabled', 'access restricted', 'violation', 'penalty',
    'prosecution', 'court order', 'subpoena', 'fbi', 'cia', 'interpol',
    'homeland security', 'tax evasion', 'money laundering',
    'criminal investigation', 'cease and desist', 'legal proceedings',
    'law enforcement', 'face consequences', 'serious consequences',
    'failure to comply', 'non-compliance', 'will be reported',
]

TOO_GOOD_PATTERNS = [
    'congratulations', 'selected', 'winner', 'free', 'guaranteed', 'no risk',
    'you have been chosen', 'you\'ve won', 'claim your', 'collect your prize',
    'exclusive offer', 'special promotion', 'limited offer', 'once in a lifetime',
    'amazing deal', 'unbelievable offer', 'too good', 'incredible opportunity',
    'earn from home', 'make money fast', 'work from home', 'easy money',
    'passive income', 'financial freedom', 'get rich', 'overnight millionaire',
    'secret method', 'proven system', 'no experience needed', 'no skills required',
    'free money', 'free gift', 'complimentary', 'bonus', 'reward',
    'cashback', 'discount code', 'promo code', '100% free', 'zero cost',
    'risk-free', 'money-back guarantee', 'satisfaction guaranteed',
]

IMPERSONATION_PATTERNS = [
    'from your bank', 'apple support', 'irs', 'government', 'official',
    'microsoft support', 'google security', 'amazon security', 'paypal team',
    'customer service', 'technical support', 'it department', 'helpdesk',
    'system administrator', 'security team', 'fraud department',
    'compliance department', 'tax department', 'revenue service',
    'customs department', 'immigration', 'embassy', 'consulate',
    'central bank', 'reserve bank', 'federal reserve', 'state bank',
    'dear customer', 'dear user', 'dear account holder', 'valued customer',
    'dear sir/madam', 'beloved', 'trusted partner', 'esteemed customer',
    'netflix team', 'facebook security', 'instagram support', 'whatsapp team',
    'telegram team', 'twitter support', 'linkedin team',
]

SUSPICIOUS_CTA_PATTERNS = [
    'click here', 'click below', 'click the link', 'download now', 'open attachment',
    'click this link', 'tap here', 'follow this link', 'visit this page',
    'open this', 'access your account', 'log in now', 'sign in here',
    'update now', 'upgrade now', 'confirm now', 'verify now',
    'reset your password', 'unlock your account', 'reactivate',
    'claim now', 'redeem now', 'collect now', 'get started now',
    'apply now', 'register now', 'subscribe now', 'join now',
    'call this number', 'contact us immediately', 'reply with',
    'send a text', 'forward this', 'share with',
]

# Regex patterns for entity extraction
URL_REGEX = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
CRYPTO_REGEX = r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b|0x[a-fA-F0-9]{40}\b'
