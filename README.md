# Latina Dance Academy - Online Course Platform

A modern, responsive online course platform for Latin dance education with both public website and admin dashboard interfaces.

## 🎯 Project Overview

This is a complete frontend implementation of an online course platform designed for Latin dance instruction. The platform features a beautiful public website for students and a comprehensive admin dashboard for course management.

## ✨ Features

### Public Website
- **Modern Homepage** with hero section and featured courses
- **Course Catalog** with 6 Latin dance styles (Salsa, Bachata, Merengue, Cha Cha, Rumba, Samba)
- **Individual Course Pages** with 3 levels × 4 sessions structure
- **About Us Page** with team information and company values
- **Photo Gallery** with lightbox functionality
- **Video Gallery** for streaming content
- **Blog Section** for articles and tips
- **Newsletter Subscription** form
- **Tournament Section** for competitions
- **Responsive Design** for mobile, tablet, and desktop

### Admin Dashboard
- **Secure Login System** with session management
- **Dashboard Overview** with analytics and statistics
- **Course Management** - Add, edit, delete courses
- **Session Management** - Manage 3 levels × 4 sessions per course
- **User Management** - View and manage student accounts
- **Photo Gallery Management** - Upload and organize images
- **Video Gallery Management** - Upload and manage video content
- **Blog Post Management** - Create and edit blog content
- **Newsletter Management** - Manage subscriber list
- **Analytics Dashboard** - Charts and performance metrics
- **Responsive Admin Interface** with mobile-friendly navigation

## 🎨 Design Features

- **Modern UI/UX** with clean, professional design
- **Gradient Backgrounds** and smooth animations
- **Interactive Elements** with hover effects and transitions
- **Card-based Layout** for easy content organization
- **Progress Tracking** for course completion
- **Search and Filter** functionality
- **Modal Windows** for forms and content preview
- **Lightbox Gallery** for image viewing
- **Video Player** with streaming controls (no download)
- **Mobile-First** responsive design

## 📁 Project Structure

```
latina-website-herin/
├── index.html                 # Homepage
├── about.html                 # About Us page
├── courses.html               # Course catalog
├── tournaments.html           # Tournament section
├── gallery.html               # Photo gallery
├── blog.html                  # Blog listing
├── styles/
│   ├── main.css              # Main stylesheet
│   └── components.css        # UI components
├── js/
│   └── main.js               # Main JavaScript
├── admin/
│   ├── login.html            # Admin login
│   ├── dashboard.html        # Admin dashboard
│   ├── courses.html          # Course management
│   ├── sessions.html         # Session management
│   ├── users.html            # User management
│   ├── gallery.html          # Gallery management
│   ├── videos.html           # Video management
│   ├── blog.html             # Blog management
│   ├── newsletter.html       # Newsletter management
│   ├── analytics.html        # Analytics dashboard
│   ├── settings.html         # Settings page
│   ├── admin.css             # Admin styles
│   └── admin.js              # Admin functionality
└── README.md                 # Project documentation
```

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (optional, for development)

### Installation
1. Clone or download the project files
2. Open `index.html` in your web browser
3. For admin access, navigate to `admin/login.html`
   - Username: `admin`
   - Password: `admin123`

### Development Setup
For local development with a web server:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js (if you have http-server installed)
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000` in your browser.

## 🎓 Course Structure

The platform is designed for 6 main Latin dance courses:

1. **Salsa Fundamentals** - Beginner friendly
2. **Bachata Sensual** - Romantic and sensual
3. **Merengue Express** - Fast-paced and energetic
4. **Cha Cha Cha** - Energetic and playful
5. **Rumba Passion** - Advanced techniques
6. **Samba Carnival** - Brazilian carnival style

Each course features:
- **3 Levels**: Beginner, Intermediate, Advanced
- **4 Sessions per Level**: 20-30 minutes each
- **Progress Tracking**: Visual progress indicators
- **Video Content**: Streaming-only (no downloads)

## 🛠️ Technical Implementation

### Frontend Technologies
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with Flexbox and Grid
- **JavaScript (ES6+)** - Interactive functionality
- **Font Awesome** - Icons
- **Google Fonts** - Typography (Inter font family)
- **Chart.js** - Analytics charts (admin dashboard)

### Key Features
- **Responsive Design** - Mobile-first approach
- **Progressive Enhancement** - Works without JavaScript
- **Accessibility** - ARIA labels and semantic HTML
- **Performance** - Optimized images and lazy loading
- **Cross-browser** - Compatible with modern browsers

### Admin Features
- **Session Management** - Login/logout functionality
- **Data Tables** - Sortable and searchable content
- **File Upload** - Image and video management
- **Modal Forms** - Add/edit content
- **Real-time Updates** - Dynamic content management
- **Export Functionality** - Data export capabilities

## 🎨 Design System

### Color Palette
- **Primary**: #e74c3c (Red)
- **Secondary**: #667eea (Blue)
- **Accent**: #764ba2 (Purple)
- **Text**: #333333 (Dark Gray)
- **Background**: #f8f9fa (Light Gray)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700
- **Responsive**: Scales appropriately on all devices

### Components
- **Buttons**: Primary, Secondary, Outline variants
- **Cards**: Course cards, team cards, feature cards
- **Forms**: Input fields, textareas, selects
- **Modals**: Overlay dialogs for forms and content
- **Tables**: Data tables with sorting and search
- **Navigation**: Responsive navbar and sidebar

## 📱 Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🔒 Security Features

- **Admin Authentication** - Login system with session management
- **Input Validation** - Form validation and sanitization
- **XSS Prevention** - Content security measures
- **CSRF Protection** - Cross-site request forgery prevention

## 🚀 Deployment

The project is ready for deployment to any static hosting service:

- **Netlify** - Drag and drop deployment
- **Vercel** - Git-based deployment
- **GitHub Pages** - Free hosting for public repositories
- **AWS S3** - Scalable static hosting
- **Firebase Hosting** - Google's hosting solution

## 🔧 Customization

### Adding New Courses
1. Update the course data in the relevant HTML files
2. Add course images to the appropriate directories
3. Update the course grid in `courses.html`
4. Add course-specific pages in the `courses/` directory

### Modifying Styles
- Main styles: `styles/main.css`
- Component styles: `styles/components.css`
- Admin styles: `admin/admin.css`

### Adding Functionality
- Main JavaScript: `js/main.js`
- Admin JavaScript: `admin/admin.js`

## 📊 Analytics Integration

The admin dashboard includes:
- **User Registration Trends** - Line chart
- **Course Completion Rates** - Doughnut chart
- **Revenue Analytics** - Bar charts
- **User Activity** - Real-time tracking
- **Export Capabilities** - Data export in various formats

## 🤝 Contributing

This is a frontend-only implementation. For backend integration:

1. **API Endpoints** - Create RESTful APIs for data management
2. **Database** - Set up user, course, and content databases
3. **Authentication** - Implement secure user authentication
4. **File Upload** - Set up file storage for images and videos
5. **Email Service** - Newsletter and notification system

## 📄 License

This project is created for educational and demonstration purposes. Feel free to use and modify for your own projects.

## 📞 Support

For questions or support:
- Email: info@latinadanceacademy.com
- Phone: +1 (555) 123-4567

---

**Note**: This is a frontend-only implementation. Backend development and database integration would be required for a production environment.


