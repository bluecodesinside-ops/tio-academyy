/* ===== TIO ACADEMY - CORE JAVASCRIPT SYSTEM ===== */
/* Enterprise-level JavaScript architecture */

'use strict';

/**
 * Core Application Namespace
 * Provides global utilities and manages application state
 */
window.TioAcademy = window.TioAcademy || {};

/**
 * Utility Functions
 * Common helper functions used throughout the application
 */
TioAcademy.Utils = {
  /**
   * Throttle function execution
   * @param {Function} func - Function to throttle
   * @param {number} limit - Throttle limit in milliseconds
   * @returns {Function} Throttled function
   */
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Debounce function execution
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in milliseconds
   * @param {boolean} immediate - Execute immediately
   * @returns {Function} Debounced function
   */
  debounce(func, wait, immediate) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      const later = function() {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      const callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  },

  /**
   * Sanitize filename for download
   * @param {string} filename - Original filename
   * @returns {string} Sanitized filename
   */
  sanitizeFilename(filename) {
    return filename.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'download';
  },

  /**
   * Get file extension from URL
   * @param {string} url - File URL
   * @returns {string} File extension
   */
  getFileExtension(url) {
    const extension = url.split('.').pop().toLowerCase();
    const validExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'webm'];
    return validExtensions.includes(extension) ? `.${extension}` : '.jpg';
  },

  /**
   * Create download link and trigger download
   * @param {string} url - File URL
   * @param {string} filename - Desired filename
   */
  downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = this.sanitizeFilename(filename) + this.getFileExtension(url);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  /**
   * Check if device supports touch
   * @returns {boolean} True if touch is supported
   */
  isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  },

  /**
   * Check if user prefers reduced motion
   * @returns {boolean} True if reduced motion is preferred
   */
  prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
};

/**
 * Animation Manager
 * Handles scroll-triggered animations and performance optimization
 */
TioAcademy.AnimationManager = {
  observers: new Map(),

  /**
   * Initialize animation system
   */
  init() {
    this.setupScrollAnimations();
    this.setupPerformanceOptimizations();
  },

  /**
   * Setup scroll-triggered animations
   */
  setupScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          
          // Handle grid animations
          if (entry.target.classList.contains('grid')) {
            this.animateGridChildren(entry.target);
          }
        }
      });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.scroll-reveal');
    animateElements.forEach(el => observer.observe(el));

    this.observers.set('scroll', observer);
  },

  /**
   * Animate grid children with stagger effect
   * @param {Element} grid - Grid container element
   */
  animateGridChildren(grid) {
    const children = Array.from(grid.children);
    children.forEach((child, index) => {
      setTimeout(() => {
        child.classList.add('animate-in');
      }, index * 100);
    });
  },

  /**
   * Setup performance optimizations
   */
  setupPerformanceOptimizations() {
    // Pause animations when tab is not visible
    document.addEventListener('visibilitychange', () => {
      const animatedElements = document.querySelectorAll('[class*="animate"]');
      
      if (document.hidden) {
        animatedElements.forEach(el => {
          el.style.animationPlayState = 'paused';
        });
      } else {
        animatedElements.forEach(el => {
          el.style.animationPlayState = 'running';
        });
      }
    });

    // Add GPU acceleration to animated elements
    const gpuElements = document.querySelectorAll('.gallery-card, .feature-card, .course-card');
    gpuElements.forEach(el => {
      el.style.transform = 'translateZ(0)';
      el.style.backfaceVisibility = 'hidden';
      el.style.perspective = '1000px';
    });
  },

  /**
   * Clean up observers
   */
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }
};

/**
 * Navigation Manager
 * Handles navigation behavior and scroll effects
 */
