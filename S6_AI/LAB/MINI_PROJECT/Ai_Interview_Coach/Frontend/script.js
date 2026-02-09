// =================================
// GLOBAL VARIABLES & STATE
// =================================
const state = {
    currentPage: 'overview',
    currentQuestion: 1,
    totalQuestions: 5,
    timer: 0,
    timerInterval: null,
    userAnswers: [],
    currentInterview: null,
    scores: [],
};

// =================================
// INITIALIZATION
// =================================
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initMobileMenu();
    initPricingToggle();
    initVideoModal();
    initDashboard();
    initUserMenu();
    checkAuth();
    loadUserData();
});

// =================================
// AUTHENTICATION
// =================================
function checkAuth() {
    const authToken = localStorage.getItem('authToken');
    const currentPath = window.location.pathname;
    
    // Redirect to login if accessing dashboard without auth
    if (currentPath.includes('dashboard.html') && !authToken) {
        window.location.href = 'login.html';
    }
    
    // Redirect to dashboard if already logged in and on login/signup page
    if ((currentPath.includes('login.html') || currentPath.includes('signup.html')) && authToken) {
        const rememberMe = localStorage.getItem('rememberMe');
        if (rememberMe === 'true') {
            window.location.href = 'dashboard.html';
        }
    }
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('rememberMe');
    window.location.href = 'index.html';
}

function loadUserData() {
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const userEmail = localStorage.getItem('userEmail');
    
    // Update user display
    const userNameElements = document.querySelectorAll('.user-name');
    const userAvatarElements = document.querySelectorAll('.user-avatar');
    
    if (userData.firstName && userData.lastName) {
        const fullName = `${userData.firstName} ${userData.lastName}`;
        const initials = `${userData.firstName[0]}${userData.lastName[0]}`;
        
        userNameElements.forEach(el => el.textContent = fullName);
        userAvatarElements.forEach(el => el.textContent = initials);
    } else if (userEmail) {
        const name = userEmail.split('@')[0];
        userNameElements.forEach(el => el.textContent = name);
        userAvatarElements.forEach(el => el.textContent = name.substring(0, 2).toUpperCase());
    }
}

// =================================
// NAVIGATION
// =================================
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Smooth scroll to section
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetSection = document.querySelector(targetId);
                if (targetSection) {
                    targetSection.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
}

function initMobileMenu() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
}

// =================================
// DASHBOARD NAVIGATION
// =================================
function initDashboard() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    // Sidebar Navigation
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const pageName = this.getAttribute('data-page');
            
            // Update active nav item
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding page
            pages.forEach(page => page.classList.remove('active'));
            const targetPage = document.getElementById(pageName + 'Page');
            if (targetPage) {
                targetPage.classList.add('active');
                state.currentPage = pageName;
            }
        });
    });
    
    // Mobile Sidebar Toggle
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
}

function initUserMenu() {
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function() {
            userDropdown.classList.remove('show');
        });
    }
}

// =================================
// PRICING TOGGLE
// =================================
function initPricingToggle() {
    const pricingToggle = document.getElementById('pricingToggle');
    const monthlyPrices = document.querySelectorAll('.monthly-price');
    const annualPrices = document.querySelectorAll('.annual-price');
    
    if (pricingToggle) {
        pricingToggle.addEventListener('change', function() {
            if (this.checked) {
                // Show annual pricing
                monthlyPrices.forEach(el => el.style.display = 'none');
                annualPrices.forEach(el => el.style.display = 'inline');
            } else {
                // Show monthly pricing
                monthlyPrices.forEach(el => el.style.display = 'inline');
                annualPrices.forEach(el => el.style.display = 'none');
            }
        });
    }
}

// =================================
// VIDEO MODAL
// =================================
function initVideoModal() {
    const modal = document.getElementById('videoModal');
    
    if (modal) {
        window.onclick = function(event) {
            if (event.target === modal) {
                closeVideo();
            }
        };
    }
}

function playVideo() {
    const modal = document.getElementById('videoModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeVideo() {
    const modal = document.getElementById('videoModal');
    if (modal) {
        modal.style.display = 'none';
        // Stop video playback
        const iframe = modal.querySelector('iframe');
        if (iframe) {
            const iframeSrc = iframe.src;
            iframe.src = iframeSrc;
        }
    }
}

// =================================
// INTERVIEW FUNCTIONALITY
// =================================

// Quick Start Interview
function quickStartInterview(type) {
    // Navigate to practice page
    const navItems = document.querySelectorAll('.nav-item');
    const practiceNav = Array.from(navItems).find(item => item.getAttribute('data-page') === 'practice');
    
    if (practiceNav) {
        practiceNav.click();
    }
    
    // Pre-select interview type
    setTimeout(() => {
        const typeButtons = document.querySelectorAll('.option-btn');
        typeButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-type') === type) {
                btn.classList.add('active');
            }
        });
    }, 100);
}

