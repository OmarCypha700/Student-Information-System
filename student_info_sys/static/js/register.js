// Select queries for email validation
const emailField = document.getElementById("emailField");
const emailFeedBackArea = document.getElementsByClassName("email-feedback");
const emailSuccess = document.getElementsByClassName(".emailSuccess");

// Select queries for username validation
const usernameField = document.getElementById("usernameField");
const usernameFeedBackArea = document.getElementsByClassName(".username-feedback");
const usernameSuccess = document.getElementsByClassName(".usernameSuccess");

// Toggle password show and hide
const passwordField = document.getElementById("passwordField");
const password2Field = document.getElementById("password2Field");
const showPasswordBtn = document.querySelector(".showPassword");
const showPassword2Btn = document.querySelector(".showPassword2");
const submitBtn = document.querySelector(".submitBtn");


showPasswordBtn.addEventListener('click', function() {
  if (showPasswordBtn.textContent === "SHOW") {
    showPasswordBtn.textContent = "HIDE";
    passwordField.type = "text";
  } else {
    showPasswordBtn.textContent = "SHOW";
    passwordField.type = "password";
  }
});

showPassword2Btn.addEventListener("click", function() {
  if (showPassword2Btn.textContent === "SHOW") {
    showPassword2Btn.textContent = "HIDE";
    password2Field.type = "text";
  } else {
    showPassword2Btn.textContent = "SHOW";
    password2Field.type = "password";
  }
});


// Validate username
usernameField.addEventListener("keyup", (e) => {
  const usernameValue = e.target.value;

  usernameSuccess.style.display = "block";
  usernameSuccess.textContent = `Checking ${usernameValue}`;

  usernameField.classList.remove("is-invalid");
  usernameFeedBackArea.style.display = "none";

  //   Check if the username input has a value then make the API call
  if (usernameValue.length > 0) {
    fetch("/authentication/validate-username", {
      body: JSON.stringify({ username: usernameValue }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        usernameSuccess.style.display = "none";
        if (data.username_error) {
          submitBtn.disabled = true;
          // Set the username input element to invalid
          usernameField.classList.add("is-invalid");
          // display error message on the form
          usernameFeedBackArea.style.display = "block";
          usernameFeedBackArea.innerText = `${data.username_error}`;
        } else{
          submitBtn.disabled = false;
        }
      });
  }
});

// Validate email
emailField.addEventListener("keyup", (e) => {
  const emailValue = e.target.value;

  emailSuccess.style.display = "block";
  emailSuccess.textContent = `Checking ${emailValue}`;

  emailField.classList.remove("is-invalid");
  emailFeedBackArea.style.display = "none";

  // Check if email field has a value then make the API call
  if (emailValue.length > 0) {
    fetch("/authentication/validate-email", {
      body: JSON.stringify({ email: emailValue }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        emailSuccess.style.display = 'none';
        if (data.email_error) {
          submitBtn.disabled = true;
          // Set email input element to invalid
          emailField.classList.add("is-invalid");
          emailFeedBackArea.style.display = "block";
          emailFeedBackArea.innerText = `${data.email_error}`;
        } else{
          submitBtn.disabled = false;
        }
      });
  }
});