/* ===== TIO ACADEMY - ENTERPRISE GALLERY SYSTEM ===== */

'use strict';

/**
 * Main Gallery Controller
 */
class GalleryController {
  constructor() {
    this.lightbox = new LightboxModal();
    this.currentSection = 'photos';
    this.init();
  }

  init() {
    this.setupTabSwitching();
    this.setupGalleryInteractions();
    this.setupFilterSystem();
  }

  setupTabSwitching() {
    const tabs = document.querySelectorAll('.gallery-nav__tab');
    const sections = document.querySelectorAll('.gallery-section');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        
        tabs.forEach(t => t.classList.remove('gallery-nav__tab--active'));
        sections.forEach(s => s.classList.remove('gallery-section--active'));
        
        tab.classList.add('gallery-nav__tab--active');
        document.getElementById(target)?.classList.add('gallery-section--active');
        
        this.currentSection = target;
      });
    });
  }

  setupGalleryInteractions() {
    document.addEventListener('click', (e) => {
      const expandBtn = e.target.closest('[data-action="expand"]');
      const downloadBtn = e.target.closest('[data-action="download"]');
      
      if (expandBtn) {
        e.preventDefault();
        this.openLightbox(expandBtn);
      }
      
      if (downloadBtn) {
        e.preventDefault();
        this.downloadItem(downloadBtn);
      }
    });
  }

  setupFilterSystem() {
    const filters = document.querySelectorAll('.gallery-nav__filter');
    
    filters.forEach(filter => {
      filter.addEventListener('click', (e) => {
        e.preventDefault();
        filter.classList.add('loading');
        
        setTimeout(() => {
          window.location.href = filter.href;
        }, 200);
      });
    });
  }

  openLightbox(trigger) {
    const item = trigger.closest('.gallery-item');
    const section = trigger.closest('.gallery-section');
    const items = this.collectItems(section);
    const index = Array.from(section.querySelectorAll('.gallery-item')).indexOf(item);
    
    this.lightbox.open(items, index);
  }

  downloadItem(trigger) {
    const src = trigger.dataset.src;
    const title = trigger.dataset.title;
    
    if (src && title) {
      this.downloadFile(src, title);
      this.showDownloadFeedback(trigger);
    }
  }

  collectItems(section) {
    return Array.from(section.querySelectorAll('.gallery-item')).map(item => ({
      src: item.dataset.src,
      title: item.dataset.title || '',
      description: item.dataset.description || '',
      type: item.dataset.type || 'image'
    }));
  }

  downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.jpg';
    link.target = '_blank';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  showDownloadFeedback(trigger) {
    const original = trigger.innerHTML;
    trigger.innerHTML = '<i class="fas fa-check"></i>';
    trigger.style.background = '#22c55e';
    
    setTimeout(() => {
      trigger.innerHTML = original;
      trigger.style.background = '';
    }, 1500);
  }
}

/**
 * Professional Lightbox Modal
 */
class LightboxModal {
  constructor() {
    this.isOpen = false;
    this.currentIndex = 0;
    this.items = [];
    this.createModal();
    this.bindEvents();
  }

  createModal() {
    const modal = document.createElement('div');
    modal.id = 'gallery-lightbox';
    modal.className = 'lightbox';
    modal.innerHTML = `
      <div class="lightbox__container">
        <div class="lightbox__header">
          <div class="lightbox__counter">1 of 1</div>
          <div class="lightbox__controls">
            <button class="lightbox__control-btn download-btn">
              <i class="fas fa-download"></i>
            </button>
            <button class="lightbox__control-btn close-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        
        <div class="lightbox__media-container">
          <img class="lightbox__media" style="display: none;">
          <video class="lightbox__media" controls playsinline webkit-playsinline x5-playsinline style="display: none;">
            <source type="video/mp4">
          </video>
        </div>
        
        <button class="lightbox__nav-btn lightbox__nav-btn--prev">
          <i class="fas fa-chevron-left"></i>
        </button>
        
        <button class="lightbox__nav-btn lightbox__nav-btn--next">
          <i class="fas fa-chevron-right"></i>
        </button>
        
        <div class="lightbox__footer">
          <h3 class="lightbox__title"></h3>
          <p class="lightbox__description"></p>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    this.modal = modal;
    this.cacheElements();
  }

  cacheElements() {
    this.elements = {
      image: this.modal.querySelector('img'),
      video: this.modal.querySelector('video'),
      title: this.modal.querySelector('.lightbox__title'),
      description: this.modal.querySelector('.lightbox__description'),
      counter: this.modal.querySelector('.lightbox__counter'),
      prevBtn: this.modal.querySelector('.lightbox__nav-btn--prev'),
      nextBtn: this.modal.querySelector('.lightbox__nav-btn--next'),
      closeBtn: this.modal.querySelector('.close-btn'),
      downloadBtn: this.modal.querySelector('.download-btn')
    };
  }

  bindEvents() {
    this.elements.closeBtn.addEventListener('click', () => this.close());
    this.elements.prevBtn.addEventListener('click', () => this.prev());
    this.elements.nextBtn.addEventListener('click', () => this.next());
    this.elements.downloadBtn.addEventListener('click', () => this.download());
    
    document.addEventListener('keydown', (e) => {
      if (!this.isOpen) return;
      
      if (e.key === 'Escape') this.close();
      if (e.key === 'ArrowLeft') this.prev();
      if (e.key === 'ArrowRight') this.next();
    });
    
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) this.close();
    });
  }

  open(items, index = 0) {
    this.items = items;
    this.currentIndex = index;
    this.isOpen = true;
    
    this.updateContent();
    this.modal.classList.add('lightbox--active');
    document.body.style.overflow = 'hidden';
  }

  close() {
    this.modal.classList.remove('lightbox--active');
    this.isOpen = false;
    document.body.style.overflow = '';
    
    this.elements.video.pause();
    this.elements.video.currentTime = 0;
  }

  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updateContent();
    }
  }

  next() {
    if (this.currentIndex < this.items.length - 1) {
      this.currentIndex++;
      this.updateContent();
    }
  }

  updateContent() {
    const item = this.items[this.currentIndex];
    if (!item) return;
    
    if (item.type === 'video') {
      this.elements.image.style.display = 'none';
      this.elements.video.style.display = 'block';
      this.elements.video.querySelector('source').src = item.src;
      this.elements.video.load();
    } else {
      this.elements.video.style.display = 'none';
      this.elements.image.style.display = 'block';
      this.elements.image.src = item.src;
      this.elements.image.alt = item.title;
    }
    
    this.elements.title.textContent = item.title;
    this.elements.description.textContent = item.description;
    this.elements.counter.textContent = `${this.currentIndex + 1} of ${this.items.length}`;
    
    this.elements.prevBtn.disabled = this.currentIndex === 0;
    this.elements.nextBtn.disabled = this.currentIndex === this.items.length - 1;
  }

  download() {
    const item = this.items[this.currentIndex];
    if (!item) return;
    
    const link = document.createElement('a');
    link.href = item.src;
    link.download = item.title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.jpg';
    link.target = '_blank';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    const original = this.elements.downloadBtn.innerHTML;
    this.elements.downloadBtn.innerHTML = '<i class="fas fa-check"></i>';
    this.elements.downloadBtn.style.background = '#22c55e';
    
    setTimeout(() => {
      this.elements.downloadBtn.innerHTML = original;
      this.elements.downloadBtn.style.background = '';
    }, 1500);
  }
}

// Initialize gallery system
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.gallery-section')) {
    window.galleryController = new GalleryController();
  }
});