// Start New Interview
function startNewInterview() {
    quickStartInterview('technical');
}

// Start Interview
async function startInterview() {
    const field = document.getElementById('field')?.value;
    const level = document.getElementById('level')?.value;
    const selectedType = document.querySelector('.option-btn.active')?.getAttribute('data-type');
    const selectedMode = document.querySelector('input[name="mode"]:checked')?.value;
    
    // Validation
    if (!field || !level) {
        showToast('Please select field and experience level', 'error');
        return;
    }
    
    // Show loading
    const startBtn = document.getElementById('startBtn');
    const originalText = startBtn.innerHTML;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    startBtn.disabled = true;
    
    try {
        // Simulate API call to get question
        const question = await fetchQuestion(field, level, selectedType);
        
        // Hide setup, show interview screen
        document.querySelector('.setup-card').style.display = 'none';
        document.getElementById('interviewScreen').style.display = 'block';
        
        // Display question
        displayQuestion(question);
        
        // Start timer
        startTimer();
        
        // Store interview data
        state.currentInterview = {
            field,
            level,
            type: selectedType,
            mode: selectedMode,
            startTime: Date.now(),
        };
        
    } catch (error) {
        showToast('Failed to start interview. Please try again.', 'error');
        startBtn.innerHTML = originalText;
        startBtn.disabled = false;
    }
}

// Fetch Question (Simulated)
async function fetchQuestion(field, level, type) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Sample questions database
    const questions = {
        technical: [
            {
                text: "Explain the difference between let, const, and var in JavaScript. When would you use each?",
                difficulty: "medium",
                category: "Technical"
            },
            {
                text: "What is closure in JavaScript? Provide a practical example of when you would use closures.",
                difficulty: "medium",
                category: "Technical"
            },
            {
                text: "Describe the event loop in JavaScript and how it handles asynchronous operations.",
                difficulty: "hard",
                category: "Technical"
            },
        ],
        behavioral: [
            {
                text: "Tell me about a time when you had to work with a difficult team member. How did you handle the situation?",
                difficulty: "medium",
                category: "Behavioral"
            },
            {
                text: "Describe a project where you had to learn a new technology quickly. What was your approach?",
                difficulty: "medium",
                category: "Behavioral"
            },
        ],
        'system-design': [
            {
                text: "Design a URL shortening service like bit.ly. Consider scalability, high availability, and data persistence.",
                difficulty: "hard",
                category: "System Design"
            },
        ],
        hr: [
            {
                text: "Why do you want to work for our company? What do you know about us?",
                difficulty: "easy",
                category: "HR"
            },
            {
                text: "Where do you see yourself in 5 years?",
                difficulty: "easy",
                category: "HR"
            },
        ],
    };
    
    const typeQuestions = questions[type] || questions.technical;
    const randomQuestion = typeQuestions[Math.floor(Math.random() * typeQuestions.length)];
    
    return randomQuestion;
}

// Display Question
function displayQuestion(question) {
    const questionText = document.getElementById('questionText');
    const currentQuestionEl = document.getElementById('currentQuestion');
    const totalQuestionsEl = document.getElementById('totalQuestions');
    
    if (questionText) {
        questionText.textContent = question.text;
    }
    
    if (currentQuestionEl) {
        currentQuestionEl.textContent = state.currentQuestion;
    }
    
    if (totalQuestionsEl) {
        totalQuestionsEl.textContent = state.totalQuestions;
    }
    
    // Update difficulty badge
    const difficultyBadge = document.querySelector('.difficulty-badge');
    if (difficultyBadge) {
        difficultyBadge.className = `difficulty-badge ${question.difficulty}`;
        difficultyBadge.textContent = question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1);
    }
    
    // Update category badge
    const categoryBadge = document.querySelector('.category-badge');
    if (categoryBadge) {
        categoryBadge.textContent = question.category;
    }
}

