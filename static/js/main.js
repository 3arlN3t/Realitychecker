// Main JavaScript for Reality Checker web interface

let selectedFile = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize unified form handler
    initializeUnifiedForm();
    initializeNewAnalysisButton();
});

function initializeUnifiedForm() {
    const unifiedForm = document.getElementById('unifiedForm');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const hiddenFileInput = document.getElementById('hiddenFileInput');
    const jobInput = document.getElementById('jobInput');
    const removeFileBtn = document.getElementById('removeFile');
    
    if (unifiedForm) {
        // Handle form submission
        unifiedForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const jobText = jobInput.value.trim();
            
            if (selectedFile) {
                // Analyze PDF file
                await analyzePDF(selectedFile);
            } else if (jobText) {
                // Analyze text
                if (jobText.length < 20) {
                    showAlert('Job advertisement text is too short. Please provide more details.', 'warning');
                    return;
                }
                await analyzeText(jobText);
            } else {
                showAlert('Please enter job advertisement text or upload a PDF file', 'warning');
            }
        });
        
        // Handle file upload button click
        fileUploadBtn.addEventListener('click', function() {
            hiddenFileInput.click();
        });
        
        // Handle file selection
        hiddenFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.type !== 'application/pdf') {
                    showAlert('Please select a valid PDF file', 'warning');
                    hiddenFileInput.value = '';
                    return;
                }
                
                if (file.size > 10 * 1024 * 1024) { // 10MB limit
                    showAlert('File size must be less than 10MB', 'warning');
                    hiddenFileInput.value = '';
                    return;
                }
                
                selectedFile = file;
                showFileInfo(file.name);
                jobInput.value = ''; // Clear text input when file is selected
                toggleSubmitButton();
            }
        });
        
        // Handle file removal
        removeFileBtn.addEventListener('click', function() {
            selectedFile = null;
            hiddenFileInput.value = '';
            hideFileInfo();
            toggleSubmitButton();
        });
    }
}

function showFileInfo(fileName) {
    document.getElementById('fileName').textContent = `Selected: ${fileName}`;
    document.getElementById('fileInfo').style.display = 'block';
}

function hideFileInfo() {
    document.getElementById('fileInfo').style.display = 'none';
}

function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function toggleSubmitButton() {
    const submitBtn = document.getElementById('submitBtn');
    const jobInput = document.getElementById('jobInput');
    
    if (selectedFile || jobInput.value.trim()) {
        submitBtn.disabled = false;
    } else {
        submitBtn.disabled = true;
    }
}

function initializeNewAnalysisButton() {
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', function() {
            // Reset unified form
            document.getElementById('unifiedForm').reset();
            document.getElementById('jobInput').value = '';
            selectedFile = null;
            hideFileInfo();
            toggleSubmitButton();
            
            // Reset textarea height
            const jobInput = document.getElementById('jobInput');
            jobInput.style.height = 'auto';
            
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
    
    // Disable buttons and input
    const submitBtn = document.getElementById('submitBtn');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const jobInput = document.getElementById('jobInput');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Analyzing...';
    }
    
    if (fileUploadBtn) {
        fileUploadBtn.disabled = true;
    }
    
    if (jobInput) {
        jobInput.disabled = true;
    }
}

function hideLoading() {
    document.getElementById('loadingIndicator').style.display = 'none';
    
    // Re-enable buttons and input
    const submitBtn = document.getElementById('submitBtn');
    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const jobInput = document.getElementById('jobInput');
    
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Analyze';
        toggleSubmitButton(); // Re-check if button should be enabled
    }
    
    if (fileUploadBtn) {
        fileUploadBtn.disabled = false;
    }
    
    if (jobInput) {
        jobInput.disabled = false;
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