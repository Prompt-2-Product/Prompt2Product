// IntersectionObserver logic to toggle the .visible class on .reveal elements
const revealElements = document.querySelectorAll('.reveal');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    } else {
      entry.target.classList.remove('visible');
    }
  });
}, {
  threshold: 0.2 // Adjust the visibility threshold as needed
});

revealElements.forEach(element => {
  observer.observe(element);
});