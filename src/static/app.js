// LyricLawyer App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Form submission with loading state
    const form = document.querySelector('form[action="/analyze"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
            submitBtn.disabled = true;
            
            // Reset after 30 seconds (timeout)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 30000);
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Auto-expand details on page load if there are flagged items
    const flaggedPhrases = document.querySelectorAll('.alert-danger, .alert-warning');
    if (flaggedPhrases.length > 0) {
        const details = document.querySelector('details');
        if (details) {
            details.open = true;
        }
    }
});

// Copy text to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard:', text);
    });
}

// Example usage analytics (would be implemented with proper analytics)
function trackEvent(eventName, properties) {
    console.log('Event:', eventName, properties);
    // In production, this would send to analytics service
}