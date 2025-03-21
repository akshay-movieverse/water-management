document.addEventListener("DOMContentLoaded", function () {
    let sidebar = document.getElementById("sidebar");
    let toggleButton = document.getElementById("sidebarToggle");
    let mobileButton = document.getElementById("mobileSidebarToggle");

    // Sidebar Toggle (Desktop)
    toggleButton.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed");
    });

    // Sidebar Toggle (Mobile)
    mobileButton.addEventListener("click", function () {
        sidebar.classList.toggle("open");
    });

    // Close sidebar when clicking outside (Mobile)
    document.addEventListener("click", function (event) {
        if (!sidebar.contains(event.target) && !mobileButton.contains(event.target)) {
            sidebar.classList.remove("open");
        }
    });

    // Highlight Active Page
    let currentUrl = window.location.pathname;
    document.querySelectorAll(".sidebar .nav-link").forEach(link => {
        if (link.getAttribute("href") === currentUrl) {
            link.classList.add("active");
        }
    });
});



    // Select all delete buttons
    let deleteButtons = document.querySelectorAll(".btn-delete");

    deleteButtons.forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault(); // Stop default link behavior
            
            let confirmDelete = confirm("Are you sure you want to delete this?");
            if (confirmDelete) {
                window.location.href = this.href; // Proceed to the delete URL
            }
        });
    });
