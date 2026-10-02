// =====================================================
// Urban Smart City
// Global JavaScript
// =====================================================

console.log("Urban Smart City JavaScript loaded successfully.");


// =====================================================
// REPORT FORM INTERACTIONS
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const reportForm = document.getElementById("reportForm");

    // Run only on pages containing the report form
    if (!reportForm) {
        return;
    }

    // -------------------------------------------------
    // ELEMENTS
    // -------------------------------------------------

    const description =
        document.getElementById("description");

    const problemType =
        document.getElementById("problemType");

    const urgency =
        document.getElementById("urgency");

    const problemImage =
        document.getElementById("problemImage");

    const latitude =
        document.getElementById("latitude");

    const longitude =
        document.getElementById("longitude");

    const submitButton =
        reportForm.querySelector(".submit-report-button");


    // =================================================
    // 1. DESCRIPTION CHARACTER COUNTER
    // =================================================

    if (description) {

        const counter =
            document.createElement("div");

        counter.className =
            "character-counter";

        description.parentElement.appendChild(counter);


        function updateCharacterCount() {

            const length =
                description.value.length;

          counter.textContent =
    `${length} characters`;

            if (length > 450) {

                counter.classList.add(
                    "near-limit"
                );

            } else {

                counter.classList.remove(
                    "near-limit"
                );

            }
        }


        description.addEventListener(
            "input",
            updateCharacterCount
        );

        updateCharacterCount();

    }


    // =================================================
    // 2. SMART URGENCY AUTO-SELECTION
    // =================================================

    /*
        These are the problem types for which
        the system automatically suggests urgency.

        "Other" is intentionally NOT included.
        For "Other", the citizen must select urgency.
    */

    const urgencyMap = {

        "pothole": "high",

        "garbage": "medium",

        "water-leakage": "high",

        "drainage": "high",

        "waterlogging": "critical",

        "streetlight": "medium",

        "road-damage": "high",

        "traffic": "high",

        "infrastructure": "high"

    };


    // -------------------------------------------------
    // Apply urgency visual styling
    // -------------------------------------------------

    function updateUrgencyStyle() {

        if (!urgency) {
            return;
        }

        const value =
            urgency.value.toLowerCase();

        urgency.classList.remove(
            "urgency-low",
            "urgency-medium",
            "urgency-high",
            "urgency-critical"
        );


        if (value === "low") {

            urgency.classList.add(
                "urgency-low"
            );

        }

        else if (value === "medium") {

            urgency.classList.add(
                "urgency-medium"
            );

        }

        else if (value === "high") {

            urgency.classList.add(
                "urgency-high"
            );

        }

        else if (value === "critical") {

            urgency.classList.add(
                "urgency-critical"
            );

        }

    }


    // -------------------------------------------------
    // Automatically select urgency
    // -------------------------------------------------

    if (problemType && urgency) {

        problemType.addEventListener(
            "change",
            function () {

                const selectedProblem =
                    problemType.value;


                /*
                    Check whether this problem type
                    exists in our automatic urgency map.
                */

                if (
                    urgencyMap[selectedProblem]
                ) {

                    urgency.value =
                        urgencyMap[selectedProblem];

                    updateUrgencyStyle();


                    // Small visual feedback
                    urgency.classList.add(
                        "smart-updated"
                    );


                    setTimeout(
                        function () {

                            urgency.classList.remove(
                                "smart-updated"
                            );

                        },
                        700
                    );

                }

                /*
                    If the selected problem type
                    is "Other", do NOT select anything.

                    The user chooses the urgency manually.
                */

            }
        );

    }


    // -------------------------------------------------
    // User can manually change urgency
    // -------------------------------------------------

    if (urgency) {

        urgency.addEventListener(
            "change",
            updateUrgencyStyle
        );

    }


    // =================================================
    // 3. AI CLASSIFICATION PREVIEW
    // =================================================

    const aiPreviewData = {

        "pothole": {
            problem: "Pothole / Road Surface Damage",
            severity: "High",
            department: "Roads & Public Works",
            priority: "High"
        },

        "garbage": {
            problem: "Garbage / Waste Accumulation",
            severity: "Medium",
            department: "Sanitation & Waste Management",
            priority: "Medium"
        },

        "water-leakage": {
            problem: "Water Leakage",
            severity: "High",
            department: "Water Supply",
            priority: "High"
        },

        "drainage": {
            problem: "Drainage Problem",
            severity: "High",
            department: "Drainage & Sewerage",
            priority: "High"
        },

        "waterlogging": {
            problem: "Waterlogging",
            severity: "Critical",
            department: "Drainage & Water Management",
            priority: "Urgent"
        },

        "streetlight": {
            problem: "Streetlight Problem",
            severity: "Medium",
            department: "Street Lighting",
            priority: "Medium"
        },

        "road-damage": {
            problem: "Road Damage",
            severity: "High",
            department: "Roads & Public Works",
            priority: "High"
        },

        "traffic": {
            problem: "Traffic / Traffic Management",
            severity: "High",
            department: "Traffic Management",
            priority: "High"
        },

        "infrastructure": {
            problem: "Infrastructure Problem",
            severity: "High",
            department: "Urban Infrastructure",
            priority: "High"
        },

        "other": {
            problem: "Other Civic Problem",
            severity: "Pending Analysis",
            department: "To Be Determined",
            priority: "Pending"
        }

    };


    // Find AI preview container
    const aiPreview =
        document.querySelector(".ai-preview");


    if (problemType && aiPreview) {

        problemType.addEventListener(
            "change",
            function () {

                const selectedType =
                    problemType.value;

                const data =
                    aiPreviewData[selectedType];


                // No problem selected
                if (!data) {

                    aiPreview.innerHTML = `

                        <div class="ai-preview-empty">

                            <span class="ai-preview-symbol">
                                ✦
                            </span>

                            <div>

                                <strong>
                                    AI Classification Preview
                                </strong>

                                <p>
                                    Select a problem type to see
                                    the initial classification.
                                </p>

                            </div>

                        </div>

                    `;

                    return;
                }


                // Display classification
                aiPreview.innerHTML = `

                    <div class="ai-preview-header">

                        <div>

                            <span class="ai-label">
                                AI-ASSISTED CLASSIFICATION
                            </span>

                            <h3>
                                ${data.problem}
                            </h3>

                        </div>

                        <span class="ai-status">
                            Preview
                        </span>

                    </div>


                    <div class="ai-preview-grid">

                        <div class="ai-result-item">

                            <span>
                                Severity
                            </span>

                            <strong
                                class="severity-${data.severity
                                    .toLowerCase()
                                    .replaceAll(" ", "-")}"
                            >
                                ${data.severity}
                            </strong>

                        </div>


                        <div class="ai-result-item">

                            <span>
                                Responsible Department
                            </span>

                            <strong>
                                ${data.department}
                            </strong>

                        </div>


                        <div class="ai-result-item">

                            <span>
                                Priority
                            </span>

                            <strong>
                                ${data.priority}
                            </strong>

                        </div>

                    </div>


                    <div class="ai-preview-note">

                        <span>✦</span>

                        <p>
                            This is an initial classification preview.
                            Final analysis will use the problem description,
                            location and historical civic data.
                        </p>

                    </div>

                `;


                // Small entrance animation
                aiPreview.classList.remove(
                    "ai-preview-updated"
                );

                void aiPreview.offsetWidth;

                aiPreview.classList.add(
                    "ai-preview-updated"
                );

            }
        );

    }


    // =================================================
    // 4. IMAGE PREVIEW
    // =================================================

    if (problemImage) {

        problemImage.addEventListener(
            "change",
            function () {

                const file =
                    problemImage.files[0];


                if (!file) {
                    return;
                }


                // Maximum 5 MB
                const maxSize =
                    5 * 1024 * 1024;


                if (file.size > maxSize) {

                    alert(
                        "Image size must be less than 5 MB."
                    );

                    problemImage.value = "";

                    return;
                }


                // Remove old preview
                const oldPreview =
                    document.querySelector(
                        ".dynamic-image-preview"
                    );


                if (oldPreview) {
                    oldPreview.remove();
                }


                const reader =
                    new FileReader();


                reader.onload =
                    function (event) {

                        const preview =
                            document.createElement("div");


                        preview.className =
                            "dynamic-image-preview";


                        preview.innerHTML = `

                            <div class="preview-header">

                                <strong>
                                    Image Preview
                                </strong>

                                <button
                                    type="button"
                                    class="remove-image-button"
                                >
                                    Remove
                                </button>

                            </div>


                            <img
                                src="${event.target.result}"
                                alt="Problem preview"
                            >


                            <span>
                                ${file.name}
                            </span>

                        `;


                        problemImage.parentElement
                            .appendChild(preview);


                        // Remove selected image
                        const removeButton =
                            preview.querySelector(
                                ".remove-image-button"
                            );


                        removeButton.addEventListener(
                            "click",
                            function () {

                                problemImage.value =
                                    "";

                                preview.remove();

                            }
                        );

                    };


                reader.readAsDataURL(file);

            }
        );

    }


    // =================================================
    // 5. LOCATION VALIDATION
    // =================================================

    function locationSelected() {

        return (

            latitude &&
            longitude &&
            latitude.value &&
            longitude.value

        );

    }


    // =================================================
    // 6. FORM SUBMISSION
    // =================================================

    reportForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();


            // Browser validation
            if (!reportForm.checkValidity()) {

                reportForm.reportValidity();

                return;

            }


            // Location validation
            if (!locationSelected()) {

                alert(
                    "Please select the problem location on the map before submitting."
                );

                return;

            }


            // Loading state
            if (submitButton) {

                submitButton.disabled =
                    true;

                submitButton.innerHTML = `

                    <span class="button-loader"></span>

                    Processing Report...

                `;

            }


            // Temporary simulation
            // This will later become:
            // POST /api/complaints

            setTimeout(
                function () {

                    showReportSuccess();

                },
                1400
            );

        }
    );


    // =================================================
    // 7. SUCCESS MESSAGE
    // =================================================

    function showReportSuccess() {

        if (submitButton) {

            submitButton.disabled =
                false;

            submitButton.innerHTML =
                "Submit Civic Report →";

        }


        const existingMessage =
            document.querySelector(
                ".report-success-message"
            );


        if (existingMessage) {
            existingMessage.remove();
        }


        const message =
            document.createElement("div");


        message.className =
            "report-success-message";


        message.innerHTML = `

            <div class="success-icon">
                ✓
            </div>

            <div>

                <strong>
                    Civic report submitted successfully
                </strong>

                <span>
                    Your report has been recorded and is ready
                    for AI analysis.
                </span>

            </div>

        `;


        reportForm.parentElement.insertBefore(
            message,
            reportForm
        );


        message.scrollIntoView({

            behavior: "smooth",

            block: "center"

        });

    }

});


