# Forgot Password API Documentation

## Overview
The forgot password feature allows users to reset their passwords using a secure OTP (One-Time Password) system sent via email.

## Endpoints

### 1. Request Password Reset
**POST** `/api/v1/auth/forgot-password`

Send an OTP to the user's registered email address.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If this email is registered, you will receive a reset code"
}
```

### 2. Verify OTP (Optional)
**POST** `/api/v1/auth/verify-otp`

Verify if the OTP is valid without resetting the password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "message": "OTP is valid"
}
```

### 3. Reset Password
**POST** `/api/v1/auth/reset-password`

Reset the password using the OTP code.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp_code": "123456",
  "new_password": "newSecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

## Security Features

1. **OTP Validity**: OTP codes expire after 15 minutes
2. **Single Use**: Each OTP can only be used once
3. **Email Privacy**: System doesn't reveal if an email exists or not
4. **Secure Generation**: Uses cryptographically secure random number generation
5. **Password Requirements**: New passwords must be 8+ characters

## Email Templates

The system sends two types of emails:

1. **OTP Email**: Contains the 6-digit code with security warnings
2. **Confirmation Email**: Sent after successful password reset

## Error Handling

- **404**: User not found (disguised as success for security)
- **400**: Invalid or expired OTP
- **500**: Email service failures

## Environment Variables

Add these to your `.env` file:

```env
# Email Configuration
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=codebeta2500@gmail.com
MAIL_PASSWORD=sojc kfrh ozpt czlb
MAIL_FROM=codebeta2500@gmail.com
MAIL_FROM_NAME=VSDC Integration System
```

## Usage Flow

1. User requests password reset by providing email
2. System generates 6-digit OTP valid for 15 minutes
3. OTP is sent to user's email with security instructions
4. User enters email, OTP, and new password
5. System validates OTP and updates password
6. Confirmation email is sent to user
7. User can log in with new password

## Testing

To test the forgot password functionality:

1. Ensure email configuration is set up
2. Have a user account with a valid email address
3. Use the API endpoints in sequence
4. Check email inbox for OTP and confirmation emails