let currentIndex = 0;
const slides = document.querySelectorAll('.news-slide');
const totalSlides = slides.length;

// Function to show the current slide
function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.style.display = i === index ? 'block' : 'none';
    });
}

// Function to go to the next slide
function nextSlide() {
    currentIndex = (currentIndex + 1) % totalSlides;
    showSlide(currentIndex);
}

// Function to go to the previous slide
function prevSlide() {
    currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
    showSlide(currentIndex);
}

// Event listeners for navigation buttons
document.querySelector('.slider-nav.next').addEventListener('click', nextSlide);
document.querySelector('.slider-nav.prev').addEventListener('click', prevSlide);

// Show the initial slide
showSlide(currentIndex);

// Automatic slide every 3 seconds
setInterval(nextSlide, 3000);



// Example company data object
const companyData = {
    'company1': {
        name: 'Nedbank',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company2': {
        name: 'SWAPROP',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	'company3': {
        name: 'SBC',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	'company4': {
        name: 'RES',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company5': {
        name: 'NPC',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company6': {
        name: 'INALA Capital',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company7': {
        name: 'GREYSTONE',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company8': {
        name: 'FNB',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
	
	'company9': {
        name: 'SEL',
        description: 'A brief description about Company A.',
        sector: 'Finance',
        sharePriceHistory: [10, 12, 11, 14, 13], // Sample price data
        annualReports: [
            { year: 2023, link: 'report2023.pdf' },
            { year: 2022, link: 'report2022.pdf' }
        ]
    },
    
};

// Show the company details in the modal
function showCompanyDetails(companyId) {
    const company = companyData[companyId];

    // Set company info
    document.getElementById('company-info').innerHTML = `
        <h2>${company.name}</h2>
        <p>${company.description}</p>
        <p>Sector: ${company.sector}</p>
    `;

    // Set the chart (using Chart.js)
    const ctx = document.getElementById('share-price-chart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            datasets: [{
                label: 'Share Price',
                data: company.sharePriceHistory,
                borderColor: '#002266',
                backgroundColor: 'rgba(0, 34, 102, 0.2)'
            }]
        }
    });

    // Set price history table
    document.getElementById('price-history').innerHTML = `
        <h3>Share Price History</h3>
        <table>
            <tr><th>Date</th><th>Price (USD)</th></tr>
            <tr><td>Jan</td><td>$${company.sharePriceHistory[0]}</td></tr>
            <tr><td>Feb</td><td>$${company.sharePriceHistory[1]}</td></tr>
            <tr><td>Mar</td><td>$${company.sharePriceHistory[2]}</td></tr>
            <!-- Add more rows dynamically -->
        </table>
    `;

    // Set the annual reports download links
    document.getElementById('annual-reports').innerHTML = `
        <h3>Annual Reports</h3>
        ${company.annualReports.map(report => 
            `<a href="${report.link}" download>Download ${report.year} Report</a>`
        ).join('<br/>')}
    `;

    // Show the modal
    document.getElementById('company-details-modal').style.display = 'flex';
}

// Close the modal
function closeCompanyDetails() {
    document.getElementById('company-details-modal').style.display = 'none';
}
