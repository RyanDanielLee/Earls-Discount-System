// Copy email to clipboard
function copyEmail() {
  const email = document.getElementById('email').innerText;
  navigator.clipboard
    .writeText(email)
    .then(() => {
      alert('Email copied to clipboard!');
    })
    .catch((err) => {
      console.error('Failed to copy: ', err);
    });
}

// NavBar for mobile view
function myMenu() {
  var navLinks = document.getElementById('nav-items');
  var dropdown1 = document.getElementById('dropdown-content1');
  var dropdown2 = document.getElementById('dropdown-content2');

  navLinks.classList.toggle('active');
  dropdown1.classList.toggle('active');
  dropdown2.classList.toggle('active');
}