// Start Timer
function startTimer() {
    state.timer = 0;
    const timerElement = document.getElementById('timer');
    
    state.timerInterval = setInterval(() => {
        state.timer++;
        const minutes = Math.floor(state.timer / 60);
        const seconds = state.timer % 60;
        
        if (timerElement) {
            timerElement.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

// Stop Timer
function stopTimer() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
}

// Submit Answer
async function submitAnswer() {
    const answerBox = document.getElementById('answerBox');
    const answer = answerBox?.value.trim();
    
    if (!answer) {
        showToast('Please provide an answer before submitting', 'error');
        return;
    }
    
    // Show loading
    const submitBtn = document.getElementById('submitAnswer');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    submitBtn.disabled = true;
    
    try {
        // Simulate AI analysis
        const feedback = await analyzeAnswer(answer);
        
        // Store answer
        state.userAnswers.push({
            question: state.currentQuestion,
            answer: answer,
            feedback: feedback,
            timeSpent: state.timer,
        });
        
        // Show feedback
        displayFeedback(feedback);
        
        // Hide answer section
        document.querySelector('.answer-section').style.display = 'none';
        
    } catch (error) {
        showToast('Failed to analyze answer. Please try again.', 'error');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Analyze Answer (Simulated AI)
async function analyzeAnswer(answer) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Generate simulated feedback
    const score = Math.floor(Math.random() * 3) + 7; // Random score between 7-10
    
    return {
        score: score,
        strengths: [
            "Clear and structured response",
            "Good use of technical terminology",
            "Relevant examples provided",
        ],
        improvements: [
            "Could provide more specific examples",
            "Consider discussing edge cases",
            "Elaborate on implementation details",
        ],
        detailedFeedback: "Your answer demonstrates a solid understanding of the concept. You've structured your response well and used appropriate terminology. To improve, consider providing more real-world examples and discussing potential edge cases or challenges in implementation.",
    };
}

// Display Feedback
function displayFeedback(feedback) {
    const feedbackSection = document.getElementById('feedbackSection');
    const feedbackContent = document.getElementById('feedbackContent');
    
    if (feedbackSection && feedbackContent) {
        feedbackContent.innerHTML = `
            <div class="feedback-strengths">
                <h4><i class="fas fa-check-circle" style="color: var(--success);"></i> Strengths</h4>
                <ul>
                    ${feedback.strengths.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
            
            <div class="feedback-improvements" style="margin-top: 1.5rem;">
                <h4><i class="fas fa-lightbulb" style="color: var(--warning);"></i> Areas for Improvement</h4>
                <ul>
                    ${feedback.improvements.map(i => `<li>${i}</li>`).join('')}
                </ul>
            </div>
            
            <div class="feedback-detailed" style="margin-top: 1.5rem;">
                <h4><i class="fas fa-comment-dots" style="color: var(--primary);"></i> Detailed Feedback</h4>
                <p style="color: var(--text-secondary); line-height: 1.8;">${feedback.detailedFeedback}</p>
            </div>
        `;
        
        // Update score badge
        const scoreBadge = feedbackSection.querySelector('.score-badge');
        if (scoreBadge) {
            scoreBadge.textContent = `${feedback.score}/10`;
        }
        
        feedbackSection.style.display = 'block';
    }
}

// Next Question
function nextQuestion() {
    state.currentQuestion++;
    
    if (state.currentQuestion > state.totalQuestions) {
        // Interview complete
        completeInterview();
    } else {
        // Load next question
        resetQuestionScreen();
        startInterview();
    }
}

// Skip Question
function skipQuestion() {
    if (confirm('Are you sure you want to skip this question?')) {
        nextQuestion();
    }
}

// End Interview
function endInterview() {
    if (confirm('Are you sure you want to end the interview? Your progress will be saved.')) {
        completeInterview();
    }
}

// Complete Interview
function completeInterview() {
    stopTimer();
    
    // Calculate overall score
    const totalScore = state.userAnswers.reduce((sum, ans) => sum + ans.feedback.score, 0);
    const avgScore = (totalScore / state.userAnswers.length).toFixed(1);
    
    // Store in scores history
    state.scores.push({
        date: new Date().toISOString(),
        score: avgScore,
        type: state.currentInterview.type,
        field: state.currentInterview.field,
        questionsAnswered: state.userAnswers.length,
    });
    
    // Save to localStorage
    const savedScores = JSON.parse(localStorage.getItem('interviewScores') || '[]');
    savedScores.push(state.scores[state.scores.length - 1]);
    localStorage.setItem('interviewScores', JSON.stringify(savedScores));
    
    // Show results modal
    showResultsModal(avgScore);
    
    // Reset interview state
    resetInterview();
}

// Show Results Modal
function showResultsModal(score) {
    const modal = document.getElementById('resultsModal');
    
    if (modal) {
        // Update score
        const scoreText = modal.querySelector('.score-text');
        if (scoreText) {
            scoreText.innerHTML = `${score}<span>/10</span>`;
        }
        
        // Update progress circle
        const scoreProgress = modal.querySelector('.score-progress');
        if (scoreProgress) {
            const circumference = 283;
            const offset = circumference - (score / 10) * circumference;
            scoreProgress.style.strokeDashoffset = offset;
        }
        
        // Show modal
        modal.classList.add('show');
    }
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('resultsModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Reset Interview
function resetInterview() {
    state.currentQuestion = 1;
    state.timer = 0;
    state.userAnswers = [];
    state.currentInterview = null;
    
    // Reset UI
    document.querySelector('.setup-card').style.display = 'block';
    document.getElementById('interviewScreen').style.display = 'none';
}

// Reset Question Screen
function resetQuestionScreen() {
    const answerBox = document.getElementById('answerBox');
    if (answerBox) {
        answerBox.value = '';
    }
    
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection) {
        feedbackSection.style.display = 'none';
    }
    
    const answerSection = document.querySelector('.answer-section');
    if (answerSection) {
        answerSection.style.display = 'block';
    }
    
    const submitBtn = document.getElementById('submitAnswer');
    if (submitBtn) {
        submitBtn.innerHTML = 'Submit Answer <i class="fas fa-arrow-right"></i>';
        submitBtn.disabled = false;
    }
}

// Show Hint
function showHint() {
    const hints = [
        "Start by breaking down the question into smaller parts",
        "Consider using the STAR method: Situation, Task, Action, Result",
        "Think about a specific example from your experience",
        "Focus on your role and contributions",
        "Be specific with numbers and metrics where possible",
    ];
    
    const randomHint = hints[Math.floor(Math.random() * hints.length)];
    showToast(randomHint, 'info');
}

// =================================
// TOAST NOTIFICATIONS
// =================================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.className = `toast show ${type}`;
        
        // Update icon based on type
        const icon = toast.querySelector('i');
        if (icon) {
            icon.className = type === 'success' ? 'fas fa-check-circle' :
                           type === 'error' ? 'fas fa-exclamation-circle' :
                           'fas fa-info-circle';
        }
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// =================================
// BUTTON GROUP FUNCTIONALITY
// =================================
document.addEventListener('click', function(e) {
    // Interview type selection
    if (e.target.closest('.option-btn')) {
        const btn = e.target.closest('.option-btn');
        const parent = btn.parentElement;
        
        parent.querySelectorAll('.option-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
});

// =================================
// CHARTS (Simple Placeholder)
// =================================
function initCharts() {
    // Performance Chart
    const performanceChart = document.getElementById('performanceChart');
    if (performanceChart) {
        // In a real app, you would use Chart.js or similar library
        performanceChart.style.height = '300px';
        performanceChart.style.background = 'linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(139, 92, 246, 0.1))';
        performanceChart.style.borderRadius = '1rem';
        performanceChart.style.display = 'flex';
        performanceChart.style.alignItems = 'center';
        performanceChart.style.justifyContent = 'center';
        
        const ctx = performanceChart.getContext('2d');
        ctx.font = '16px Inter';
        ctx.fillStyle = '#64748b';
        ctx.textAlign = 'center';
        ctx.fillText('Chart will be rendered here', performanceChart.width / 2, performanceChart.height / 2);
    }
}

// =================================
// SETTINGS FUNCTIONALITY
// =================================
document.querySelectorAll('.settings-form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        showToast('Settings saved successfully!', 'success');
    });
});

// =================================
// SMOOTH SCROLLING
// =================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href.length > 1) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// =================================
// FORM VALIDATION HELPERS
// =================================
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

// =================================
// LOCAL STORAGE HELPERS
// =================================
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function getFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
    }
}

// =================================
// PERFORMANCE OPTIMIZATION
// =================================
// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search functionality with debounce
const searchInput = document.querySelector('.search-bar input');
if (searchInput) {
    searchInput.addEventListener('input', debounce(function(e) {
        const query = e.target.value.toLowerCase();
        // Implement search logic here
        console.log('Searching for:', query);
    }, 300));
}

// =================================
// INTERSECTION OBSERVER FOR ANIMATIONS
// =================================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .pricing-card, .testimonial-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// =================================
// PREVENT FORM SUBMISSION ON ENTER
// =================================
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && this.type !== 'submit') {
            e.preventDefault();
        }
    });
});

// =================================
// COPY TO CLIPBOARD
// =================================
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'error');
    });
}

// =================================
// KEYBOARD SHORTCUTS
// =================================
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-bar input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        closeModal();
        closeVideo();
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }
});

// =================================
// ERROR HANDLING
// =================================
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // In production, you might want to send this to an error tracking service
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    // In production, you might want to send this to an error tracking service
});

// =================================
// EXPORT FUNCTIONS FOR INLINE USE
// =================================
window.showSetup = function() {
    document.getElementById("home").style.display = "none";
    document.getElementById("setupSection").style.display = "flex";
};

window.playVideo = playVideo;
window.closeVideo = closeVideo;
window.logout = logout;
window.startNewInterview = startNewInterview;
window.quickStartInterview = quickStartInterview;
window.startInterview = startInterview;
window.submitAnswer = submitAnswer;
window.nextQuestion = nextQuestion;
window.skipQuestion = skipQuestion;
window.endInterview = endInterview;
window.closeModal = closeModal;
window.showHint = showHint;

console.log('✅ AI Interview Coach initialized successfully');
