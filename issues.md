# Potential Issues and Enhancements for Smart Attendance System

This document contains a comprehensive list of issues and enhancements that can be inferred from analyzing the codebase.

---

## 🔴 High Priority Issues

### 1. Missing College/Institution Name in Registration
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`, `server/backend-api/app/schemas/auth.py`  
**Description:** The registration form does not collect college/institution name, which is essential for multi-institution deployments and proper user identification.

### 2. Forgot Password Functionality Not Implemented
**Type:** Bug/Enhancement  
**Affected Files:** `frontend/src/pages/Login.jsx`  
**Description:** The "Forgot password?" link on the login page (`Login.jsx:148`) is currently a placeholder (`to="#"`) and doesn't link to an actual password reset flow. Users have no way to recover their accounts.

### 3. Hardcoded User Greeting in Dashboard
**Type:** Bug  
**Affected Files:** `frontend/src/pages/Dashboard.jsx:50`  
**Description:** The dashboard displays "Good morning, Alex" as a hardcoded greeting instead of using the actual logged-in user's name.

### 4. Twitter/X OAuth Button Not Functional
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Login.jsx:83-86`  
**Description:** The Twitter login button is displayed on the login page but has no onClick handler or actual OAuth implementation.

---

## 🟡 Medium Priority Issues

### 5. Missing Email Validation on Registration
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** While the backend uses EmailStr validation, the frontend doesn't provide real-time email format validation or feedback to users.

### 6. No Password Strength Indicator
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** The registration form lacks a password strength indicator. Users don't receive feedback on password security (minimum 6 characters, complexity requirements).

### 7. Missing Form Validation Messages
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** The registration form doesn't show individual field validation errors. Only a generic error message is displayed after submission fails.

### 8. Hardcoded Date/Time in Dashboard
**Type:** Bug  
**Affected Files:** `frontend/src/pages/Dashboard.jsx:51`  
**Description:** "Monday, September 23 • 08:45" is hardcoded instead of displaying the actual current date and time.

### 9. Static Attendance Statistics
**Type:** Bug  
**Affected Files:** `frontend/src/pages/Dashboard.jsx:75-98`  
**Description:** The attendance rate (94%), absent count (7), and late arrivals (3) appear to be static values instead of being fetched from the API.

### 10. Refresh Button Not Functional in AddStudents
**Type:** Bug  
**Affected Files:** `frontend/src/pages/AddStudents.jsx:94-97`  
**Description:** The "Refresh" button in the AddStudents page doesn't have an onClick handler and won't refresh the student list.

### 11. Search Not Implemented in AddStudents
**Type:** Bug  
**Affected Files:** `frontend/src/pages/AddStudents.jsx:110-116`  
**Description:** The search input in AddStudents page doesn't filter students - it's just a UI element without functionality.

### 12. "Verify All Visible" Button Not Functional
**Type:** Bug  
**Affected Files:** `frontend/src/pages/AddStudents.jsx:98-101`  
**Description:** The "Verify all visible" button doesn't have an onClick handler to batch verify students.

### 13. Year Filter Not Functional in AddStudents
**Type:** Bug  
**Affected Files:** `frontend/src/pages/AddStudents.jsx:137-147`  
**Description:** The year dropdown filter doesn't actually filter students by year.

---

## 🟢 Low Priority / Enhancement Issues

### 14. Add Department/Section Field for Students
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`, Backend schemas  
**Description:** Add a section/division field (e.g., Section A, Section B) to further categorize students within a branch and year.

### 15. Add Profile Picture Upload During Registration
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** Allow users to upload a profile picture during registration instead of requiring them to do it later in settings.

### 16. Add Face Image Upload During Student Registration
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** For students, provide an option to upload face image during registration to streamline the onboarding process.

### 17. Implement Remember Me Functionality
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Login.jsx:142-147`  
**Description:** The "Remember me" checkbox exists but doesn't persist login state across browser sessions.

### 18. Add Terms and Conditions Acceptance
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** Add a checkbox for users to accept Terms of Service and Privacy Policy during registration.

