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
            .opcontent input[type="radio"], 
            .opcontent input[type="checkbox"],
            .op${dash}content${dash}container input[type="radio"], 
            .op${dash}content${dash}container input[type="checkbox"] {
                vertical${dash}align: middle !important;
                margin: 0 0.4rem 0 0 !important;
                cursor: pointer;
                transform: translateY(1px) !important;
                ${dash}webkit${dash}transform: translateY(1px) !important;
            }
            .opcontent table, 
            .op${dash}content${dash}container table {
                width: 100% !important;
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
                .opcontent, 
                .opcontent form,
                .op${dash}content${dash}container, 
                .op${dash}content${dash}container form {
                    width: 100% !important;
                    max${dash}width: 100% !important;
                    overflow${dash}x: auto !important;
                    display: block !important;
                }
                .opcontent table, 
                .op${dash}content${dash}container table {
                    display: table !important;
                    width: 100% !important;
                    table${dash}layout: fixed !important;
                    word${dash}wrap: break${dash}word !important;
                    word${dash}break: normal !important;
                }
                .opcontent th, 
                .opcontent td,
                .op${dash}content${dash}container th,
                .op${dash}content${dash}container td,
                .opcontent td input,
                .opcontent td select,
                .op${dash}content${dash}container td input,
                .op${dash}content${dash}container td select {
                    white${dash}space: normal !important;
                    word${dash}wrap: break${dash}word !important;
                    word${dash}break: normal !important;
                    padding: 0.5rem 0.25rem !important;
                    font${dash}size: 0.6rem !important;
                }
                .searchBody, 
                .searchBody > tbody > tr, 
                .searchBody > tbody > tr > td, 
                .searchBody > tr, 
                .searchBody > tr > td {
                    display: block !important;
                    width: 100% !important;
                }
                .searchBody > tbody > tr > td,
                .searchBody > tr > td {
                    margin${dash}bottom: 1rem !important;
                    padding: 0 !important;
                }
                body.operation${dash}page .category${dash}card {
                    min${dash}height: 80px !important;
                    height: 80px !important;
                    padding: 0.5rem 1rem !important;
                    gap: 1rem !important;
                }
                body.operation${dash}page .category${dash}card p {
                    display: none !important;
                }
                body.operation${dash}page .category${dash}icon${dash}wrapper {
                    width: 44px !important;
                    height: 44px !important;
                    font${dash}size: 1.5rem !important;
                }
                body.operation${dash}page .category${dash}card h3 {
                    font${dash}size: 1.1rem !important;
                    margin: 0 !important;
                }
            }
        `;
        document.head.appendChild(style);

        // Dynamically add wrapper styles
        const opcontent = document.querySelector(".opcontent");
        if (opcontent) {
            opcontent.classList.add("op" + dash + "content" + dash + "container");
            if (opcontent.getAttribute("card") === "True") {
                opcontent.classList.add("detail" + dash + "card");
            }
        }

        // Unwrap nested html, body, and outer td tags inside opcontent
        const sanitizeOpcontent = () => {
            const opcontent = document.querySelector(".opcontent");
            if (!opcontent) return;
            
            const nestedBodys = Array.from(opcontent.querySelectorAll('body'));
            nestedBodys.forEach(body => {
                const parent = body.parentNode;
                if (parent) {
                    const frag = document.createDocumentFragment();
                    while (body.firstChild) {
                        frag.appendChild(body.firstChild);
                    }
                    parent.replaceChild(frag, body);
                }
            });
            
            const nestedHtmls = Array.from(opcontent.querySelectorAll('html'));
            nestedHtmls.forEach(html => {
                const parent = html.parentNode;
                if (parent) {
                    const frag = document.createDocumentFragment();
                    while (html.firstChild) {
                        frag.appendChild(html.firstChild);
                    }
                    parent.replaceChild(frag, html);
                }
            });
            
            const children = Array.from(opcontent.children);
            children.forEach(child => {
                if (child.tagName.toLowerCase() === 'td') {
                    const frag = document.createDocumentFragment();
                    while (child.firstChild) {
                        frag.appendChild(child.firstChild);
                    }
                    opcontent.replaceChild(frag, child);
                }
            });
        };

        // Align radio buttons and checkboxes with adjacent text node
        const alignInputs = () => {
            document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
                const parent = input.parentElement;
                if (!parent) return;
                if (parent.tagName.toLowerCase() === "span" && parent.style.whiteSpace === "nowrap") return;
                
                const next = input.nextSibling;
                if (next && next.nodeType === 3) {
                    const text = next.textContent.trim();
                    if (text) {
                        const span = document.createElement("span");
                        span.textContent = " " + text;
                        span.style.verticalAlign = "middle";
                        span.style.display = "inline-block";
                        
                        const wrapper = document.createElement("span");
                        wrapper.style.display = "inline-block";
                        wrapper.style.whiteSpace = "nowrap";
                        wrapper.style.verticalAlign = "middle";
                        
                        input.style.verticalAlign = "middle";
                        input.style.margin = "0 0.4rem 0 0";
                        input.style.display = "inline-block";
                        
                        parent.insertBefore(wrapper, input);
                        wrapper.appendChild(input);
                        wrapper.appendChild(span);
                        parent.removeChild(next);
                    }
                }
            });
        };

        const rearrangeLayout = () => {
            const ths = Array.from(document.querySelectorAll('th.sectionTitle'));
            const prevTh = ths.find(th => th.textContent.trim() === 'Dati Previdenziali');
            if (prevTh) {
                const rightTd = prevTh.closest('td');
                if (rightTd) {
                    const tr = rightTd.parentElement;
                    if (tr && tr.cells.length >= 3) {
                        const layoutTable = tr.closest('table');
                        if (layoutTable) {
                            layoutTable.style.setProperty("display", "block", "important");
                            
                            // Style only direct child rows of this layout table to prevent nested table rows pollution
                            Array.from(layoutTable.rows).forEach(row => {
                                if (row !== tr) {
                                    row.style.setProperty("display", "block", "important");
                                    Array.from(row.cells).forEach(cell => {
                                        cell.style.setProperty("display", "block", "important");
                                        cell.style.setProperty("width", "100%", "important");
                                    });
                                }
                            });
                        }
                        
                        tr.style.setProperty("display", "flex", "important");
                        tr.style.setProperty("flex" + dash + "direction", "column" + dash + "reverse", "important");
                        
                        // Force all child tables inside the layout columns to span 100%
                        tr.querySelectorAll('table').forEach(tbl => {
                            tbl.style.setProperty("width", "100%", "important");
                        });
                        
                        const cells = Array.from(tr.cells);
                        cells[0].style.setProperty("display", "block", "important");
                        cells[0].style.setProperty("width", "100%", "important");
                        cells[1].style.setProperty("display", "none", "important");
                        cells[2].style.setProperty("display", "block", "important");
                        cells[2].style.setProperty("width", "100%", "important");
                        cells[2].style.setProperty("margin" + dash + "bottom", "1.5rem", "important");
                    }
                }
            }
        };

        const handleDomUpdates = () => {
            sanitizeOpcontent();
            alignInputs();
            rearrangeLayout();
        };

        handleDomUpdates();
        
        // Listen to DOM mutations for dynamic AJAX pages load
        const observer = new MutationObserver(handleDomUpdates);
        observer.observe(document.body, { childList: true, subtree: true });
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
