// BULLETPROOF Gallery Filtering - SENIOR ARCHITECT SOLUTION
console.log('🚀 GALLERY.JS LOADING');

// Initialize gallery filters
function initGalleryFilters() {
    console.log('🔧 INITIALIZING GALLERY FILTERING');
    
    const filterButtons = document.querySelectorAll('button[data-filter], .filter-btn, .cassia-filter-btn');
    const galleryItems = document.querySelectorAll('div[data-category], .photo-item, .video-item, .cassia-gallery-item');
    
    console.log('📊 FOUND:', filterButtons.length, 'buttons,', galleryItems.length, 'items');
    
    if (filterButtons.length === 0 || galleryItems.length === 0) {
        console.error('❌ NO ELEMENTS FOUND - RETRYING IN 1 SECOND');
        setTimeout(initGalleryFilters, 1000);
        return;
    }
    
    filterButtons.forEach((button, index) => {
        console.log(`🔘 Button ${index}: "${button.textContent.trim()}" = ${button.getAttribute('data-filter')}`);
        
        button.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const filterValue = this.getAttribute('data-filter');
            console.log('🎯 CLICKED:', filterValue);
            
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            let visibleCount = 0;
            galleryItems.forEach(item => {
                const itemCategory = item.getAttribute('data-category');
                const shouldShow = filterValue === 'all' || itemCategory === filterValue;
                
                if (shouldShow) {
                    item.style.display = 'block';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            console.log('✅ SHOWING:', visibleCount, 'items for filter:', filterValue);
        };
    });
    
    console.log('🚀 FILTERING INITIALIZED SUCCESSFULLY');
}

// Execute immediately and on DOM ready
initGalleryFilters();
document.addEventListener('DOMContentLoaded', initGalleryFilters);
setTimeout(initGalleryFilters, 500);
setTimeout(initGalleryFilters, 1000);

// Handle tab switching
const tabButtons = document.querySelectorAll('.tab-btn');
const gallerySections = document.querySelectorAll('.gallery-section');

tabButtons.forEach(button => {
    button.addEventListener('click', function() {
        const targetTab = this.dataset.tab;
        
        tabButtons.forEach(btn => btn.classList.remove('active'));
        gallerySections.forEach(section => section.classList.remove('active'));
        
        this.classList.add('active');
        document.getElementById(targetTab).classList.add('active');
    });
});

// Initialize gallery filters
function initGalleryFilters() {
    console.log('🔧 INITIALIZING GALLERY FILTERING');
    
    // Get elements with multiple selectors
    const filterButtons = document.querySelectorAll('button[data-filter], .filter-btn, .cassia-filter-btn');
    const galleryItems = document.querySelectorAll('div[data-category], .photo-item, .video-item, .cassia-gallery-item');
    
    console.log('📊 FOUND:', filterButtons.length, 'buttons,', galleryItems.length, 'items');
    
    if (filterButtons.length === 0 || galleryItems.length === 0) {
        console.error('❌ NO ELEMENTS FOUND - RETRYING IN 1 SECOND');
        setTimeout(initGalleryFilters, 1000);
        return;
    }
    
    // Add click handlers
    filterButtons.forEach((button, index) => {
        console.log(`🔘 Button ${index}: "${button.textContent.trim()}" = ${button.getAttribute('data-filter')}`);
        
        button.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const filterValue = this.getAttribute('data-filter');
            console.log('🎯 CLICKED:', filterValue);
            
            // Update active states
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter items
            let visibleCount = 0;
            galleryItems.forEach(item => {
                const itemCategory = item.getAttribute('data-category');
                const shouldShow = filterValue === 'all' || itemCategory === filterValue;
                
                if (shouldShow) {
                    item.style.display = 'block';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            console.log('✅ SHOWING:', visibleCount, 'items for filter:', filterValue);
        };
    });
    
    console.log('🚀 FILTERING INITIALIZED SUCCESSFULLY');
}

// Initialize photo gallery with click and hover events
function initPhotoGallery() {
    const photoItems = document.querySelectorAll('.cassia-gallery-item');
    
    photoItems.forEach(item => {
        const img = item.querySelector('.cassia-image');
        const viewBtn = item.querySelector('.cassia-view-btn');
        const downloadBtn = item.querySelector('.cassia-download-btn');
        const playBtn = item.querySelector('.cassia-play-btn');
        
        // Click on image to open lightbox
        if (img) {
            img.addEventListener('click', function(e) {
                e.stopPropagation();
                openLightbox(img.src, img.alt);
            });
        }
        
        // View button click
        if (viewBtn) {
            viewBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                if (img) openLightbox(img.src, img.alt);
            });
        }
        
        // Download button click
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                if (img) downloadImage(img.src);
            });
        }
        
        // Play button for videos
        if (playBtn) {
            playBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const videoUrl = this.dataset.videoUrl;
                if (videoUrl) {
                    openVideoModal(videoUrl);
                }
            });
        }
    });
}