### 19. Add Phone Number Field for Students
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`, Backend schemas  
**Description:** Currently phone number is only collected for teachers. Consider adding it for students for notifications.

### 20. Add Parent/Guardian Contact for Students
**Type:** Enhancement  
**Affected Files:** Registration and Profile pages  
**Description:** Add parent/guardian contact information for students to enable sending attendance alerts to parents.

### 21. Add Batch/Admission Year Field
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** Add admission year/batch field to distinguish students who may share roll numbers across different batches.

### 22. Edit Details Button Disabled
**Type:** Bug/Enhancement  
**Affected Files:** `frontend/src/students/pages/StudentProfile.jsx:129`  
**Description:** The "Edit details" button has `cursor-not-allowed` class and doesn't allow students to edit their profile information.

### 23. Add Loading States for API Calls
**Type:** Enhancement  
**Affected Files:** Multiple pages  
**Description:** Several pages lack proper loading indicators when fetching or submitting data.

### 24. Add Confirmation Before Deleting Subject
**Type:** Enhancement  
**Affected Files:** `frontend/src/students/pages/StudentProfile.jsx:305-309`  
**Description:** While there is a confirm dialog, it could be improved with a more user-friendly modal component.

### 25. Add Date of Birth Field
**Type:** Enhancement  
**Affected Files:** Registration and Profile pages  
**Description:** Collect student date of birth for age verification and additional identification.

### 26. Add Gender Field
**Type:** Enhancement  
**Affected Files:** Registration and Profile pages  
**Description:** Add optional gender field for demographic data and addressing users appropriately.

### 27. Add Address Field
**Type:** Enhancement  
**Affected Files:** Registration and Profile pages  
**Description:** Collect student/teacher address for administrative purposes.

### 28. Add Department Field for Teachers
**Type:** Enhancement  
**Affected Files:** `frontend/src/pages/Register.jsx`  
**Description:** Add a department field for teachers (e.g., Computer Science Dept, Mathematics Dept).

---

## 🔧 Technical/Code Quality Issues

### 29. Typo in Login.jsx Variable Name
**Type:** Bug  
**Affected Files:** `frontend/src/pages/Login.jsx:11`  
**Description:** Variable is named `setRemeber` instead of `setRemember` (typo).

### 30. Console.log Statements in Production Code
**Type:** Code Quality  
**Affected Files:** Multiple files  
**Description:** There are `console.log` statements in:
- `Login.jsx:41`
- `Settings.jsx:96`
- `StudentProfile.jsx:78` (commented)
These should be removed or replaced with proper logging.

### 31. Missing Error Boundaries
**Type:** Enhancement  
**Affected Files:** React components  
**Description:** The app doesn't implement React Error Boundaries to gracefully handle component errors.

### 32. No Input Sanitization on Frontend
**Type:** Security  
**Affected Files:** All form components  
**Description:** User inputs should be sanitized before sending to the backend to prevent potential XSS or injection attacks.

### 33. Static Profile Initials Fallback
**Type:** Bug  
**Affected Files:** `frontend/src/pages/Settings.jsx:59`  
**Description:** The `getInitials` function returns "AJ" as default instead of something more generic or derived from the user's email.

### 34. Missing PropTypes/TypeScript
**Type:** Code Quality  
**Affected Files:** All React components  
**Description:** Components lack PropTypes validation or TypeScript types, making them prone to runtime errors.

### 35. No Unit Tests
**Type:** Testing  
**Affected Files:** N/A  
**Description:** The repository appears to lack unit tests for both frontend and backend code.

---

## 📱 Accessibility Issues

### 36. Missing Form Labels Association
**Type:** Accessibility  
**Affected Files:** Form components  
**Description:** Some form labels may not be properly associated with their inputs using `htmlFor` attribute.

### 37. Missing ARIA Labels
**Type:** Accessibility  
**Affected Files:** Various components  
**Description:** Interactive elements like icon-only buttons lack proper ARIA labels for screen readers.

### 38. Color Contrast Issues
**Type:** Accessibility  
**Affected Files:** Various components  
**Description:** Some text colors may not meet WCAG contrast requirements (e.g., light gray text on white backgrounds).

---

## 🔒 Security Issues

### 39. Token Storage in localStorage
**Type:** Security  
**Affected Files:** `frontend/src/pages/Login.jsx:43-44`  
**Description:** Authentication tokens are stored in localStorage which is vulnerable to XSS attacks. Consider using httpOnly cookies.

### 40. No Rate Limiting Indication
**Type:** Security  
**Affected Files:** Login and Registration pages  
**Description:** No visual indication or handling for rate-limited requests to prevent brute force attacks.

---

## Summary

| Priority | Count |
|----------|-------|
| 🔴 High | 4 |
| 🟡 Medium | 9 |
| 🟢 Low/Enhancement | 14 |
| 🔧 Technical | 7 |
| 📱 Accessibility | 3 |
| 🔒 Security | 2 |
| **Total** | **39** |

---

## Contributing

If you'd like to work on any of these issues, please:
1. Check if an issue already exists in the GitHub Issues tab
2. Create a new issue with the appropriate labels
3. Reference this document in your issue description
4. Follow the contribution guidelines in `CONTRIBUTING.md`
