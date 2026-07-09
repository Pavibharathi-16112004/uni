const API_BASE = "http://127.0.0.1:8000";

const messageBox = document.getElementById("message");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");

function showMessage(text, type) {
  messageBox.textContent = text;
  messageBox.className = "message " + type;
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        showMessage(data.detail || "Login failed", "error");
        return;
      }

      showMessage("Login successful. Welcome " + data.name, "success");

      // Redirect to the dashboard after a short pause so the user sees the message
      setTimeout(() => {
        const url = `dashboard.html?name=${encodeURIComponent(data.name)}&email=${encodeURIComponent(data.email)}`;
        window.location.href = url;
      }, 600);
    } catch (err) {
      showMessage("Could not reach server. Is FastAPI running?", "error");
    }
  });
}

if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      const res = await fetch(`${API_BASE}/api/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        showMessage(data.detail || "Signup failed", "error");
        return;
      }

      showMessage("Signup successful. You can now sign in.", "success");
    } catch (err) {
      showMessage("Could not reach server. Is FastAPI running?", "error");
    }
  });
}