TioAcademy.NavigationManager = {
  navbar: null,
  lastScrollY: 0,

  /**
   * Initialize navigation system
   */
  init() {
    this.navbar = document.querySelector('.navbar');
    if (!this.navbar) return;

    this.setupScrollEffects();
    this.setupActiveStates();
  },

  /**
   * Setup scroll-based navigation effects
   */
  setupScrollEffects() {
    const handleScroll = TioAcademy.Utils.throttle(() => {
      const currentScrollY = window.scrollY;
      
      // Add scrolled class
      if (currentScrollY > 100) {
        this.navbar.classList.add('navbar--scrolled');
      } else {
        this.navbar.classList.remove('navbar--scrolled');
      }
      
      // Hide/show navbar on scroll direction
      if (currentScrollY > this.lastScrollY && currentScrollY > 200) {
        this.navbar.style.transform = 'translateY(-100%)';
      } else {
        this.navbar.style.transform = 'translateY(0)';
      }
      
      this.lastScrollY = currentScrollY;
    }, 16);

    window.addEventListener('scroll', handleScroll, { passive: true });
  },

  /**
   * Setup active navigation states
   */
  setupActiveStates() {
    const navLinks = document.querySelectorAll('.navbar__link');
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('navbar__link--active');
      }
    });
  }
};

/**
 * Form Manager
 * Handles form interactions and validation
 */
TioAcademy.FormManager = {
  /**
   * Initialize form system
   */
  init() {
    this.setupFormEnhancements();
    this.setupFormValidation();
  },

  /**
   * Setup form interaction enhancements
   */
  setupFormEnhancements() {
    const inputs = document.querySelectorAll('.form-input');
    
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        input.parentElement?.classList.add('focused');
      });
      
      input.addEventListener('blur', () => {
        input.parentElement?.classList.remove('focused');
      });
    });
  },

  /**
   * Setup basic form validation
   */
  setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
          if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
          } else {
            field.classList.remove('error');
          }
        });
        
        if (!isValid) {
          e.preventDefault();
        }
      });
    });
  }
};

/**
 * Performance Monitor
 * Monitors and optimizes application performance
 */
TioAcademy.PerformanceMonitor = {
  /**
   * Initialize performance monitoring
   */
  init() {
    this.setupLazyLoading();
    this.setupImageOptimization();
    this.monitorPerformance();
  },

  /**
   * Setup lazy loading for images
   */
  setupLazyLoading() {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            const dataSrc = img.getAttribute('data-src');
            
            if (dataSrc) {
              img.src = dataSrc;
              img.removeAttribute('data-src');
              img.classList.remove('lazy');
              imageObserver.unobserve(img);
            }
          }
        });
      }, {
        rootMargin: '100px'
      });

      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  },

  /**
   * Setup image optimization and error handling
   */
  setupImageOptimization() {
    document.addEventListener('error', (e) => {
      if (e.target.tagName === 'IMG') {
        const img = e.target;
        const container = img.closest('.gallery-card__image');
        
        if (container) {
          container.innerHTML = `
            <div class="image-error">
              <i class="fas fa-image"></i>
              <p>Image unavailable</p>
            </div>
          `;
        }
      }
    }, true);
  },

  /**
   * Monitor performance metrics
   */
  monitorPerformance() {
    if ('performance' in window) {
      window.addEventListener('load', () => {
        const loadTime = performance.now();
        console.log(`Page loaded in ${Math.round(loadTime)}ms`);
        
        // Report Core Web Vitals if available
        if ('web-vitals' in window) {
          // Implementation would go here for production monitoring
        }
      });
    }
  }
};

/**
 * Application Initializer
 * Coordinates the initialization of all systems
 */
