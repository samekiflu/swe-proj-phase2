// Check if already logged in
window.addEventListener("load", () => {
    if (authToken) {
        showDashboard();
        loadArtifacts();
    } else {
        showLogin();
    }
});

function showLogin() {
    document.getElementById("loginPage").classList.add("active");
    document.getElementById("dashboardPage").classList.remove("active");
}

function showDashboard() {
    document.getElementById("loginPage").classList.remove("active");
    document.getElementById("dashboardPage").classList.add("active");
}

// ====== LOGIN ======
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("loginError");
    const loginBtn = document.getElementById("loginBtn");
    
    errorDiv.classList.remove("show");
    loginBtn.disabled = true;
    loginBtn.textContent = "Logging in...";

    try {
        await login(username, password);
        showDashboard();
        loadArtifacts();
        document.getElementById("loginForm").reset();
        document.getElementById("username").value = "ece461";
        document.getElementById("password").value = "password";
    } catch (error) {
        errorDiv.textContent = "❌ " + error.message;
        errorDiv.classList.add("show");
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "Login";
    }
}

// ====== LOGOUT ======
function handleLogout() {
    if (confirm("Are you sure you want to logout?")) {
        logout();
        showLogin();
        document.getElementById("loginForm").reset();
        document.getElementById("username").value = "ece461";
        document.getElementById("password").value = "password";
    }
}

// ====== CREATE ARTIFACT ======
async function handleCreateArtifact(event) {
    event.preventDefault();
    
    const type = document.getElementById("artifactType").value;
    const url = document.getElementById("artifactUrl").value;
    const errorDiv = document.getElementById("createError");
    const createBtn = document.getElementById("createBtn");
    
    errorDiv.classList.remove("show");
    createBtn.disabled = true;
    createBtn.textContent = "Creating...";

    try {
        const result = await createArtifact(type, url);
        alert(`✅ Created ${result.metadata.name} (ID: ${result.metadata.id})`);
        document.getElementById("artifactUrl").value = "";
        loadArtifacts();
    } catch (error) {
        errorDiv.textContent = "❌ " + error.message;
        errorDiv.classList.add("show");
    } finally {
        createBtn.disabled = false;
        createBtn.textContent = "Create";
    }
}

// ====== LOAD ARTIFACTS ======
async function loadArtifacts() {
    try {
        const artifacts = await listArtifacts();
        const container = document.getElementById("artifactsList");
        document.getElementById("artifactCount").textContent = artifacts.length;

        if (artifacts.length === 0) {
            container.innerHTML = `<p class="empty-message">No artifacts yet. Create one to get started!</p>`;
            return;
        }

        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>ID</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const artifact of artifacts) {
            html += `
                <tr>
                    <td>${artifact.name}</td>
                    <td>${artifact.type}</td>
                    <td>${artifact.id}</td>
                    <td>
                        <button class="delete-btn" onclick="handleDeleteArtifact('${artifact.type}', '${artifact.id}')">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        }

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    } catch (error) {
        alert("Error loading artifacts: " + error.message);
    }
}

// ====== DELETE ARTIFACT ======
async function handleDeleteArtifact(type, id) {
    if (!confirm(`Delete ${type} #${id}?`)) return;

    try {
        await deleteArtifact(type, id);
        alert("✅ Deleted");
        loadArtifacts();
    } catch (error) {
        alert("❌ " + error.message);
    }
}

// ====== SEARCH BY NAME ======
async function handleSearch() {
    const name = document.getElementById("searchInput").value;
    if (!name) return alert("Enter a name to search");

    try {
        const results = await searchByName(name);
        displaySearchResults(results);
    } catch (error) {
        alert("❌ " + error.message);
    }
}

// ====== SEARCH BY REGEX ======
async function handleRegexSearch() {
    const regex = document.getElementById("searchInput").value;
    if (!regex) return alert("Enter a regex pattern to search");

    try {
        const results = await searchByRegex(regex);
        displaySearchResults(results);
    } catch (error) {
        alert("❌ " + error.message);
    }
}

function displaySearchResults(results) {
    const container = document.getElementById("searchResults");

    if (!results || results.length === 0) {
        container.innerHTML = `<p class="empty-message">No results found</p>`;
        return;
    }

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>ID</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const result of results) {
        html += `
            <tr>
                <td>${result.name}</td>
                <td>${result.type}</td>
                <td>${result.id}</td>
            </tr>
        `;
    }

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

// ====== INGEST MODEL ======
async function handleIngestModel(event) {
    event.preventDefault();
    
    const url = document.getElementById("ingestUrl").value;
    const errorDiv = document.getElementById("ingestError");
    const resultDiv = document.getElementById("ingestResult");
    const ingestBtn = document.getElementById("ingestBtn");
    
    errorDiv.classList.remove("show");
    resultDiv.classList.remove("show");
    ingestBtn.disabled = true;
    ingestBtn.textContent = "Ingesting...";

    try {
        const result = await ingestModel(url);
        
        document.getElementById("ingestUrl").value = "";

        if (result.accepted) {
            resultDiv.className = "ingest-result success show";
            resultDiv.innerHTML = `
                <strong>✅ Model Accepted!</strong>
                <p><strong>ID:</strong> ${result.metadata.id}</p>
                <p><strong>Name:</strong> ${result.metadata.name}</p>
            `;
        } else {
            resultDiv.className = "ingest-result error show";
            resultDiv.innerHTML = `
                <strong>❌ Model Rejected</strong>
                <p><strong>Reason:</strong> ${result.reason}</p>
            `;
        }

        loadArtifacts();
    } catch (error) {
        errorDiv.textContent = "❌ " + error.message;
        errorDiv.classList.add("show");
    } finally {
        ingestBtn.disabled = false;
        ingestBtn.textContent = "Ingest";
    }
}

// ====== RESET REGISTRY ======
async function handleReset() {
    if (!confirm("🚨 WARNING: This will DELETE ALL artifacts! Are you sure?")) {
        return;
    }

    try {
        await resetRegistry();
        alert("✅ Registry reset successfully");
        loadArtifacts();
    } catch (error) {
        alert("❌ " + error.message);
    }
}