/**
 * Main JavaScript for Reality Checker web interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle form submissions
    const textForm = document.getElementById('textForm');
    const pdfForm = document.getElementById('pdfForm');
    
    if (textForm) {
        textForm.addEventListener('submit', handleTextFormSubmit);
    }
    
    if (pdfForm) {
        pdfForm.addEventListener('submit', handlePdfFormSubmit);
    }
    
    // Handle new analysis button
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', resetForms);
    }
});

/**
 * Handle text form submission
 * @param {Event} e - Form submit event
 */
async function handleTextFormSubmit(e) {
    e.preventDefault();
    const jobText = document.getElementById('jobText').value;
    if (!jobText.trim()) {
        alert('Please enter job advertisement text');
        return;
    }
    
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
            displayResults(result.result);
        } else {
            throw new Error(result.message || 'Analysis failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

/**
 * Handle PDF form submission
 * @param {Event} e - Form submit event
 */
async function handlePdfFormSubmit(e) {
    e.preventDefault();
    const pdfFile = document.getElementById('pdfFile').files[0];
    if (!pdfFile) {
        alert('Please select a PDF file');
        return;
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (pdfFile.size > maxSize) {
        alert('File is too large. Maximum size is 10MB.');
        return;
    }
    
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
            displayResults(result.result);
        } else {
            throw new Error(result.message || 'Analysis failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
        hideLoading();
    }
}

/**
 * Display analysis results
 * @param {Object} result - Analysis result object
 */
function displayResults(result) {
    hideLoading();
    
    const trustScore = document.getElementById('trustScore');
    const scoreCircle = document.getElementById('scoreCircle');
    const classification = document.getElementById('classification');
    const reasoning = document.getElementById('reasoning');
    const resultCard = document.getElementById('resultCard');
    
    // Set trust score
    trustScore.textContent = result.trust_score;
    
    // Set score circle color based on trust score
    scoreCircle.className = 'score-circle';
    if (result.trust_score >= 70) {
        scoreCircle.classList.add('score-high');
    } else if (result.trust_score >= 40) {
        scoreCircle.classList.add('score-medium');
    } else {
        scoreCircle.classList.add('score-low');
    }
    
    // Set classification
    classification.textContent = result.classification;
    
    // Set reasoning
    let reasoningHtml = '<ul>';
    result.reasoning.forEach(reason => {
        reasoningHtml += `<li>${reason}</li>`;
    });
    reasoningHtml += '</ul>';
    reasoning.innerHTML = reasoningHtml;
    
    // Show result card
    resultCard.style.display = 'block';
}

/**
 * Show loading indicator
 */
function showLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultCard = document.getElementById('resultCard');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    if (resultCard) {
        resultCard.style.display = 'none';
    }
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * Reset forms
 */
function resetForms() {
    const textForm = document.getElementById('textForm');
    const pdfForm = document.getElementById('pdfForm');
    const resultCard = document.getElementById('resultCard');
    
    if (textForm) {
        textForm.reset();
    }
    
    if (pdfForm) {
        pdfForm.reset();
    }
    
    if (resultCard) {
        resultCard.style.display = 'none';
    }
}