/**
 * ID-PAY Shared JavaScript Utilities
 * jQuery-based form validation, AJAX, UI effects
 */

$(document).ready(function() {
    // Global form validation
    $('.needs-validation').on('submit', function(e) {
        let valid = true;
        $(this).find('.form-control').each(function() {
            if ($(this).hasClass('is-invalid')) valid = false;
        });
        if (!valid) e.preventDefault();
    });

    // Password toggle
    $('.toggle-password').on('click', function() {
        const target = $(this).data('target');
        const $input = $(target);
        const type = $input.attr('type') === 'password' ? 'text' : 'password';
        $input.attr('type', type);
        $(this).html(type === 'password' ? '👁️' : '🙈');
    });

    // Auto-format phone numbers
    $('input[name="mobile"]').on('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '').slice(0,10);
    });

    // PIN input (4 digits only)
    $('input[name="pin"]').on('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '').slice(0,4);
    });

// Toast notifications
    window.showToast = function(msg, type = 'success') {
        if (!$('.toast-container').length) {
            $('body').append('<div class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
        }
        const toast = $(`
            <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${msg}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        $('.toast-container').append(toast);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
        toast.on('hidden.bs.toast', () => toast.remove());
    };


    // AJAX error handler
    $(document).ajaxError(function(event, xhr) {
        showToast('Connection error. Please try again.', 'error');
    });
});

// Form field validation helper
function validateField($field, regex, errorMsg) {
    const val = $field.val().trim();
    if (!val || !regex.test(val)) {
        $field.addClass('is-invalid');
        return false;
    }
    $field.removeClass('is-invalid').addClass('is-valid');
    return true;
}

// Email validation
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