TioAcademy.App = {
  /**
   * Initialize the application
   */
  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.bootstrap());
    } else {
      this.bootstrap();
    }
  },

  /**
   * Bootstrap all application systems
   */
  bootstrap() {
    try {
      // Initialize core systems
      TioAcademy.AnimationManager.init();
      TioAcademy.NavigationManager.init();
      TioAcademy.FormManager.init();
      TioAcademy.PerformanceMonitor.init();
      
      // Initialize page-specific components
      this.initializePageComponents();
      
      // Mark application as ready
      document.body.classList.add('app-ready');
      
      console.log('Tio Academy application initialized successfully');
    } catch (error) {
      console.error('Error initializing Tio Academy application:', error);
    }
  },

  /**
   * Initialize page-specific components
   */
  initializePageComponents() {
    const currentPage = document.body.getAttribute('data-page');
    
    switch (currentPage) {
      case 'gallery':
        if (typeof TioAcademy.GalleryManager !== 'undefined') {
          TioAcademy.GalleryManager.init();
        }
        break;
      case 'home':
        this.initializeHomePage();
        break;
      default:
        // Initialize common components
        this.initializeCommonComponents();
        break;
    }
  },

  /**
   * Initialize home page specific features
   */
  initializeHomePage() {
    this.setupCounterAnimations();
    this.setupVideoPreview();
  },

  /**
   * Initialize common components across all pages
   */
  initializeCommonComponents() {
    this.setupSmoothScrolling();
    this.setupScrollToTop();
  },

  /**
   * Setup counter animations for stats
   */
  setupCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number, .hero__stat-number');
    
    const animateCounter = (counter) => {
      const target = parseInt(counter.textContent.replace(/[^\d]/g, ''));
      const duration = 2000;
      const start = performance.now();
      
      const animate = (currentTime) => {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(target * easeOutQuart);
        
        // Preserve original formatting
        const originalText = counter.textContent;
        const suffix = originalText.replace(/[\d]/g, '');
        counter.textContent = current + suffix;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      
      requestAnimationFrame(animate);
    };
    
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          setTimeout(() => animateCounter(entry.target), 300);
          counterObserver.unobserve(entry.target);
        }
      });
    });
    
    counters.forEach(counter => counterObserver.observe(counter));
  },

  /**
   * Setup video preview functionality
   */
  setupVideoPreview() {
    const videoPreview = document.querySelector('.video-preview');
    if (videoPreview) {
      videoPreview.addEventListener('click', () => {
        // Placeholder for video modal functionality
        console.log('Video preview clicked');
      });
    }
  },

  /**
   * Setup smooth scrolling for anchor links
   */
  setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        
        const targetId = anchor.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          const offsetTop = targetElement.offsetTop - 100;
          
          window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
          });
        }
      });
    });
  },

  /**
   * Setup scroll to top functionality
   */
  setupScrollToTop() {
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollToTopBtn.className = 'scroll-to-top';
    scrollToTopBtn.setAttribute('aria-label', 'Scroll to top');
    
    // Styles
    Object.assign(scrollToTopBtn.style, {
      position: 'fixed',
      bottom: '30px',
      right: '30px',
      width: '50px',
      height: '50px',
      background: 'var(--color-accent)',
      border: 'none',
      borderRadius: '50%',
      color: 'white',
      fontSize: '18px',
      cursor: 'pointer',
      opacity: '0',
      visibility: 'hidden',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      zIndex: 'var(--z-index-fixed)',
      boxShadow: 'var(--shadow-lg)'
    });
    
    document.body.appendChild(scrollToTopBtn);
    
    // Show/hide based on scroll position
    const handleScroll = TioAcademy.Utils.throttle(() => {
      if (window.scrollY > 500) {
        scrollToTopBtn.style.opacity = '1';
        scrollToTopBtn.style.visibility = 'visible';
      } else {
        scrollToTopBtn.style.opacity = '0';
        scrollToTopBtn.style.visibility = 'hidden';
      }
    }, 16);
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Smooth scroll to top
    scrollToTopBtn.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }
};

/**
 * Error Handler
 * Global error handling and reporting
 */
TioAcademy.ErrorHandler = {
  /**
   * Initialize error handling
   */
  init() {
    this.setupGlobalErrorHandling();
    this.setupUnhandledRejectionHandling();
  },

  /**
   * Setup global error handling
   */
  setupGlobalErrorHandling() {
    window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
      // In production, you would send this to your error reporting service
    });
  },

  /**
   * Setup unhandled promise rejection handling
   */
  setupUnhandledRejectionHandling() {
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      // In production, you would send this to your error reporting service
    });
  }
};

// Initialize the application
TioAcademy.App.init();
