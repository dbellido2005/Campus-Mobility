# SendGrid Setup Instructions for Campus Mobility

This guide will help you set up SendGrid for email verification in the Campus Mobility application.

## Prerequisites

- A SendGrid account (free tier available)
- Access to your domain DNS settings (optional, for domain verification)

## Step 1: Create a SendGrid Account

1. Go to [https://sendgrid.com](https://sendgrid.com)
2. Click "Start for free" or "Sign up"
3. Fill out the registration form with your details
4. Verify your email address when prompted
5. Complete the account setup process

## Step 2: Create an API Key

1. Log into your SendGrid dashboard
2. Navigate to **Settings** → **API Keys** in the left sidebar
3. Click **Create API Key**
4. Choose **Restricted Access** (recommended for security)
5. Set the following permissions:
   - **Mail Send**: Full Access
   - **Mail Settings**: Read Access (optional)
   - **Tracking**: Read Access (optional)
6. Give your API key a descriptive name (e.g., "Campus Mobility Production")
7. Click **Create & View**
8. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!

## Step 3: Verify Your Sender Identity

### Option A: Single Sender Verification (Easiest)

1. Go to **Settings** → **Sender Authentication** → **Single Sender Verification**
2. Click **Create New Sender**
3. Fill out the form:
   - **From Name**: Campus Mobility
   - **From Email**: Use an email you control (e.g., noreply@yourdomain.com)
   - **Reply To**: Same as from email or your support email
   - **Company Address**: Your organization's address
4. Click **Create**
5. Check your email and click the verification link

### Option B: Domain Authentication (Recommended for Production)

1. Go to **Settings** → **Sender Authentication** → **Domain Authentication**
2. Click **Authenticate Your Domain**
3. Enter your domain name (e.g., yourdomain.com)
4. Choose your DNS host
5. Follow the instructions to add the required DNS records
6. Click **Verify** once DNS records are added

## Step 4: Configure Campus Mobility

1. Copy your `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit your `.env` file and add your SendGrid configuration:
   ```env
   SENDGRID_API_KEY=your-actual-api-key-here
   SENDGRID_FROM_EMAIL=noreply@yourdomain.com
   SENDGRID_FROM_NAME=Campus Mobility
   ```

3. **Important**: Make sure the `SENDGRID_FROM_EMAIL` matches the verified sender email from Step 3

## Step 5: Test Your Configuration

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the email test script:
   ```bash
   python test_email.py
   ```

3. Check that you receive the test email and that no errors appear in the console

## Troubleshooting

### Common Issues

**"Unauthorized" or "Forbidden" errors:**
- Verify your API key is correct
- Check that your API key has "Mail Send" permissions
- Make sure you copied the API key completely

**"The from address does not match a verified Sender Identity":**
- Ensure `SENDGRID_FROM_EMAIL` matches your verified sender email exactly
- Complete the sender verification process in the SendGrid dashboard

**Emails not being delivered:**
- Check your spam folder
- Verify the recipient email address is valid
- Monitor your SendGrid dashboard for delivery statistics

### Rate Limits

SendGrid free tier includes:
- 100 emails per day
- No daily sending limit for paid plans

For production use, consider upgrading to a paid plan for higher limits and better deliverability.

## Security Best Practices

1. **Never commit your API key to version control**
2. Use environment variables for all sensitive configuration
3. Rotate your API keys regularly
4. Use restricted access API keys with minimal required permissions
5. Monitor your SendGrid dashboard for unusual activity

## Monitoring and Analytics

SendGrid provides detailed analytics in your dashboard:
- Delivery rates
- Open rates (if tracking enabled)
- Bounce rates
- Spam reports

Monitor these metrics to ensure good email deliverability.

## Production Considerations

1. **Domain Authentication**: Use domain authentication instead of single sender verification
2. **Dedicated IP**: Consider a dedicated IP address for high-volume sending
3. **Suppression Lists**: Implement proper handling of bounces and unsubscribes
4. **Email Templates**: Consider using SendGrid's dynamic templates for more complex emails

## Support

- SendGrid Documentation: [https://docs.sendgrid.com](https://docs.sendgrid.com)
- SendGrid Support: Available through your dashboard
- Campus Mobility Issues: Contact your development team

---

**Note**: Keep your API key secure and never share it publicly. If you suspect your API key has been compromised, immediately delete it from the SendGrid dashboard and create a new one.