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

//Switch tab for faceplate
function openTab(tabName) {
  const tabs = document.querySelectorAll('.tab');
  const sections = document.querySelectorAll('.form-section');

  tabs.forEach((tab) => tab.classList.remove('active'));
  sections.forEach((section) => section.classList.remove('active'));

  document.getElementById(tabName).classList.add('active');
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

//Modal for confirmation
function openConfirmationModal() {
  document.getElementById('confirmation-modal').style.display = 'block';
}

function closeConfirmationModal() {
  document.getElementById('confirmation-modal').style.display = 'none';
}

function submitRevokeForm() {
  const form = document.getElementById('revoke-form');
  if (form) {
    form.submit();
  } else {
    console.error('Revoke form not found');
  }
}

//Modal for reissue-confirmation
function openReissueConfirmModal(event) {
  event.preventDefault();
  document.getElementById('reissue-confirmation-modal').style.display = 'block';
}

function closeReissueConfirmModal() {
  document.getElementById('reissue-confirmation-modal').style.display = 'none';
}
