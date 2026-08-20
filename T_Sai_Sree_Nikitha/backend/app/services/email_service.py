import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.config import settings

logger = logging.getLogger("email_service")

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Sends an HTML email using SMTP configuration.
    Fails gracefully if SMTP is not configured or throws an exception.
    """
    if not settings.SMTP_HOST or not settings.SMTP_PORT or not settings.SMTP_FROM:
        logger.warning(f"SMTP not configured. Skipping email to {to_email} with subject: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False

def get_base_template(title: str, body_html: str) -> str:
    """
    Generates a uniform, clean HTML email template.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; }}
            .container {{ max-width: 600px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 0 auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background-color: #0f172a; padding: 24px; text-align: center; color: #ffffff; }}
            .header h2 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }}
            .content {{ padding: 32px; line-height: 1.6; font-size: 14px; }}
            .content p {{ margin-top: 0; margin-bottom: 16px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 16px; }}
            .footer {{ background-color: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>VendorIQ Platform</h2>
            </div>
            <div class="content">
                <h3 style="margin-top: 0; color: #0f172a;">{title}</h3>
                {body_html}
            </div>
            <div class="footer">
                &copy; 2026 VendorIQ. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

def send_password_reset_email(to_email: str, username: str, reset_url: str) -> bool:
    subject = "VendorIQ - Password Reset Request"
    body = f"""
    <p>Hello {username},</p>
    <p>We received a request to reset the password for your VendorIQ account.</p>
    <p>Please click the button below to set a new password. This reset link is active for 1 hour.</p>
    <div style="text-align: center;">
        <a href="{reset_url}" class="btn" style="color: #ffffff;">Reset Password</a>
    </div>
    <p style="margin-top: 24px; font-size: 12px; color: #64748b;">If the button does not work, copy and paste this URL into your browser: <br>{reset_url}</p>
    <p>If you did not make this request, you can safely ignore this email.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))

def send_vendor_status_email(to_email: str, vendor_name: str, status: str, comments: str = "") -> bool:
    subject = f"VendorIQ - Vendor Status Updated: {status}"
    comment_section = f"<p><strong>Comments:</strong> {comments}</p>" if comments else ""
    body = f"""
    <p>Dear Partner,</p>
    <p>The registration profile status for vendor <strong>{vendor_name}</strong> has been updated to: <span style="font-weight: 700; color: {'#16a34a' if status == 'Active' else '#dc2626'};">{status}</span>.</p>
    {comment_section}
    <p>Log in to your dashboard to view profile details and proceed with outstanding workflows.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))

def send_procurement_status_email(to_email: str, title: str, status: str, comments: str = "") -> bool:
    subject = f"VendorIQ - Procurement Request {status}"
    comment_section = f"<p><strong>Comments:</strong> {comments}</p>" if comments else ""
    body = f"""
    <p>Hello,</p>
    <p>The procurement requisition <strong>"{title}"</strong> has been: <span style="font-weight: 700; color: {'#16a34a' if status == 'Approved' else '#dc2626'};">{status}</span>.</p>
    {comment_section}
    <p>Please check the procurement portal for subsequent purchase order generation or revisions.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))

def send_delivery_delay_alert(to_email: str, po_number: str, delay_days: int) -> bool:
    subject = f"VendorIQ Alert - Purchase Order Delayed: {po_number}"
    body = f"""
    <p>Attention Supply Chain Operations,</p>
    <p>The Purchase Order <strong>{po_number}</strong> is flagged as delayed by <strong>{delay_days} days</strong> past its expected delivery date.</p>
    <p>Please contact the assigned vendor contact immediately to resolve logistics holdups.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))

def send_contract_expiry_alert(to_email: str, contract_number: str, title: str, days_left: int) -> bool:
    subject = f"VendorIQ Alert - Contract Expiration Warning: {contract_number}"
    body = f"""
    <p>Attention Legal Compliance,</p>
    <p>The contract <strong>{contract_number} ("{title}")</strong> is set to expire in <strong>{days_left} days</strong>.</p>
    <p>Initiate renewals or SLA compliance reviews to prevent service interruption.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))

def send_compliance_alert(to_email: str, vendor_name: str, score: float, risk: str) -> bool:
    subject = f"VendorIQ Alert - High Risk Compliance Warning: {vendor_name}"
    body = f"""
    <p>Attention Quality Assurance,</p>
    <p>Vendor <strong>{vendor_name}</strong> is flagged under warning levels:</p>
    <ul>
        <li><strong>Reliability Score:</strong> {score:.1f}%</li>
        <li><strong>Risk Level:</strong> <span style="color: #dc2626; font-weight: bold;">{risk}</span></li>
    </ul>
    <p>Compliance audit checks and risk audits are required for this vendor.</p>
    """
    return send_email(to_email, subject, get_base_template(subject, body))
