// Basic front-end behaviour shared by every page.
// Kept intentionally simple - no frameworks, no build step.

document.addEventListener("DOMContentLoaded", function () {
    // Prevent double-submission of any form on the page: once the user
    // clicks "Save", disable the button so a slow connection or an
    // accidental double-click doesn't insert the same row twice.
    var forms = document.querySelectorAll("form.form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function () {
            var submitButton = form.querySelector("button[type='submit']");
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Saving...";
            }
        });
    });
});

// Used on the grading results page: shows/hides the hidden row that
// holds one student's full answer text, without adding an extra
// column to the results table.
function toggleAnswer(rowId) {
    var row = document.getElementById(rowId);
    if (!row) {
        return;
    }
    row.style.display = row.style.display === "none" ? "table-row" : "none";
}
