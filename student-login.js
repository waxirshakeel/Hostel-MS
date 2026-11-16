
document.getElementById("studentLoginForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("loginMessage");

    message.textContent = "Please wait...";

    try {
        const response = await fetch("/api/student-login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || "Login failed.");
        }

        message.textContent = result.message;

        window.location.href = "/student-dashboard";

    } catch (error) {
        message.textContent = error.message;
    }
});
