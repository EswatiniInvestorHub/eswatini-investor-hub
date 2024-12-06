let chartInstance = null;

function showCompanyDetails(companyId) {
    const company = companyData[companyId];

    // Set company info
    document.getElementById('company-info').innerHTML = `
        <h2>${company.name}</h2>
        <p>${company.description}</p>
        <p>Sector: ${company.sector}</p>
    `;

    // Destroy the previous chart instance if it exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    // Set the chart (using Chart.js)
    const ctx = document.getElementById('share-price-chart').getContext('2d');
    chartInstance = new Chart(ctx, {
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

function closeCompanyDetails() {
    document.getElementById('company-details-modal').style.display = 'none';
}
