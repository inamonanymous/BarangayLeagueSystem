# Frontend Overview

## Overview

The League Management System frontend is a Single Page Application (SPA) built using React 19.

The current interface supports public browsing and Administrator management.
Administrators and Encoders can enter game scores and player statistics.

The frontend communicates with the backend through a REST API and has no direct
database access. It performs UI validation and enables or disables controls based
on available state; the backend remains responsible for enforcing business rules
and authorization.

---

# Goals

The frontend is designed with the following goals:

- Provide a clean and intuitive user experience.
- Maintain a consistent interface across all modules.
- Minimize duplicated UI code through reusable components.
- Support feature-based development for easier maintenance.
- Keep presentation separate from business logic.
- Support responsive layouts for desktop and mobile devices.
- Prepare the codebase for future enhancements such as Dark Mode and Progressive Web App (PWA) support.

---

# Architecture Philosophy

The frontend follows a Feature-Based Architecture.

Instead of organizing files by type (components, pages, hooks, services), the project is organized by business features.

Current feature folders include:

- Authentication
- Players
- Seasons
- Users
- Dashboard

Team, roster, game schedule, results and standings components live under the
Seasons feature. Shared API functions, layout, and tab components live under
`shared`. A season workspace separates these activities into sections.

This approach improves scalability, readability, and maintainability as the application grows.

---

# Communication with Backend

The frontend communicates with the Flask backend using RESTful APIs.

The frontend is responsible for:

- Rendering user interfaces
- Managing client-side interactions
- Form validation
- Displaying API responses
- Managing application state

The backend is responsible for:

- Business rules
- Authentication
- Authorization
- Data persistence
- Database transactions

Business logic shall remain on the backend to ensure consistency and security.

---

# Target Platforms

Version 1 supports:

- Desktop Web Browsers
- Mobile Web Browsers

The primary administrative experience is optimized for desktop users, while viewers may comfortably access league information through mobile devices.

---

# Design Principles

The frontend shall adhere to the following principles:

- Simplicity over complexity.
- Reusability over duplication.
- Composition over inheritance.
- Separation of concerns.
- Consistent user experience.
- Predictable project structure.
- Responsive design by default.

---

# Future Enhancements

The architecture is prepared for future improvements, including:

- Dark Mode
- Progressive Web App (PWA)
- Push Notifications
- JWT Authentication
- Offline Viewing
- Internationalization (i18n)