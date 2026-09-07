import pytest
from app.router.input_classifier import InputClassifier
from app.schemas.analysis import InputType


@pytest.mark.asyncio
async def test_classify_url():
    classifier = InputClassifier()
    assert await classifier.classify(url="https://secure-bank.example.com/login") == InputType.URL
    assert await classifier.classify(text="https://phishing-site.xyz/verify") == InputType.URL
    assert await classifier.classify(text="www.paypal-verification.com") == InputType.URL


@pytest.mark.asyncio
async def test_classify_text_and_email():
    classifier = InputClassifier()
    assert await classifier.classify(text="Hello, how are you doing today?") == InputType.TEXT
    
    email_text = "From: security@bank.com\nTo: victim@user.com\nSubject: Account Suspended\n\nPlease verify."
    assert await classifier.classify(text=email_text) == InputType.EMAIL


@pytest.mark.asyncio
async def test_classify_empty():
    classifier = InputClassifier()
    assert await classifier.classify() == InputType.UNKNOWN
