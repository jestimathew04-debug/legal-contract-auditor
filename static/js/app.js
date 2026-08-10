// LEXAUDIT SPA Application Logic (Redesigned)

// Handle API Base dynamically
const API_BASE = window.location.protocol.startsWith('http') 
    ? window.location.origin 
    : 'http://127.0.0.1:5000';

// App State
let contractText = "";
let clauses = [];
let activeFilter = "all";
let activeIndex = null;
let drawerOpen = false;

// DOM Elements
const docViewer = document.getElementById("doc-viewer");
const docTitle = document.getElementById("doc-title");
const docSize = document.getElementById("doc-size");
const clauseList = document.getElementById("clause-list");
const uploadZone = document.getElementById("upload-zone");
const fileInput = document.getElementById("file-input");
const loader = document.getElementById("loader");

// Buttons & Collapsible Bar
const btnClear = document.getElementById("btn-clear");
const btnReanalyze = document.getElementById("btn-reanalyze");
const btnSample = document.getElementById("btn-sample");
const btnExportJson = document.getElementById("btn-export-json");
const btnExportPdf = document.getElementById("btn-export-pdf");
const auditToggleBar = document.getElementById("audit-toggle-bar");
const auditDrawer = document.getElementById("audit-drawer");
const auditToggleIcon = document.getElementById("audit-toggle-icon");
const auditLogBadge = document.getElementById("audit-log-badge");

// Top Grid Metric DOM Elements
const metricClass = document.getElementById("metric-class");
const metricScore = document.getElementById("metric-score");
const metricScoreLabel = document.getElementById("metric-score-label");
const metricHigh = document.getElementById("metric-high");
const metricClauses = document.getElementById("metric-clauses");

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    checkBackendHealth();
    setupEventListeners();
});

// Check API Connection Status
async function checkBackendHealth() {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        if (response.ok) {
            dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)] animate-pulse";
            text.textContent = `ONLINE: ${data.engine.active_engine.toUpperCase()}`;
        } else {
            throw new Error("API returned error status");
        }
    } catch (error) {
        dot.className = "w-2.5 h-2.5 rounded-full bg-red-650 shadow-[0_0_10px_rgba(220,38,38,0.6)] animate-pulse";
        text.textContent = "OFFLINE (RUN APP.PY)";
        showError("Backend server is offline. Run app.py to connect.");
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Collapsible Bottom Drawer Toggle
    auditToggleBar.addEventListener("click", toggleDrawer);

    // Drag & Drop Handlers
    uploadZone.addEventListener("click", () => fileInput.click());
    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("border-red-500", "bg-red-950/10");
    });
    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("border-red-500", "bg-red-950/10");
    });
    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("border-red-500", "bg-red-950/10");
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Clear Document Action
    btnClear.addEventListener("click", resetApp);

    // Re-Analyze Document Action
    btnReanalyze.addEventListener("click", reanalyzeCurrentText);

    // Load Sample Button
    btnSample.addEventListener("click", loadSampleContract);

    // Export Buttons
    btnExportJson.addEventListener("click", exportJSON);
    btnExportPdf.addEventListener("click", () => window.print());

    // Filter Navigation Click Handlers (Pill Buttons)
    document.querySelectorAll(".filter-tab").forEach(tab => {
        tab.addEventListener("click", (e) => {
            // Remove active style classes from all tabs
            document.querySelectorAll(".filter-tab").forEach(t => {
                t.className = "filter-tab py-1.5 px-4 rounded-lg text-xs font-semibold text-zinc-550 hover:text-white transition-all flex items-center gap-1.5";
            });
            
            // Set active design to selected tab
            const target = e.currentTarget;
            activeFilter = target.getAttribute("data-filter");
            
            if (activeFilter === "all") {
                target.className = "filter-tab py-1.5 px-4 rounded-lg text-xs font-semibold transition-all bg-zinc-900 text-white shadow-sm";
            } else if (activeFilter === "HIGH") {
                target.className = "filter-tab py-1.5 px-4 rounded-lg text-xs font-semibold transition-all bg-red-950/50 text-red-400 border border-red-900/60 shadow-sm flex items-center gap-1.5";
            } else if (activeFilter === "MEDIUM") {
                target.className = "filter-tab py-1.5 px-4 rounded-lg text-xs font-semibold transition-all bg-amber-950/50 text-amber-400 border border-amber-900/60 shadow-sm flex items-center gap-1.5";
            } else if (activeFilter === "LOW") {
                target.className = "filter-tab py-1.5 px-4 rounded-lg text-xs font-semibold transition-all bg-emerald-950/50 text-emerald-400 border border-emerald-900/60 shadow-sm flex items-center gap-1.5";
            }
            
            renderClauseList();
        });
    });
}

