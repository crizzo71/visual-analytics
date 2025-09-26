# Security Guide for RedHat LDAP Analytics Dashboard

## 🔐 Security Overview

This dashboard implements comprehensive security measures to protect sensitive organizational data from Red Hat's LDAP directory.

## 🛡️ Security Features Implemented

### 1. Authentication & Authorization
- **JWT-based session management** with configurable timeout
- **Role-based access control** (Admin, Manager, Viewer)
- **Permission-based feature access**
- **Multi-factor authentication ready** (can be extended)

#### Demo Credentials
```
Admin Access:
- Email: crizzo@redhat.com
- Password: admin123
- Permissions: Full access, export data, user management

Viewer Access:
- Email: demo@redhat.com
- Password: demo123
- Permissions: Limited read-only access
```

### 2. Data Protection
- **Automatic data masking** based on user role
- **Email masking**: `john.doe@redhat.com` → `j***e@redhat.com`
- **Phone masking**: `+1-555-123-4567` → `***-***-4567`
- **Employee ID masking**: `EMP12345` → `EM***5`
- **Role-based data filtering** (managers see only their teams)

### 3. Audit Logging
- **Comprehensive audit trail** for all user actions
- **Login/logout tracking** with failed attempt monitoring
- **Data access logging** with details of what was viewed
- **Export operations logging** with record counts
- **Security event logging** for suspicious activities

### 4. Network Security
- **IP-based access controls** (configurable)
- **Session security** with fingerprinting
- **Rate limiting** protection
- **Secure headers** implementation

### 5. Configuration Security
- **Encrypted configuration storage**
- **Environment variable protection**
- **Secure file permissions** (600 for sensitive files)
- **Secrets management** with automatic key generation

## 🚀 Deployment Security

### Development Environment
```bash
# Start secure dashboard
./run_secure_analytics.sh
```

### Production Deployment

#### 1. HTTPS Configuration
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Use reverse proxy (nginx example)
server {
    listen 443 ssl;
    ssl_certificate cert.pem;
    ssl_certificate_key key.pem;

    location / {
        proxy_pass http://127.0.0.1:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 2. Environment Variables
```bash
export DASHBOARD_SECRET_KEY="your-secure-secret-key"
export SESSION_TIMEOUT_MINUTES="30"
export MAX_LOGIN_ATTEMPTS="3"
export ENABLE_AUDIT_LOGGING="true"
export ALLOWED_IPS="10.0.0.0/8,192.168.0.0/16"
```

#### 3. Firewall Configuration
```bash
# Allow only specific ports
ufw allow 443/tcp
ufw allow 8814/tcp  # MCP server (internal only)
ufw deny 8501/tcp   # Block unsecured dashboard
ufw deny 8502/tcp   # Block unless behind proxy
```

## 🔍 Security Monitoring

### Audit Log Locations
- **Main audit log**: `logs/audit.log`
- **MCP server log**: `logs/mcp_server.log`
- **Application log**: `logs/ldap_mcp.log`

### Key Security Events to Monitor
```bash
# Failed login attempts
grep "LOGIN_ATTEMPT.*false" logs/audit.log

# Data exports
grep "DATA_EXPORT" logs/audit.log

# Security events
grep "SECURITY_EVENT" logs/audit.log

# Configuration changes
grep "CONFIGURATION_CHANGE" logs/audit.log
```

### Automated Monitoring Setup
```bash
# Set up logrotate
cat > /etc/logrotate.d/ldap-analytics << EOF
/path/to/logs/*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    create 0600 user user
}
EOF

# Set up fail2ban for brute force protection
cat > /etc/fail2ban/filter.d/ldap-analytics.conf << EOF
[Definition]
failregex = .*LOGIN_ATTEMPT.*"success": false.*"email": "([^"]*)"
ignoreregex =
EOF
```

## 🔧 Security Configuration

### Role-Based Permissions

| Feature | Admin | Manager | Viewer | Auditor |
|---------|-------|---------|--------|---------|
| View All Data | ✅ | ❌ | ❌ | ❌ |
| View Team Data | ✅ | ✅ | ❌ | ❌ |
| Export Data | ✅ | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ | ✅ |
| Org Charts | ✅ | ✅ | ❌ | ❌ |
| Analytics | ✅ | ✅ | ✅ | ✅ |

### Data Masking Rules

| User Role | Email | Phone | Employee ID | Personal Data |
|-----------|-------|-------|-------------|---------------|
| Admin | None | None | None | None |
| Manager | Partial | Full | Partial | Full |
| Viewer | Full | Full | Full | Full |
| Auditor | Hash | Hash | Hash | Hash |

## ⚠️ Security Best Practices

### 1. Password Security
- **Change default passwords** immediately
- **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
- **Enable password rotation** every 90 days
- **Consider LDAP authentication** integration

### 2. Session Management
- **Set appropriate timeouts** (30-60 minutes)
- **Monitor concurrent sessions**
- **Log session activities**
- **Implement session cleanup**

### 3. Data Access
- **Follow principle of least privilege**
- **Regularly review user permissions**
- **Monitor data exports**
- **Implement data retention policies**

### 4. Infrastructure Security
- **Use HTTPS in production**
- **Implement network segmentation**
- **Regular security updates**
- **Backup audit logs**

### 5. Compliance
- **Regular security audits**
- **Document access procedures**
- **Train users on security policies**
- **Incident response procedures**

## 🚨 Incident Response

### Security Incident Checklist
1. **Identify** the security event
2. **Isolate** affected systems
3. **Investigate** the scope and impact
4. **Remediate** the vulnerability
5. **Document** lessons learned

### Emergency Contacts
- **IT Security Team**: security@redhat.com
- **System Administrator**: admin@redhat.com
- **Compliance Officer**: compliance@redhat.com

## 📞 Support

For security questions or issues:
- **Internal**: Contact IT Security team
- **Technical**: Review audit logs and configuration
- **Emergency**: Follow incident response procedures

---

**⚠️ IMPORTANT**: This dashboard handles sensitive organizational data. All access is logged and monitored. Report any suspicious activity immediately.