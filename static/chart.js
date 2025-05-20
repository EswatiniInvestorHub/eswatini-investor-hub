function createLineChart(priceHistoryData) {
    const ctx = document.getElementById("share-price-chart").getContext("2d");

    // Format data for the chart
    const labels = priceHistoryData.map(item => item.date);
    const prices = priceHistoryData.map(item => item.price);

    // Destroy existing chart instance if any
    if (window.sharePriceChart) {
        window.sharePriceChart.destroy();
    }

    // Create a new line chart
    window.chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
            label: 'Share Price',
            data: prices,
            borderColor: 'blue',
            backgroundColor: 'rgba(0, 0, 255, 0.2)',
            fill: true,
            tension: 0.5  // More curved line
        }]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Date'
                },
                ticks: {
                    autoSkip: true,
                    maxTicksLimit: 7,
                    maxRotation: 45,
                    minRotation: 30
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Price (E)'
                }
            }
        }
    }
});

}