// Collapsible Drawer Controller
function toggleDrawer(forceState = null) {
    if (forceState !== null) {
        drawerOpen = forceState;
    } else {
        drawerOpen = !drawerOpen;
    }

    if (drawerOpen) {
        auditDrawer.classList.add("open");
        auditToggleIcon.classList.add("rotate-180");
    } else {
        auditDrawer.classList.remove("open");
        auditToggleIcon.classList.remove("rotate-180");
    }
}

// Helper: Format file sizes
function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Show/Hide Loader Spinner
function showLoader(visible, text = "Auditing contract...") {
    if (visible) {
        document.querySelector("#loader p.text-xs").textContent = text;
        loader.classList.remove("opacity-0", "pointer-events-none");
    } else {
        loader.classList.add("opacity-0", "pointer-events-none");
    }
}

// Reset app dashboard state
function resetApp() {
    contractText = "";
    clauses = [];
    activeFilter = "all";
    activeIndex = null;
    
    docTitle.textContent = "No contract loaded";
    docSize.textContent = "";
    docViewer.innerHTML = `
        <div class="h-[650px] flex flex-col items-center justify-center text-zinc-600 gap-3">
            <i class="fa-solid fa-file-contract text-4xl opacity-15"></i>
            <p class="text-sm text-zinc-550">Audited contract text will render here with color-coded risk markers.</p>
        </div>
    `;
    
    // Clear top metrics
    metricClass.textContent = "No File Loaded";
    metricScore.textContent = "0";
    metricScoreLabel.innerHTML = `<span class="w-2 h-2 rounded-full bg-zinc-650"></span> N/A Rating`;
    metricScoreLabel.className = "text-[10px] font-semibold text-zinc-400 mt-4 flex items-center gap-1.5";
    metricHigh.textContent = "0";
    metricClauses.textContent = "0";

    // Toggle drawer closed
    toggleDrawer(false);
    auditLogBadge.classList.add("hidden");
    
    btnClear.classList.add("hidden");
    btnReanalyze.classList.add("hidden");
    uploadZone.classList.remove("hidden");
    fileInput.value = "";
}

// Load Sample Contract
async function loadSampleContract() {
    showLoader(true, "Fetching and auditing sample contract...");
    try {
        const response = await fetch(`${API_BASE}/api/sample`);
        const data = await response.json();
        
        if (data.success) {
            docTitle.textContent = "sample_contract.txt";
            docSize.textContent = `(${formatBytes(data.raw_text.length)})`;
            contractText = data.raw_text;
            clauses = data.clauses;
            
            renderDashboard(data);
            btnClear.classList.remove("hidden");
            btnReanalyze.classList.remove("hidden");
            uploadZone.classList.add("hidden");
            
            // Expand drawer automatically for user visual confirmation
            setTimeout(() => toggleDrawer(true), 300);
        } else {
            showError(data.error || "Failed to load sample contract");
        }
    } catch (e) {
        showError("Unable to load sample contract. Check server connectivity.");
    } finally {
        showLoader(false);
    }
}

// Upload and Analyze Document
async function handleFileUpload(file) {
    showLoader(true, `Uploading and analyzing ${file.name}...`);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            docTitle.textContent = file.name;
            docSize.textContent = `(${formatBytes(file.size)})`;
            contractText = data.raw_text;
            clauses = data.clauses;
            
            renderDashboard(data);
            btnClear.classList.remove("hidden");
            btnReanalyze.classList.remove("hidden");
            uploadZone.classList.add("hidden");
            
            // Expand drawer automatically
            setTimeout(() => toggleDrawer(true), 300);
        } else {
            showError(data.error || "Could not analyze the file");
        }
    } catch (e) {
        showError("An error occurred during file upload. Check connection to app.py.");
    } finally {
        showLoader(false);
    }
}

// Re-run Analysis on Current Text (Re-Analyze Action)
async function reanalyzeCurrentText() {
    if (!contractText) return;
    
    showLoader(true, "Re-analyzing contract text...");
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: contractText })
        });
        const data = await response.json();
        
        if (data.success) {
            clauses = data.clauses;
            renderDashboard(data);
            
            // Expand drawer
            toggleDrawer(true);
        } else {
            showError(data.error || "Re-analysis failed");
        }
    } catch (e) {
        showError("Server error during re-analysis.");
    } finally {
        showLoader(false);
    }
}

