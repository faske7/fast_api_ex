// Клик по строке таблицы
document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll("table tbody tr");

    rows.forEach(row => {
        row.addEventListener("click", function () {
            const viewLink = this.querySelector("a");
            if (viewLink) {
                window.location.href = viewLink.href;
            }
        });
    });
});

// Сообщение в консоли
console.log("Custom JS loaded: Table interaction enabled.");
