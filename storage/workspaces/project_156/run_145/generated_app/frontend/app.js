// IntersectionObserver for scroll reveal effect
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    } else {
      entry.target.classList.remove('visible');
    }
  });
}, {
  threshold: 0.1
});

// Select all elements with the class 'reveal'
const revealElements = document.querySelectorAll('.reveal');

// Apply observer to each element
revealElements.forEach((element) => {
  observer.observe(element);
});