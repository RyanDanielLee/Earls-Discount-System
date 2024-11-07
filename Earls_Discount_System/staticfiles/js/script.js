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