// Initialize lightbox functionality
function initLightbox() {
    // Lightbox will be created dynamically when needed
}

// Open lightbox with image
function openLightbox(imageSrc, imageAlt) {
    // Create or update lightbox content
    let lightbox = document.getElementById('photoLightbox');
    
    if (!lightbox) {
        lightbox = document.createElement('div');
        lightbox.id = 'photoLightbox';
        lightbox.className = 'lightbox-modal';
        lightbox.innerHTML = `
            <div class="lightbox-content">
                <button class="lightbox-close" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>
                <div class="lightbox-image-container">
                    <img id="lightboxImage" src="" alt="" />
                    <div class="lightbox-navigation">
                        <button class="nav-btn prev-btn" title="Previous">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                        <button class="nav-btn next-btn" title="Next">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
                <div class="lightbox-info">
                    <h3 id="lightboxTitle">${imageAlt || 'Image'}</h3>
                    <div class="lightbox-actions">
                        <button id="lightboxDownload" class="btn btn-primary">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(lightbox);
        
        // Add event listeners
        setupLightboxEvents(lightbox);
    }
    
    // Update lightbox content
    const lightboxImg = lightbox.querySelector('#lightboxImage');
    const lightboxTitle = lightbox.querySelector('#lightboxTitle');
    const downloadBtn = lightbox.querySelector('#lightboxDownload');
    
    lightboxImg.src = imageSrc;
    lightboxImg.alt = imageAlt;
    lightboxTitle.textContent = imageAlt || 'Image';
    
    // Update download button
    downloadBtn.onclick = () => downloadImage(imageSrc, imageAlt);
    
    // Show lightbox
    lightbox.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Update navigation for current photo
    updateLightboxNavigation(lightbox, imageSrc);
}

// Setup lightbox event listeners
function setupLightboxEvents(lightbox) {
    const closeBtn = lightbox.querySelector('.lightbox-close');
    const prevBtn = lightbox.querySelector('.prev-btn');
    const nextBtn = lightbox.querySelector('.next-btn');
    
    // Close lightbox
    closeBtn.addEventListener('click', closeLightbox);
    
    // Close when clicking outside the content
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'Escape') {
                closeLightbox();
            } else if (e.key === 'ArrowLeft') {
                navigateLightbox('prev');
            } else if (e.key === 'ArrowRight') {
                navigateLightbox('next');
            }
        }
    });
    
    // Navigation buttons
    if (prevBtn) prevBtn.addEventListener('click', () => navigateLightbox('prev'));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateLightbox('next'));
}

// Close lightbox
function closeLightbox() {
    const lightbox = document.getElementById('photoLightbox');
    if (lightbox) {
        lightbox.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Navigate between photos in lightbox
function navigateLightbox(direction) {
    const lightbox = document.getElementById('photoLightbox');
    if (!lightbox) return;
    
    const currentImg = lightbox.querySelector('#lightboxImage');
    if (!currentImg) return;
    
    const currentSrc = currentImg.src;
    const photoItems = Array.from(document.querySelectorAll('.photo-item'));
    const currentIndex = photoItems.findIndex(item => {
        const img = item.querySelector('img');
        return img && img.src === currentSrc;
    });
    
    if (currentIndex === -1) return;
    
    let targetIndex;
    if (direction === 'prev') {
        targetIndex = (currentIndex - 1 + photoItems.length) % photoItems.length;
    } else {
        targetIndex = (currentIndex + 1) % photoItems.length;
    }
    
    const targetItem = photoItems[targetIndex];
    const targetImg = targetItem.querySelector('img');
    
    if (targetImg) {
        openLightbox(targetImg.src, targetImg.alt);
    }
}

// Update lightbox navigation state
function updateLightboxNavigation(lightbox, currentSrc) {
    const photoItems = Array.from(document.querySelectorAll('.photo-item'));
    const currentIndex = photoItems.findIndex(item => {
        const img = item.querySelector('img');
        return img && img.src === currentSrc;
    });
    
    // Enable/disable navigation buttons
    const prevBtn = lightbox.querySelector('.prev-btn');
    const nextBtn = lightbox.querySelector('.next-btn');
    
    if (prevBtn) {
        prevBtn.disabled = currentIndex <= 0;
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentIndex >= photoItems.length - 1;
    }
}

// Download image with multiple fallback methods
async function downloadImage(imageSrc, filename = 'download') {
    // Show loading state
    showNotification('Preparing download...', 'info');
    
    // Create a filename
    const extension = imageSrc.split('.').pop().split('?')[0].toLowerCase();
    const cleanFilename = (filename || 'image')
        .replace(/[^a-z0-9]/gi, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
    const downloadFilename = `${cleanFilename || 'image'}.${['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension) ? extension : 'jpg'}`;
    
    // Method 1: Try direct download first (works for same-origin and some CORS cases)
    try {
        const directLink = document.createElement('a');
        directLink.href = imageSrc;
        directLink.download = downloadFilename;
        directLink.style.display = 'none';
        document.body.appendChild(directLink);
        directLink.click();
        document.body.removeChild(directLink);
        showNotification('Download started!', 'success');
        return;
    } catch (e) {
        console.log('Direct download failed, trying next method...');
    }
    
    // Method 2: Try fetch + blob (works for many CORS cases)
    try {
        const response = await fetch(imageSrc, {
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin',
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            
            const blobLink = document.createElement('a');
            blobLink.href = blobUrl;
            blobLink.download = downloadFilename;
            blobLink.style.display = 'none';
            document.body.appendChild(blobLink);
            blobLink.click();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(blobLink);
                window.URL.revokeObjectURL(blobUrl);
            }, 100);
            
            showNotification('Download started!', 'success');
            return;
        }
    } catch (e) {
        console.log('Blob download failed, trying next method...', e);
    }
    
    // Method 3: Try server-side download proxy
    try {
        // Use the correct URL pattern that matches your Django URL configuration
        const proxyUrl = `/gallery/download/?url=${encodeURIComponent(imageSrc)}&filename=${encodeURIComponent(downloadFilename)}`;
        
        // Create a hidden iframe to handle the download
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        
        // Set a timeout to clean up the iframe
        setTimeout(() => {
            if (iframe.parentNode) {
                document.body.removeChild(iframe);
            }
        }, 60000); // Remove after 60 seconds
        
        // Set the iframe source to trigger the download
        iframe.src = proxyUrl;
        
        showNotification('Starting download...', 'info');
        return;
    } catch (e) {
        console.log('Server proxy failed, trying next method...', e);
    }
    
    // Method 4: Open in new tab as last resort
    try {
        const win = window.open(imageSrc, '_blank');
        if (win) {
            showNotification('Image opened in new tab. Right-click and select "Save Image As..." to download.', 'info');
        } else {
            throw new Error('Popup blocked');
        }
    } catch (e) {
        // Final fallback - show direct link
        const finalMessage = document.createElement('div');
        finalMessage.innerHTML = `
            <p>Could not start download automatically.</p>
            <p>Please right-click the link below and select "Save link as..." to download:</p>
            <a href="${imageSrc}" style="color: white; text-decoration: underline;">
                ${downloadFilename}
            </a>
        `;
        showNotification(finalMessage, 'error');
    }
}

// Check if URL is from the same origin
function isSameOrigin(url) {
    try {
        const origin = window.location.origin;
        const urlObj = new URL(url, window.location.href);
        return urlObj.origin === origin;
    } catch (e) {
        return false;
    }
}

// Show notification with better visibility
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Add icon based on type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Force reflow to enable transition
    void notification.offsetWidth;
    
    // Auto remove after 5 seconds (longer for important messages)
    setTimeout(() => {
        notification.classList.add('show');
        
        const removeAfter = type === 'error' ? 5000 : 3000;
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, removeAfter);
    }, 50);
}

