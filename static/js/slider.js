document.addEventListener('DOMContentLoaded', () => {
    let slideIndex = 0;
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;

    function showSlide(index) {
        if (index >= totalSlides) {
            slideIndex = 0;
        } else if (index < 0) {
            slideIndex = totalSlides - 1;
        } else {
            slideIndex = index;
        }
        const offset = -slideIndex * 100;
        document.querySelector('.slides').style.transform = `translateX(${offset}%)`;
    }

    // Declare changeSlide in the global scope
    window.changeSlide = function (direction) {
        showSlide(slideIndex + direction);
    };

    // Auto slide every 5 seconds
    setInterval(() => {
        window.changeSlide(1);
    }, 7000); // Change slide every 5 seconds

    // Initialize
    showSlide(slideIndex);
});
