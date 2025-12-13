const API_BASE = "https://xi43tvk341.execute-api.us-east-1.amazonaws.com";

let authToken = localStorage.getItem("authToken") || null;

// ====== AUTH ======
async function login(username, password) {
    const response = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user: { name: username },
            secret: { password }
        })
    });

    if (!response.ok) throw new Error("Login failed");
    
    const token = await response.text();
    authToken = token.replace("Bearer ", "");
    localStorage.setItem("authToken", authToken);
    
    return authToken;
}

function logout() {
    authToken = null;
    localStorage.removeItem("authToken");
}

// ====== ARTIFACTS (CRUD) ======
async function createArtifact(type, url) {
    const response = await fetch(`${API_BASE}/artifact/${type}`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${authToken}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url })
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
    }
    return await response.json();
}

async function listArtifacts() {
    const response = await fetch(`${API_BASE}/artifacts`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (!response.ok) throw new Error("List failed");
    return await response.json();
}

async function deleteArtifact(type, id) {
    const response = await fetch(`${API_BASE}/artifact/${type}/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (!response.ok) throw new Error("Delete failed");
    return await response.json();
}

async function searchByName(name) {
    const response = await fetch(`${API_BASE}/artifact/byName/${name}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (!response.ok) throw new Error("Search failed");
    return await response.json();
}

async function searchByRegex(regex) {
    const response = await fetch(`${API_BASE}/artifact/byRegEx`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${authToken}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ regex })
    });

    if (!response.ok) throw new Error("Search failed");
    return await response.json();
}

async function ingestModel(url) {
    const response = await fetch(`${API_BASE}/artifact/model/ingest`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${authToken}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url })
    });

    if (!response.ok) throw new Error("Ingest failed");
    return await response.json();
}

async function resetRegistry() {
    const response = await fetch(`${API_BASE}/reset`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (!response.ok) throw new Error("Reset failed");
    return await response.json();
}