// =====================================================
// REGISTRATION PAGE
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const registerForm =
        document.getElementById("registerForm");

    // Run only on registration page
    if (!registerForm) {
        return;
    }

    const accountType =
        document.getElementById("accountType");

    const officerVerification =
        document.getElementById("officerVerification");

    const registerButton =
        document.getElementById("registerButton");

    const officialEmail =
        document.getElementById("officialEmail");

    const officerId =
        document.getElementById("officerId");

    const verificationReason =
        document.getElementById("verificationReason");

    const password =
        document.getElementById("registerPassword");

    const confirmPassword =
        document.getElementById("confirmPassword");

    const passwordToggle =
        document.getElementById("passwordToggle");

    const strengthBar =
        document.getElementById("strengthBar");

    const strengthText =
        document.getElementById("strengthText");

    const message =
        document.getElementById("registerMessage");


    // =================================================
    // 1. ACCOUNT TYPE
    // =================================================

    function updateAccountType() {

        if (
            accountType.value ===
            "municipality_officer"
        ) {

            officerVerification.classList.add("show");

            officialEmail.required = true;

            officerId.required = true;

            verificationReason.required = true;

            registerButton.innerHTML =
                'Submit Verification Request <span>→</span>';

        }

        else {

            officerVerification.classList.remove("show");

            officialEmail.required = false;

            officerId.required = false;

            verificationReason.required = false;

            registerButton.innerHTML =
                'Create Account <span>→</span>';
        }
    }


    accountType.addEventListener(
        "change",
        updateAccountType
    );

    updateAccountType();


    // =================================================
    // 2. PASSWORD VISIBILITY
    // =================================================

    passwordToggle.addEventListener(
        "click",
        function () {

            if (
                password.type ===
                "password"
            ) {

                password.type = "text";

                passwordToggle.textContent =
                    "Hide";

                passwordToggle.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            }

            else {

                password.type = "password";

                passwordToggle.textContent =
                    "Show";

                passwordToggle.setAttribute(
                    "aria-label",
                    "Show password"
                );
            }

        }
    );


    // =================================================
    // 3. PASSWORD STRENGTH
    // =================================================

    password.addEventListener(
        "input",
        function () {

            const value =
                password.value;

            let strength = 0;


            if (value.length >= 8) {
                strength++;
            }


            if (/[A-Z]/.test(value)) {
                strength++;
            }


            if (/[0-9]/.test(value)) {
                strength++;
            }


            if (/[^A-Za-z0-9]/.test(value)) {
                strength++;
            }


            strengthBar.className =
                "strength-bar";


            if (value.length === 0) {

                strengthText.textContent =
                    "Password strength";

                return;
            }


            if (strength <= 1) {

                strengthBar.classList.add(
                    "strength-weak"
                );

                strengthText.textContent =
                    "Weak password";

            }

            else if (strength <= 3) {

                strengthBar.classList.add(
                    "strength-medium"
                );

                strengthText.textContent =
                    "Moderate password";

            }

            else {

                strengthBar.classList.add(
                    "strength-strong"
                );

                strengthText.textContent =
                    "Strong password";
            }

        }
    );


    // =================================================
    // 4. VALIDATION
    // =================================================

    function clearErrors() {

        document.querySelectorAll(
            ".field-error"
        ).forEach(function (element) {

            element.textContent = "";

        });


        document.querySelectorAll(
            ".input-error"
        ).forEach(function (element) {

            element.classList.remove(
                "input-error"
            );

        });


        document.querySelectorAll(
            ".terms-error"
        ).forEach(function (element) {

            element.classList.remove(
                "terms-error"
            );

        });
    }


    function showError(
        input,
        errorId,
        text
    ) {

        input.classList.add(
            "input-error"
        );


        const errorElement =
            document.getElementById(
                errorId
            );


        if (errorElement) {

            errorElement.textContent =
                text;
        }
    }


    // =================================================
    // 5. FORM SUBMISSION
    // =================================================

    registerForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            clearErrors();

            message.className =
                "register-message";

            message.textContent =
                "";


            const name =
                document.getElementById(
                    "registerName"
                );

            const email =
                document.getElementById(
                    "registerEmail"
                );

            const terms =
                document.getElementById(
                    "terms"
                );


            let valid = true;


            // -------------------------------------------------
            // Name
            // -------------------------------------------------

            if (
                name.value.trim().length < 2
            ) {

                showError(
                    name,
                    "nameError",
                    "Please enter your full name."
                );

                valid = false;
            }


            // -------------------------------------------------
            // Email
            // -------------------------------------------------

            if (
                !email.value.trim() ||
                !email.validity.valid
            ) {

                showError(
                    email,
                    "emailError",
                    "Please enter a valid email address."
                );

                valid = false;
            }


            // -------------------------------------------------
            // Account type
            // -------------------------------------------------

            if (
                accountType.value === ""
            ) {

                accountType.classList.add(
                    "input-error"
                );

                valid = false;
            }


            // -------------------------------------------------
            // Officer verification
            // -------------------------------------------------

            if (
                accountType.value ===
                "municipality_officer"
            ) {

                if (
                    officialEmail.value.trim() === ""
                ) {

                    showError(
                        officialEmail,
                        "officialEmailError",
                        "Please enter your official municipal email."
                    );

                    valid = false;
                }


                if (
                    officerId.value.trim() === ""
                ) {

                    showError(
                        officerId,
                        "officerIdError",
                        "Please enter your officer or employee ID."
                    );

                    valid = false;
                }


                if (
                    verificationReason.value.trim().length < 10
                ) {

                    showError(
                        verificationReason,
                        "verificationReasonError",
                        "Please provide a short reason for municipal access."
                    );

                    valid = false;
                }
            }


            // -------------------------------------------------
            // Password
            // -------------------------------------------------

            if (
                password.value.length < 8
            ) {

                showError(
                    password,
                    "passwordError",
                    "Password must contain at least 8 characters."
                );

                valid = false;
            }


            // -------------------------------------------------
            // Confirm password
            // -------------------------------------------------

            if (
                password.value !==
                confirmPassword.value
            ) {

                showError(
                    confirmPassword,
                    "confirmPasswordError",
                    "Passwords do not match."
                );

                valid = false;
            }


            // -------------------------------------------------
            // Terms
            // -------------------------------------------------

            if (!terms.checked) {

                terms.parentElement.classList.add(
                    "terms-error"
                );

                valid = false;
            }


            // -------------------------------------------------
            // Stop if invalid
            // -------------------------------------------------

            if (!valid) {

                message.textContent =
                    "Please review the highlighted fields.";

                message.classList.add(
                    "message-error"
                );

                return;
            }


            // =================================================
            // REAL REGISTRATION SUBMISSION
            // =================================================

            registerButton.disabled = true;

            registerButton.innerHTML = `
                <span class="button-loader"></span>
                Creating account...
            `;


            const payload = {

                name:
                    name.value.trim(),

                email:
                    email.value.trim(),

                password:
                    password.value,

                account_type:
                    accountType.value,

                official_email:
                    officialEmail
                        ? officialEmail.value.trim()
                        : "",

                officer_id:
                    officerId
                        ? officerId.value.trim()
                        : "",

                verification_reason:
                    verificationReason
                        ? verificationReason.value.trim()
                        : ""
            };


            try {

                const response =
                    await fetch(
                        "/api/register",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(payload)
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.message ||
                        "Registration failed."
                    );
                }


                // =================================================
                // REGISTRATION SUCCESS
                // =================================================

                message.className =
                    "register-message message-success";

                message.textContent =
                    data.message;


                registerForm.reset();

                updateAccountType();

            }


            catch (error) {

                // =================================================
                // REGISTRATION ERROR
                // =================================================

                message.className =
                    "register-message message-error";

                message.textContent =
                    error.message ||
                    "Unable to create your account.";

            }


            finally {

                registerButton.disabled =
                    false;

                updateAccountType();
            }

        }
    );


    // =================================================
    // 6. REMOVE ERROR STATE WHILE TYPING
    // =================================================

    registerForm
        .querySelectorAll(
            "input, select, textarea"
        )
        .forEach(function (input) {

            input.addEventListener(
                "input",
                function () {

                    input.classList.remove(
                        "input-error"
                    );

                }
            );


            input.addEventListener(
                "change",
                function () {

                    input.classList.remove(
                        "input-error"
                    );

                }
            );

        });

});
// =====================================================
// LOGIN PAGE
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const loginForm = document.getElementById("loginForm");

    // Run only on the login page
    if (!loginForm) {
        return;
    }

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const passwordToggle = document.getElementById("passwordToggle");
    const loginButton = document.getElementById("loginButton");
    const loginLoading = document.getElementById("loginLoading");
    const loginMessage = document.getElementById("loginMessage");
    const forgotPassword = document.getElementById("forgotPassword");


    // =================================================
    // 1. PASSWORD VISIBILITY
    // =================================================

    if (passwordToggle && passwordInput) {

        passwordToggle.addEventListener("click", function () {

            if (passwordInput.type === "password") {

                passwordInput.type = "text";
                passwordToggle.textContent = "Hide";
                passwordToggle.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            } else {

                passwordInput.type = "password";
                passwordToggle.textContent = "Show";
                passwordToggle.setAttribute(
                    "aria-label",
                    "Show password"
                );

            }

        });

    }


    // =================================================
    // 2. LOGIN MESSAGE
    // =================================================

    function showLoginMessage(text, success) {

        if (!loginMessage) {
            return;
        }

        loginMessage.className = "login-message";
        loginMessage.textContent = text;
        loginMessage.style.display = "block";

        if (success) {
            loginMessage.classList.add("message-success");
        } else {
            loginMessage.classList.add("message-error");
        }

    }


    // =================================================
    // 3. CLEAR LOGIN MESSAGE
    // =================================================

    function clearLoginMessage() {

        if (!loginMessage) {
            return;
        }

        loginMessage.className = "login-message";
        loginMessage.textContent = "";
        loginMessage.style.display = "none";

    }


    // =================================================
    // 4. FORGOT PASSWORD
    // =================================================

    if (forgotPassword) {

        forgotPassword.addEventListener("click", function (event) {

            event.preventDefault();

            showLoginMessage(
                "Password recovery will be available soon.",
                false
            );

        });

    }


    // =================================================
    // 5. LOGIN FORM SUBMISSION
    // =================================================

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        clearLoginMessage();


        // ---------------------------------------------
        // Check form elements
        // ---------------------------------------------

        if (!emailInput || !passwordInput) {

            showLoginMessage(
                "Login form is not configured correctly.",
                false
            );

            return;
        }


        // ---------------------------------------------
        // Get values
        // ---------------------------------------------

        const email = emailInput.value.trim();
        const password = passwordInput.value;


        // ---------------------------------------------
        // Validate email
        // ---------------------------------------------

        if (!email) {

            showLoginMessage(
                "Please enter your email address.",
                false
            );

            emailInput.focus();

            return;
        }


        if (!emailInput.validity.valid) {

            showLoginMessage(
                "Please enter a valid email address.",
                false
            );

            emailInput.focus();

            return;
        }


        // ---------------------------------------------
        // Validate password
        // ---------------------------------------------

        if (!password) {

            showLoginMessage(
                "Please enter your password.",
                false
            );

            passwordInput.focus();

            return;
        }


        // ---------------------------------------------
        // Loading state
        // ---------------------------------------------

        if (loginButton) {

            loginButton.disabled = true;
            loginButton.classList.add("loading");

        }

        if (loginLoading) {

            loginLoading.style.display = "inline";
            loginLoading.textContent = "Signing in...";

        }


        // =================================================
        // SEND LOGIN REQUEST TO FLASK
        // =================================================

        try {

            console.log("Sending login request...");


            const response = await fetch("/api/login", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })

            });


            console.log(
                "Login response status:",
                response.status
            );


            // ---------------------------------------------
            // Read response
            // ---------------------------------------------

            const data = await response.json();


            console.log("Login response:", data);


            // ---------------------------------------------
            // Login failed
            // ---------------------------------------------

            if (!response.ok || !data.success) {

                showLoginMessage(
                    data.message ||
                    "Login failed. Please check your email and password.",
                    false
                );

                if (loginButton) {
                    loginButton.disabled = false;
                    loginButton.classList.remove("loading");
                }

                if (loginLoading) {
                    loginLoading.style.display = "none";
                }

                return;
            }


            // ---------------------------------------------
            // Login successful
            // ---------------------------------------------

            showLoginMessage(
                data.message ||
                "Login successful. Redirecting...",
                true
            );


            console.log("Login successful.");
            console.log("Role:", data.role);
            console.log("Redirect:", data.redirect_url);


            // ---------------------------------------------
            // Redirect
            // ---------------------------------------------

            if (data.redirect_url) {

                setTimeout(function () {

                    window.location.href =
                        data.redirect_url;

                }, 500);

            } else {

                // Fallback based on role

                if (data.role === "citizen") {

                    window.location.href =
                        "/citizen-dashboard";

                } else if (
                    data.role === "municipality_officer"
                ) {

                    window.location.href =
                        "/municipal-dashboard";

                } else if (
                    data.role === "admin"
                ) {

                    window.location.href =
                        "/admin-dashboard";

                } else {

                    showLoginMessage(
                        "Login successful, but dashboard could not be determined.",
                        false
                    );

                    if (loginButton) {
                        loginButton.disabled = false;
                        loginButton.classList.remove("loading");
                    }

                    if (loginLoading) {
                        loginLoading.style.display = "none";
                    }

                }

            }


        } catch (error) {

            // ---------------------------------------------
            // Login error
            // ---------------------------------------------

            console.error("Login error:", error);


            showLoginMessage(
                "Unable to connect to the server. Please make sure Flask is running.",
                false
            );


            if (loginButton) {

                loginButton.disabled = false;
                loginButton.classList.remove("loading");

            }


            if (loginLoading) {

                loginLoading.style.display = "none";

            }

        }

    });


    // =================================================
    // 6. CLEAR MESSAGE WHEN TYPING
    // =================================================

    if (emailInput) {

        emailInput.addEventListener("input", function () {

            clearLoginMessage();

        });

    }


    if (passwordInput) {

        passwordInput.addEventListener("input", function () {

            clearLoginMessage();

        });

    }

});