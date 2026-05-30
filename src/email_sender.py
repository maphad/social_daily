import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class EmailSender:
    """Sends digest emails via SMTP"""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587):
        """
        Initialize email sender
        Args:
            smtp_host: SMTP server (default: Gmail)
            smtp_port: SMTP port (default: 587 for TLS)
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.sender_name = "Social Daily"
    
    def send_digest_email(self, recipient_email: str, recipient_name: str, 
                         html_content: str, digest_date: str) -> bool:
        """
        Send digest email to recipient
        
        Args:
            recipient_email: Email address
            recipient_name: Recipient name for greeting
            html_content: HTML body of email
            digest_date: Date string for subject line
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            print("⚠️  Email credentials not configured in .env")
            print("   Set SENDER_EMAIL and SENDER_PASSWORD to enable email delivery")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Your Social Daily Digest - {digest_date}"
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            # Add HTML part
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✓ Email sent to {recipient_email}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False


class ConsolePrinter:
    """Prints digest to console (for testing/demo)"""
    
    @staticmethod
    def print_digest(digest_data: dict):
        """Pretty-print digest to console"""
        print("\n" + "="*70)
        print(f"📧 EMAIL DIGEST: {digest_data['digest_date']}")
        print("="*70)
        
        for platform, data in digest_data['platforms'].items():
            print(f"\n{data['emoji']} {platform.upper()}")
            print("-" * 70)
            
            for idx, item in enumerate(data['items'], 1):
                print(f"\n{idx}. {item['title']}")
                print(f"   By: {item['author']}")
                print(f"   {item['excerpt']}")
                print(f"   Link: {item['url']}")


def send_digest(recipient_email: str, recipient_name: str, 
                html_content: str, digest_date: str,
                delivery_channels: List[str] = None) -> dict:
    """
    Send digest via specified channels
    
    Args:
        recipient_email: Email address
        recipient_name: Recipient name
        html_content: HTML content
        digest_date: Date of digest
        delivery_channels: List of channels ('email', 'sms', 'whatsapp', 'console')
    
    Returns:
        Dict with delivery status per channel
    """
    if delivery_channels is None:
        delivery_channels = ['console']
    
    status = {}
    
    for channel in delivery_channels:
        if channel == 'email':
            sender = EmailSender()
            status['email'] = 'sent' if sender.send_digest_email(
                recipient_email, recipient_name, html_content, digest_date
            ) else 'failed'
        
        elif channel == 'console':
            print(f"\n📋 [DEMO] Sending to console...")
            status['console'] = 'sent'
        
        elif channel == 'sms':
            print(f"📱 [TODO] SMS delivery not yet implemented")
            status['sms'] = 'not_implemented'
        
        elif channel == 'whatsapp':
            print(f"💬 [TODO] WhatsApp delivery not yet implemented")
            status['whatsapp'] = 'not_implemented'
    
    return status
