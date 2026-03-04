# Chama Admin Console - Product Requirements Document

## 1. Overview

**Project Name:** Chama Admin Console  
**Type:** Web Application (Next.js)  
**Core Functionality:** Super admin platform to manage chamas, users, payments, and platform settings  
**Target Users:** Platform administrators, super admins

---

## 2. Goals

- Enable super admins to onboard and manage chamas
- Provide platform-wide analytics and reporting
- Manage user roles and permissions
- Configure platform settings (fees, payments, features)
- Monitor and control platform health

---

## 3. User Roles

| Role | Description |
|------|-------------|
| **SUPER_ADMIN** | Full platform access, can manage all chamas |
| **PLATFORM_ADMIN** | Administrative access, limited to assigned regions |

---

## 4. Core Features

### 4.1 Authentication & Security

- **Login:** Email + password with 2FA
- **Session Management:** JWT tokens with refresh
- **Audit Logging:** All admin actions logged

### 4.2 Dashboard

- **Overview Cards:**
  - Total chamas (active/inactive)
  - Total members
  - Total transactions volume (KES)
  - Platform revenue
  
- **Charts:**
  - Monthly chama growth (line)
  - Transaction volume (bar)
  - Top performing chamas (table)
  - Regional distribution (pie)

- **Recent Activity:**
  - New chama registrations
  - Large transactions
  - System alerts

### 4.3 Chama Management

**List View:**
- Search by name, code, region
- Filter by status (active/suspended/pending)
- Sort by date, members, volume
- Bulk actions (activate, suspend)

**Chama Detail:**
- Profile (name, code, region, registration)
- Members list with roles
- Financial summary (contributions, loans, treasury)
- Transaction history
- Activity log

**Onboarding Flow:**
1. Enter chama details (name, code, region)
2. Set subscription tier (free/pro/enterprise)
3. Configure chama-specific settings
4. Invite initial admin (chair)
5. Send welcome email

**Chama Settings:**
- Enable/disable features
- Set custom fees
- Configure M-Pesa (if using own till)
- Branding (logo, colors)

### 4.4 Member Management

**Global Member Search:**
- Search across all chamas
- Filter by chama, role, status

**Member Actions:**
- View profile
- Transfer between chamas
- Suspend/activate
- View transaction history

### 4.5 Transaction Monitoring

- All platform transactions
- Filter by type, status, chama, date
- Export to CSV/Excel
- Dispute management

### 4.6 Financial Management

**Platform Revenue:**
- Monthly revenue by source
- Fee collection summary
- Payout status

**Payouts:**
- Pending payouts to chamas
- Approve/reject manual payouts
- Batch processing

### 4.7 Platform Settings

**General:**
- Platform name, logo
- Support contact

**Fees:**
- Platform fee percentage (default 2%)
- Minimum transaction fee
- Subscription pricing

**Payment:**
- M-Pesa credentials
- Pesapal credentials
- Payment mode (central/hybrid)
- Settlement timing

**Features:**
- Enable/disable marketplace
- Enable/disable loans
- Enable/disable subscriptions

**Regions:**
- Add/edit regions
- Assign admins per region

### 4.8 Reports & Analytics

**Pre-built Reports:**
- Chama performance
- Member engagement
- Revenue breakdown
- Loan portfolio health

**Custom Reports:**
- Date range selection
- Filter by chama/region
- Export options

### 4.9 Audit Logs

- All admin actions with timestamps
- Filter by admin, action, date
- Export for compliance

---

## 5. Technical Architecture

### Stack
- **Framework:** Next.js 15 (App Router)
- **UI:** React + Tailwind CSS
- **Charts:** Recharts
- **Tables:** TanStack Table
- **Forms:** React Hook Form + Zod
- **State:** React Query + Zustand
- **API:** REST from microservices

### Pages Structure
```
/login
/dashboard
/chamas
  /[id]
  /onboard
/members
/transactions
/financial
/settings
  /general
  /fees
  /payments
  /features
/reports
/audit-logs
```

### API Integration
- Core Service: Members, Contributions, Loans
- Listings Marketplace:, Orders
- Payments: M-Pesa, Pesapal
- Notifications: Push, SMS

---

## 6. UI/UX Guidelines

### Design System
- **Color Palette:**
  - Primary: `#1a56db` (Blue)
  - Success: `#16a34a` (Green)
  - Warning: `#ca8a04` (Yellow)
  - Error: `#dc2626` (Red)
  - Background: `#f8fafc`
  
- **Typography:**
  - Headings: Inter (Bold)
  - Body: Inter (Regular)
  - Monospace: JetBrains Mono

- **Spacing:** 4px base unit (4, 8, 12, 16, 24, 32, 48, 64)

### Components
- Cards with subtle shadows
- Tables with sorting, filtering, pagination
- Modal dialogs for actions
- Toast notifications
- Loading skeletons

### Responsive
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

---

## 7. API Endpoints

### Authentication
```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
POST   /api/auth/2fa/verify
```

### Chamas
```
GET    /api/admin/chamas
POST   /api/admin/chamas
GET    /api/admin/chamas/{id}
PATCH  /api/admin/chamas/{id}
DELETE /api/admin/chamas/{id}
POST   /api/admin/chamas/{id}/activate
POST   /api/admin/chamas/{id}/suspend
```

### Members
```
GET    /api/admin/members
GET    /api/admin/members/{id}
PATCH  /api/admin/members/{id}
POST   /api/admin/members/{id}/transfer
```

### Transactions
```
GET    /api/admin/transactions
GET    /api/admin/transactions/{id}
POST   /api/admin/transactions/refund
```

### Settings
```
GET    /api/admin/settings
PATCH  /api/admin/settings
GET    /api/admin/settings/fees
PATCH  /api/admin/settings/fees
```

### Analytics
```
GET    /api/admin/analytics/overview
GET    /api/admin/analytics/chamas
GET    /api/admin/analytics/revenue
```

### Audit
```
GET    /api/admin/audit-logs
```

---

## 8. Milestones

1. **Phase 1 - Foundation**
   - Project setup
   - Authentication
   - Dashboard
   
2. **Phase 2 - Chama Management**
   - List/Detail views
   - Onboarding flow
   - Settings

3. **Phase 3 - Financial**
   - Transactions
   - Revenue tracking
   - Payouts

4. **Phase 4 - Reports**
   - Analytics charts
   - Custom reports
   - Export functionality

---

## 9. Success Metrics

- [ ] Admins can onboard new chamas in < 5 minutes
- [ ] Dashboard loads in < 2 seconds
- [ ] All CRUD operations functional
- [ ] Audit logging complete
- [ ] Mobile responsive

---

## 10. Future Considerations

- Multi-tenancy support
- White-label admin for chama admins
- API access for third-party integrations
- Mobile admin app
