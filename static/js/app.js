/**
 * Handle form submissions and interactions
 */

// Auto-hide alerts after 5 seconds (except persistent ones)
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Don't auto-hide the no active canisters info box
        if (alert.id === 'noActiveCanisters') {
            return;
        }
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
});

