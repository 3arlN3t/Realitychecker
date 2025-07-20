#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from app.services.pdf_processing import PDFProcessingService
from app.config import get_config

config = get_config()
pdf_service = PDFProcessingService(config)

test_urls = [
    'https://media.twiliocdn.com/AC123456789012345678901234567890/MM123456789012345678901234567890',
    'https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test',
    'https://example.com/test.pdf'
]

for url in test_urls:
    is_twilio = pdf_service._is_twilio_media_url(url)
    print(f'{url[:60]}... -> Twilio URL: {is_twilio}')