// Renders the Full Metrics and Layouts
function renderDashboard(data) {
    const metrics = data.metrics;
    
    // 1. Populate Metrics row
    metricClass.textContent = metrics.document_type || "General Contract";
    metricScore.textContent = metrics.compliance_score;
    metricHigh.textContent = metrics.high_risk_flags;
    metricClauses.textContent = metrics.total_clauses;
    
    // Audit log badge count
    if (metrics.total_clauses > 0) {
        auditLogBadge.textContent = `${metrics.total_clauses} Clauses`;
        auditLogBadge.classList.remove("hidden");
    } else {
        auditLogBadge.classList.add("hidden");
    }
    
    // Set score compliance rating label styling
    if (metrics.compliance_score >= 80) {
        metricScoreLabel.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> High Compliance`;
        metricScoreLabel.className = "text-[10px] font-semibold text-emerald-400 mt-4 flex items-center gap-1.5";
    } else if (metrics.compliance_score >= 50) {
        metricScoreLabel.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-500"></span> Moderate Risk`;
        metricScoreLabel.className = "text-[10px] font-semibold text-amber-400 mt-4 flex items-center gap-1.5";
    } else {
        metricScoreLabel.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span> High Risk Danger`;
        metricScoreLabel.className = "text-[10px] font-semibold text-red-550 mt-4 flex items-center gap-1.5";
    }
    
    // 2. Render Document text with highlighted spans
    renderDocumentText();
    
    // 3. Render Bottom Drawer Clause Cards Grid
    renderClauseList();
}

// Escape HTML for XSS Prevention
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Construct and render HTML highlighting in the Contract Viewer
function renderDocumentText() {
    if (!contractText) return;
    
    // Sort clauses by start index to enable sequential slicing
    const sortedClauses = [...clauses].sort((a, b) => a.start - b.start);
    
    let htmlOutput = "";
    let lastIndex = 0;
    
    sortedClauses.forEach((clause) => {
        const originalIdx = clauses.indexOf(clause);
        
        // Append text prior to this clause
        htmlOutput += escapeHtml(contractText.slice(lastIndex, clause.start));
        
        // Append highlighted clause wrap
        const riskClass = clause.risk_level.toLowerCase();
        htmlOutput += `<span class="clause-highlight hl-${riskClass}" data-index="${originalIdx}" id="hl-span-${originalIdx}">${escapeHtml(clause.text)}</span>`;
        
        lastIndex = clause.end;
    });
    
    // Append remaining document text
    htmlOutput += escapeHtml(contractText.slice(lastIndex));
    
    docViewer.innerHTML = htmlOutput;
    
    // Attach click listeners to text highlights
    document.querySelectorAll(".clause-highlight").forEach(el => {
        el.addEventListener("click", (e) => {
            const index = parseInt(e.currentTarget.getAttribute("data-index"));
            selectClause(index, true); // Select and scroll sidebar/drawer
        });
    });
}

// Renders the list of clause cards inside the collapsible bottom drawer
function renderClauseList() {
    clauseList.innerHTML = "";
    
    const filtered = clauses.filter(c => {
        if (activeFilter === "all") return true;
        return c.risk_level === activeFilter;
    });
    
    if (filtered.length === 0) {
        clauseList.innerHTML = `
            <div class="py-12 text-center text-zinc-650 text-sm">
                <i class="fa-solid fa-clipboard-question text-3xl opacity-10 mb-3"></i>
                <p>No clauses matched the selected risk severity filter.</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach((clause) => {
        const originalIdx = clauses.indexOf(clause);
        const card = document.createElement("div");
        
        // Style variables based on risk level
        let borderClass = "border-zinc-850 hover:border-zinc-800 bg-[#0E0E10]";
        let badgeClass = "bg-zinc-900 text-zinc-400 border-zinc-800";
        let iconClass = "fa-info-circle";
        
        if (clause.risk_level === "HIGH") {
            borderClass = "border-red-950/60 hover:border-red-800/40 bg-[#160B0B]/40";
            badgeClass = "bg-red-950/50 text-red-400 border-red-900/50 shadow-[0_0_8px_rgba(239,68,68,0.12)]";
            iconClass = "fa-triangle-exclamation text-red-500";
        } else if (clause.risk_level === "MEDIUM") {
            borderClass = "border-amber-950/60 hover:border-amber-800/40 bg-[#16120B]/40";
            badgeClass = "bg-amber-950/50 text-amber-400 border-amber-900/50";
            iconClass = "fa-circle-exclamation text-amber-500";
        } else if (clause.risk_level === "LOW") {
            borderClass = "border-emerald-950/60 hover:border-emerald-800/40 bg-[#0B1610]/40";
            badgeClass = "bg-emerald-950/50 text-emerald-400 border-emerald-900/50";
            iconClass = "fa-circle-check text-emerald-500";
        }
        
        card.id = `audit-card-${originalIdx}`;
        card.className = `border ${borderClass} rounded-xl p-5 cursor-pointer transition-all duration-300 ${originalIdx === activeIndex ? 'ring-2 ring-red-500 shadow-xl shadow-red-950/20' : ''}`;
        
        // Issues sub-render
        let issuesHtml = "";
        if (clause.issues && clause.issues.length > 0) {
            issuesHtml = `
                <div class="mt-4 pt-4 border-t border-zinc-900/60 space-y-4 font-sans">
                    ${clause.issues.map(issue => `
                        <div class="text-[12px] leading-relaxed">
                            <div class="flex items-center gap-1.5 text-zinc-300 font-bold">
                                <span class="w-1.5 h-1.5 rounded-full ${issue.severity === 'HIGH' ? 'bg-red-500' : issue.severity === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'}"></span>
                                Risk Audit Flag:
                            </div>
                            <p class="text-zinc-400 mt-1 pl-3 border-l border-zinc-800">${issue.explanation}</p>
                            
                            <div class="flex items-center gap-1.5 text-red-400 font-bold mt-2.5">
                                <i class="fa-solid fa-arrow-right-to-bracket text-red-500 text-[10px]"></i>
                                Mitigation Action:
                            </div>
                            <p class="text-red-400 mt-1 pl-3 font-medium border-l border-red-950">${issue.recommendation}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            issuesHtml = `
                <div class="mt-3 text-[12px] text-zinc-550 font-sans italic">
                    Clause complies with standard regulatory legal guidelines. No risk flags generated.
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="flex items-start justify-between gap-4">
                <div class="space-y-1">
                    <span class="text-[9px] font-bold text-zinc-550 font-mono tracking-widest uppercase">Clause Category</span>
                    <h4 class="font-extrabold text-sm text-zinc-150 flex items-center gap-2">
                        ${clause.category}
                    </h4>
                </div>
                <span class="text-[9px] uppercase font-bold tracking-widest px-2.5 py-0.5 border rounded-full flex items-center gap-1.5 ${badgeClass}">
                    <i class="fa-solid ${iconClass.split(' ')[0]}"></i> ${clause.risk_level}
                </span>
            </div>
            
            <!-- Excerpt content box -->
            <div class="mt-3">
                <span class="text-[9px] font-bold text-zinc-600 font-mono uppercase tracking-widest">Document Excerpt</span>
                <p class="text-[13px] text-zinc-350 mt-1 leading-relaxed font-mono bg-black/40 p-3 rounded-lg border border-zinc-900/80">${escapeHtml(clause.text)}</p>
            </div>
            
            ${issuesHtml}
        `;
        
        // Add card click listener
        card.addEventListener("click", () => {
            selectClause(originalIdx, false); // Select and scroll text viewer
        });
        
        clauseList.appendChild(card);
    });
}

// Selects a clause and synchronizes highlighting & scrolling between viewer and drawer list
function selectClause(index, scrollDrawer = false) {
    activeIndex = index;
    
    // 1. Remove highlight active classes from viewer
    document.querySelectorAll(".clause-highlight").forEach(el => {
        el.classList.remove("hl-active");
    });
    
    // Add active class to corresponding span in document viewer
    const activeSpan = document.getElementById(`hl-span-${index}`);
    if (activeSpan) {
        activeSpan.classList.add("hl-active");
        
        // Scroll document viewer to highlighted text if triggered from drawer card
        if (!scrollDrawer) {
            activeSpan.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }
    
    // 2. Remove active ring style from drawer cards
    document.querySelectorAll("#clause-list > div").forEach(card => {
        card.className = card.className.replace(/\bring-2 ring-red-500 shadow-xl shadow-red-950\/20\b/g, "").trim();
    });
    
    // Make sure drawer is open
    if (scrollDrawer && !drawerOpen) {
        toggleDrawer(true);
    }
    
    // Add active ring styling to the selected card
    setTimeout(() => {
        const activeCard = document.getElementById(`audit-card-${index}`);
        if (activeCard) {
            activeCard.className += " ring-2 ring-red-500 shadow-xl shadow-red-950/20";
            
            // Scroll the drawer list to the card if triggered from document viewer
            if (scrollDrawer) {
                activeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        }
    }, drawerOpen ? 0 : 500); // Wait for drawer open animation if it was closed
}

// Export Audit Result to JSON File
function exportJSON() {
    if (!contractText || clauses.length === 0) return;
    
    const exportData = {
        audit_date: new Date().toISOString(),
        document_title: docTitle.textContent,
        document_size: docSize.textContent,
        document_classification: metricClass.textContent,
        compliance_score: metricScore.textContent,
        high_risk_flags: metricHigh.textContent,
        total_clauses_audited: metricClauses.textContent,
        clauses: clauses
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 4)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    
    link.href = url;
    link.download = `lexaudit_report_${docTitle.textContent.replace(/\.[^/.]+$/, "")}.json`;
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Display error fallback
function showError(message) {
    alert(message);
}
