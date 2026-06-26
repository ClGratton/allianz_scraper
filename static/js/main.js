document.addEventListener("DOMContentLoaded", () => {
    // Inject mobile spacing and prevent text selection
    (function() {
        const style = document.createElement("style");
        const dash = String.fromCharCode(45);
        style.textContent = `
            button, .floating${dash}btn, .category${dash}card, .op${dash}card, .submenu${dash}btn, .btn, .btn${dash}submit, a {
                user${dash}select: none !important;
                ${dash}webkit${dash}user${dash}select: none !important;
            }
            @media (max${dash}width: 768px) {
                .dashboard${dash}wrapper {
                    margin${dash}top: 3.5rem !important;
                    width: 100% !important;
                    max${dash}width: 100% !important;
                    overflow${dash}x: hidden !important;
                }
                .container {
                    margin${dash}top: 3.5rem !important;
                }
                .op${dash}content${dash}container {
                    width: 100% !important;
                    max${dash}width: 100% !important;
                    overflow${dash}x: auto !important;
                    display: block !important;
                }
            }
        `;
        document.head.appendChild(style);
    })();

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", handleLoginSubmit);
    }

    // Theme Toggle Logic
    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
        const icon = toggleBtn.querySelector(".theme-toggle-icon");
        
        // Enforce stored theme preference on load
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark") {
            document.body.classList.add("dark-theme");
        } else {
            document.body.classList.remove("dark-theme");
        }
        
        const updateIcon = () => {
            if (document.body.classList.contains("dark-theme")) {
                icon.textContent = "☀️";
            } else {
                icon.textContent = "🌙";
            }
        };
        
        updateIcon();
        
        toggleBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark-theme");
            if (document.body.classList.contains("dark-theme")) {
                localStorage.setItem("theme", "dark");
            } else {
                localStorage.setItem("theme", "light");
            }
            updateIcon();
        });
    }
});

const steps = [
    { text: "Inizializzazione della sessione sicura...", duration: 1500 },
    { text: "Connessione al portale Allianz in corso...", duration: 2000 },
    { text: "Verifica delle credenziali utente...", duration: 2500 },
    { text: "Accesso all'Area Personale Allianz...", duration: 2000 },
    { text: "Estrazione del ticket di sicurezza SCA...", duration: 2500 },
    { text: "Caricamento e sincronizzazione delle operazioni...", duration: 1500 }
];

let stepInterval;

function handleLoginSubmit(event) {
    event.preventDefault();

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const errorMsg = document.getElementById("error-msg");
    const submitBtn = document.getElementById("submit-btn");

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        showError("Compila tutti i campi richiesti.");
        return;
    }

    // Email format check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(username)) {
        showError("Inserisci un indirizzo email valido.");
        return;
    }

    // Password safety boundary check
    if (password.length < 4) {
        showError("La password deve essere di almeno 4 caratteri.");
        return;
    }

    // Clear error
    errorMsg.style.display = "none";
    
    // Disable inputs & submit button
    toggleInputs(true);

    // Show loading overlay and run visual multi-step loader
    showLoading(true);

    // Call API
    fetch("/api/login", {
        method: "POST",
        headers: {
            ["Content" + String.fromCharCode(45) + "Type"]: "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Smooth transition to dashboard
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 500);
        } else {
            showError(data.error || "Impossibile autenticarsi. Riprova.");
            showLoading(false);
            toggleInputs(false);
        }
    })
    .catch(error => {
        showError("Errore di connessione al server locale. Verifica che il backend sia attivo.");
        showLoading(false);
        toggleInputs(false);
    });
}

function showError(message) {
    const errorMsg = document.getElementById("error-msg");
    if (errorMsg) {
        errorMsg.textContent = message;
        errorMsg.style.display = "block";
    }
}

function toggleInputs(disable) {
    const inputs = document.querySelectorAll(".form-input, .btn-submit");
    inputs.forEach(input => {
        input.disabled = disable;
    });
}

function showLoading(show) {
    const overlay = document.getElementById("loading-overlay");
    const stepText = document.getElementById("loading-step");
    const subtext = document.getElementById("loading-subtext");

    if (show) {
        overlay.classList.add("active");
        let currentStep = 0;
        
        const updateText = () => {
            if (currentStep < steps.length) {
                stepText.style.opacity = "0";
                setTimeout(() => {
                    stepText.textContent = steps[currentStep].text;
                    subtext.textContent = `Fase ${currentStep + 1} di ${steps.length}`;
                    stepText.style.opacity = "1";
                    currentStep++;
                }, 300);
            }
        };

        updateText();
        stepInterval = setInterval(updateText, 1500);

    } else {
        overlay.classList.remove("active");
        clearInterval(stepInterval);
    }
}
