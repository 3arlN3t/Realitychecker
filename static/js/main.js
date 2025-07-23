// Main JavaScript for Reality Checker web interface

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    initializeTextForm();
    initializePDFForm();
    initializeNewAnalysisButton();
});

function initializeTextForm() {
    const textForm = document.getElementById('textForm');
    if (textForm) {
        textForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const jobText = document.getElementById('jobText').value;
            
            if (!jobText.trim()) {
                showAlert('Please enter job advertisement text', 'warning');
                return;
            }
            
            if (jobText.trim().length < 20) {
                showAlert('Job advertisement text is too short. Please provide more details.', 'warning');
                return;
            }
            
            await analyzeText(jobText);
        });
    }
}

function initializePDFForm() {
    const pdfForm = document.getElementById('pdfForm');
    if (pdfForm) {
        pdfForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const pdfFile = document.getElementById('pdfFile').files[0];
            
            if (!pdfFile) {
                showAlert('Please select a PDF file', 'warning');
                return;
            }
            
            if (pdfFile.type !== 'application/pdf') {
                showAlert('Please select a valid PDF file', 'warning');
                return;
            }
            
            if (pdfFile.size > 10 * 1024 * 1024) { // 10MB limit
                showAlert('File size must be less than 10MB', 'warning');
                return;
            }
            
            await analyzePDF(pdfFile);
        });
    }
}

function initializeNewAnalysisButton() {
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', function() {
            // Reset forms
            document.getElementById('textForm').reset();
            document.getElementById('pdfForm').reset();
            
            // Hide results
            document.getElementById('resultCard').style.display = 'none';
            
            // Show the input card
            document.querySelector('.card').style.display = 'block';
        });
    }
}

async function analyzeText(jobText) {
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('job_text', jobText);
        
        const response = await fetch('/web/analyze/text', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            displayResults(result);
        } else {
            throw new Error(result.message || 'Analysis failed');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

async function analyzePDF(pdfFile) {
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('pdf_file', pdfFile);
        
        const response = await fetch('/web/analyze/pdf', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            displayResults(result);
        } else {
            throw new Error(result.message || 'Analysis failed');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

function displayResults(response) {
    const result = response.result;
    
    // Update trust score
    const trustScoreElement = document.getElementById('trustScore');
    const scoreCircle = document.getElementById('scoreCircle');
    
    trustScoreElement.textContent = result.trust_score;
    
    // Set score color
    scoreCircle.className = 'score-circle';
    if (result.trust_score >= 70) {
        scoreCircle.classList.add('score-high');
    } else if (result.trust_score >= 40) {
        scoreCircle.classList.add('score-medium');
    } else {
        scoreCircle.classList.add('score-low');
    }
    
    // Update classification
    document.getElementById('classification').textContent = result.classification;
    
    // Update reasoning
    const reasoningElement = document.getElementById('reasoning');
    let reasoningHtml = '<h6>Analysis Details:</h6><ul class="list-unstyled">';
    
    result.reasoning.forEach(reason => {
        reasoningHtml += `<li class="mb-2"><i class="fas fa-check-circle text-primary me-2"></i>${reason}</li>`;
    });
    
    reasoningHtml += '</ul>';
    reasoningElement.innerHTML = reasoningHtml;
    
    // Show results and hide input form
    document.querySelector('.card').style.display = 'none';
    document.getElementById('resultCard').style.display = 'block';
    
    // Scroll to results
    document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth' });
}

function showLoading() {
    document.getElementById('loadingIndicator').style.display = 'block';
    
    // Disable form buttons
    const buttons = document.querySelectorAll('button[type="submit"]');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Analyzing...';
    });
}

function hideLoading() {
    document.getElementById('loadingIndicator').style.display = 'none';
    
    // Re-enable form buttons
    const textBtn = document.querySelector('#textForm button[type="submit"]');
    const pdfBtn = document.querySelector('#pdfForm button[type="submit"]');
    
    if (textBtn) {
        textBtn.disabled = false;
        textBtn.innerHTML = 'Analyze Text';
    }
    
    if (pdfBtn) {
        pdfBtn.disabled = false;
        pdfBtn.innerHTML = 'Analyze PDF';
    }
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}