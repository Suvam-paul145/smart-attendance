# Issue Report: Insert College Name in Registration Form

## Summary

Add a **College Name** field to the student and teacher registration forms to allow users to specify which educational institution they belong to.

## Problem Statement

Currently, the registration form (`frontend/src/pages/Register.jsx`) collects the following information:
- **Common fields**: Name, Email, Password
- **Student-specific fields**: Branch, Year, Roll Number
- **Teacher-specific fields**: Employee ID, Phone Number

However, there is **no field to capture the user's college/institution name**. This is a critical piece of information for:
- Multi-institution deployments
- Generating institution-specific reports
- Student and teacher identification within a specific college

## Proposed Solution

### Frontend Changes

1. **Add College Name field to `Register.jsx`**:
   - Add a new text input field for "College Name" in the registration form
   - This should be a common field for both students and teachers
   - Include an appropriate icon (e.g., `Building` or `School` from lucide-react)

2. **Update form state**:
   ```javascript
   const [formData, setFormData] = useState({
     name: "",
     email: "",
     password: "",
     collegeName: "",  // New field
     branch: "",
     employee_id: "",
     phone: "",
     roll: "",
     year: ""
   });
   ```

3. **Update payload submission**:
   ```javascript
   const payload = {
     role,
     name: formData.name,
     email: formData.email,
     password: formData.password,
     college_name: formData.collegeName,  // New field
     // ... other fields
   };
   ```

### Backend Changes

1. **Update `RegisterRequest` schema** (`server/backend-api/app/schemas/auth.py`):
   ```python
   class RegisterRequest(BaseModel):
       role: str
       name: str
       email: EmailStr
       password: constr(min_length=6, max_length=72)
       college_name: str  # New required field for multi-institution support
       # ... existing fields
   ```
   
   > **Note:** For single-institution deployments, this field can be made optional (`Optional[str] = None`) or pre-filled with a default value in the frontend.

2. **Update user model and database schema** to include college_name field

3. **Update profile endpoints** to return and accept college_name

### UI Mockup

The new field should be placed after the email field and before role-specific fields:

```
┌─────────────────────────────────────┐
│  Full Name                    [👤]  │
├─────────────────────────────────────┤
│  Email Address                [📧]  │
├─────────────────────────────────────┤
│  College Name                 [🏫]  │  ← NEW FIELD
├─────────────────────────────────────┤
│  [Role-specific fields...]          │
├─────────────────────────────────────┤
│  Password                     [🔒]  │
└─────────────────────────────────────┘
```

## Acceptance Criteria

- [ ] College Name field is visible on both student and teacher registration forms
- [ ] Field validation is implemented:
  - **Multi-institution deployments**: Required field with proper error messaging
  - **Single-institution deployments**: Optional field or pre-filled with institution name
- [ ] College name is saved to the database upon registration
- [ ] College name is displayed on user profile pages
- [ ] College name is editable in settings/profile pages
- [ ] Backend API accepts and returns college_name field

## Technical Notes

- The field should use the `Building` icon from `lucide-react`
- Consider adding autocomplete functionality for known colleges in future iterations
- May need to add a colleges collection/table for standardized college names

## Files to Modify

### Frontend
- `frontend/src/pages/Register.jsx`
- `frontend/src/pages/Settings.jsx`
- `frontend/src/students/pages/StudentProfile.jsx`

### Backend
- `server/backend-api/app/schemas/auth.py`
- `server/backend-api/app/api/routes/auth.py`
- Database models/schemas

## Priority

**Medium** - This is a useful feature for multi-institution deployments but not critical for core functionality.

## Labels

`enhancement`, `frontend`, `backend`, `registration`