// Add notification styles
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        left: 20px;
        max-width: 400px;
        margin: 0 auto;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        background: #2c3e50;
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 15px;
        line-height: 1.4;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .notification i {
        font-size: 18px;
        flex-shrink: 0;
    }
    
    .notification span {
        flex: 1;
    }
    
    .notification.show {
        transform: translateY(0);
        opacity: 1;
    }
    
    .notification.success {
        background: rgba(39, 174, 96, 0.95);
        border-left: 4px solid #2ecc71;
    }
    
    .notification.error {
        background: rgba(231, 76, 60, 0.95);
        border-left: 4px solid #e74c3c;
    }
    
    .notification.info {
        background: rgba(52, 152, 219, 0.95);
        border-left: 4px solid #3498db;
    }
    
    @media (min-width: 768px) {
        .notification {
            left: auto;
            margin: 0;
        }
    }
`;

document.head.appendChild(style);

// Video Modal Function
function openVideoModal(videoUrl) {
    // Create video modal if it doesn't exist
    let videoModal = document.getElementById('videoModal');
    
    if (!videoModal) {
        videoModal = document.createElement('div');
        videoModal.id = 'videoModal';
        videoModal.className = 'video-modal';
        videoModal.innerHTML = `
            <div class="video-modal-content">
                <button class="video-modal-close" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>
                <div class="video-container">
                    <video id="modalVideo" controls autoplay>
                        <source src="" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
            </div>
        `;
        document.body.appendChild(videoModal);
        
        // Add event listeners
        const closeBtn = videoModal.querySelector('.video-modal-close');
        closeBtn.addEventListener('click', closeVideoModal);
        
        videoModal.addEventListener('click', function(e) {
            if (e.target === videoModal) {
                closeVideoModal();
            }
        });
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && videoModal.style.display === 'flex') {
                closeVideoModal();
            }
        });
    }
    
    // Update video source and show modal
    const video = videoModal.querySelector('#modalVideo');
    video.src = videoUrl;
    videoModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeVideoModal() {
    const videoModal = document.getElementById('videoModal');
    if (videoModal) {
        const video = videoModal.querySelector('#modalVideo');
        video.pause();
        video.src = '';
        videoModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Add video modal styles
const videoModalStyle = document.createElement('style');
videoModalStyle.textContent = `
    .video-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    
    .video-modal-content {
        position: relative;
        max-width: 90vw;
        max-height: 90vh;
        background: #000;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .video-modal-close {
        position: absolute;
        top: 15px;
        right: 15px;
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .video-modal-close:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(1.1);
    }
    
    .video-container {
        width: 100%;
        height: 100%;
    }
    
    .video-container video {
        width: 100%;
        height: auto;
        max-height: 90vh;
        display: block;
    }
`;

document.head.appendChild(videoModalStyle);
